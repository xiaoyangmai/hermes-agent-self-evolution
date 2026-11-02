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
