import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from evolution.hermes_runtime import HermesRuntime, digest, write_json
from evolution.skills.skill_module import SkillModule
import evolution.hermes_runtime as runtime_module


def test_export_uses_the_optimized_predictor_signature():
    module = SkillModule("initial")
    module.predictor.predict.signature = module.predictor.predict.signature.with_instructions("optimized")
    assert module.skill_text == "optimized"


def test_operation_resumes_without_resubmitting(tmp_path):
    runtime = object.__new__(HermesRuntime)
    calls = []
    def request(path, body=None, **kwargs):
        calls.append((path, body))
        return {"id": "op-1", "status": "succeeded", "result": {"revision": "abc"}}
    runtime.request = request
    receipt = tmp_path / "operation.json"
    write_json(receipt, {"id": "op-1", "status": "queued"})
    assert runtime.operation("/mutate", receipt, "stable") == {"revision": "abc"}
    assert calls == [("/v1/operations/op-1", None)]


def test_cached_trial_is_scoped_to_the_experiment(tmp_path):
    runtime = object.__new__(HermesRuntime)
    runtime.output = tmp_path
    runtime.experiment_id = "experiment-A"
    runtime.failure = None
    runtime.max_runs = 0
    task = json.dumps({"id": "one"})
    identity = digest(("experiment-A\0instructions\0" + task).encode())
    write_json(tmp_path / "trials" / identity / "receipt.json", {"status": "collected", "trace_summary": {"messages": 4}})
    assert json.loads(runtime.execute("instructions", task))["trace"]["messages"] == 4
    runtime.experiment_id = "experiment-B"
    with pytest.raises(RuntimeError, match="budget exhausted"):
        runtime.execute("instructions", task)


def test_finalize_cannot_accept_another_delivery(tmp_path):
    runtime = object.__new__(HermesRuntime)
    runtime.prefix = "/v1/projects/demo"
    runtime.project = SimpleNamespace(PROFILE="frontend")
    runtime.operation = lambda *args: {}
    runtime.request = lambda *args: {"result": {"delivery_id": "other", "source_revision": "abc", "profile": "frontend"}}
    with pytest.raises(RuntimeError, match="does not identify"):
        runtime.collect({"delivery_id": "this", "revision": "abc"}, tmp_path)


def test_windows_newlines_do_not_create_an_empty_commit(tmp_path, monkeypatch):
    runtime = object.__new__(HermesRuntime)
    runtime.frontmatter = "name: test"
    runtime.skill_path = tmp_path / "SKILL.md"
    runtime.skill_path.write_bytes(b"---\r\nname: test\r\n---\r\n\r\nBody\r\n")
    runtime.repo = tmp_path
    runtime.project = SimpleNamespace(PROFILES=())
    calls = []
    def git(repo, *args):
        calls.append(args)
        if args[0] == "push":
            raise RuntimeError("reached push")
        return "abc"
    monkeypatch.setattr(runtime_module, "git", git)
    with pytest.raises(RuntimeError, match="reached push"):
        runtime.deploy("Body")
    assert calls == [("rev-parse", "HEAD"), ("push", "origin", "HEAD")]


def test_production_busy_check_precedes_any_git_or_file_change(tmp_path, monkeypatch):
    runtime = object.__new__(HermesRuntime)
    runtime.frontmatter = 'name: test'
    runtime.skill_path = tmp_path / 'SKILL.md'
    runtime.skill_path.write_text('---\nname: test\n---\n\nBaseline\n')
    runtime.repo, runtime.prefix = tmp_path, '/v1/projects/demo'
    runtime.project = SimpleNamespace(PROFILES=('frontend',))
    runtime.request = lambda path, body=None, **kw: ({'active_agents': 1} if kw.get('gateway') else {'api_server_key': 'test'})
    calls = []
    monkeypatch.setattr(runtime_module, 'git', lambda *args: calls.append(args))
    with pytest.raises(RuntimeError, match='active run'):
        runtime.deploy('Candidate')
    assert not calls and 'Baseline' in runtime.skill_path.read_text()
    assert runtime.production_mutation_started is False


def test_lost_submission_response_reuses_receipt_and_key_without_release(tmp_path):
    runtime = object.__new__(HermesRuntime)
    runtime.output, runtime.experiment_id, runtime.failure = tmp_path, 'exp', None
    runtime.max_runs, runtime.timeout, runtime.key = 2, 60, 'key'
    runtime.project = SimpleNamespace(PROFILE='frontend', trace_summary=lambda rows: {'messages': len(rows)},
                                      verify_trace=lambda summary: None)
    task_input = json.dumps({'id': 'case'}, sort_keys=True)
    identity = digest(('exp\0body\0' + task_input).encode())
    folder = tmp_path / 'trials' / identity
    write_json(folder / 'receipt.json', {'status': 'submitting', 'delivery_id': 'dspy-original',
               'revision': 'sha', 'before': {'files': {}, 'revision': 'sha'}, 'deadline': 9999999999})
    write_json(folder / 'task.json', {'input': 'original task'})
    calls = []
    def request(path, body=None, **kwargs):
        calls.append((path, body, kwargs))
        if path.endswith('/v1/runs'):
            return {'run_id': 'original-run'}
        if '/api/sessions/' in path:
            return {'data': [], 'pagination': {'returned': 0, 'limit': 500}}
        return {'status': 'completed', 'session_id': 'session'}
    runtime.request = request
    runtime.deploy = lambda body: (_ for _ in ()).throw(AssertionError('must not redeploy'))
    runtime.environment = lambda *args: {'files': {}, 'revision': 'sha'}
    runtime.collect = lambda *args: None
    runtime.execute('body', task_input)
    assert calls[0][1] == {'input': 'original task'}
    assert calls[0][2]['key'] == 'dspy-original'
    receipt = json.loads((folder / 'receipt.json').read_text())
    assert receipt['gateway_run_id'] == 'original-run' and receipt['deadline'] == 9999999999


def test_timeout_requests_stop_and_waits_for_terminal_status(tmp_path, monkeypatch):
    runtime = object.__new__(HermesRuntime)
    runtime.output, runtime.experiment_id, runtime.failure = tmp_path, 'exp', None
    runtime.max_runs, runtime.timeout, runtime.key = 2, 60, 'key'
    runtime.project = SimpleNamespace(PROFILE='frontend', trace_summary=lambda rows: {'messages': len(rows)})
    task_input = json.dumps({'id': 'case'}, sort_keys=True)
    identity = digest(('exp\0body\0' + task_input).encode())
    folder = tmp_path / 'trials' / identity
    write_json(folder / 'receipt.json', {'status': 'running', 'delivery_id': 'dspy-original',
               'gateway_run_id': 'original-run', 'deadline': 1})
    calls, statuses = [], iter(['running', 'cancelled'])
    def request(path, body=None, **kwargs):
        calls.append(path)
        if path.endswith('/stop'):
            return {'accepted': True}
        if '/api/sessions/' in path:
            return {'data': [], 'pagination': {'returned': 0, 'limit': 500}}
        return {'status': next(statuses), 'session_id': 'session'}
    runtime.request = request
    monkeypatch.setattr(runtime_module.time, 'time', lambda: 10)
    monkeypatch.setattr(runtime_module.time, 'sleep', lambda seconds: None)
    with pytest.raises(RuntimeError, match='execution failed'):
        runtime.execute('body', task_input)
    receipt = json.loads((folder / 'receipt.json').read_text())
    assert receipt['terminal']['status'] == 'cancelled'
    assert sum(path.endswith('/stop') for path in calls) == 1
