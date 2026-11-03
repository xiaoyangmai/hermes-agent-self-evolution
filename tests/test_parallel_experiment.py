import json
import io
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest

from evolution.experiment_runtime import ParallelExperimentRuntime
from evolution.hermes_runtime import digest, write_json


def test_two_candidate_slots_allow_four_runs_without_switching(tmp_path):
    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.output = tmp_path
    runtime.max_runs = 4
    runtime.experiment_id = 'exp'
    runtime.condition = threading.Condition()
    runtime.active = {'a': 0, 'b': 0}
    runtime.bodies = {'a': None, 'b': None}
    runtime.inflight = set()
    runtime.uncertain = {}
    runtime.failure = None
    barrier = threading.Barrier(4, timeout=15)
    seen = []

    class Slot:
        def __init__(self, name):
            self.name = name

        def execute(self, instructions, task_input):
            identity = digest(('exp\0' + instructions + '\0' + task_input).encode())
            path = tmp_path / 'trials' / identity / 'receipt.json'
            receipt = json.loads(path.read_text())
            seen.append((self.name, instructions, sum(runtime.active.values())))
            barrier.wait()
            receipt.update(status='collected', trace_summary={'slot': self.name})
            write_json(path, receipt)
            return json.dumps({'trial': str(path.parent), 'trace': receipt['trace_summary']})

    runtime.slots = {s: Slot(s) for s in ('a', 'b')}
    tasks = [('alpha', json.dumps({'id': 'a1'})), ('alpha', json.dumps({'id': 'a2'})),
             ('beta', json.dumps({'id': 'b1'})), ('beta', json.dumps({'id': 'b2'}))]
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda pair: runtime.execute(*pair), tasks))
    assert len(results) == 4 and max(row[2] for row in seen) == 4
    assert len({s for s, body, _ in seen if body == 'alpha'}) == 1
    assert len({s for s, body, _ in seen if body == 'beta'}) == 1
    assert {s for s, body, _ in seen if body == 'alpha'} != {s for s, body, _ in seen if body == 'beta'}
    assert json.loads(runtime.execute(*tasks[0]))['trace'] == json.loads(results[0])['trace']
    assert not runtime.has_search_capacity(1, 0)
    assert runtime.has_search_capacity(0, 0)


def test_candidate_commit_is_pushed_only_to_experiment_branch(tmp_path, monkeypatch):
    remote, repo, output = tmp_path / 'remote.git', tmp_path / 'repo', tmp_path / 'out'
    subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
    subprocess.run(['git', 'init', '-b', 'main', str(repo)], check=True, capture_output=True)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    skill = repo / 'profiles/frontend/skills/skill/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('---\nname: skill\n---\n\nBaseline\n')
    git('add', '.')
    git('commit', '-m', 'baseline')
    git('remote', 'add', 'origin', str(remote))
    git('push', '-u', 'origin', 'main')
    baseline = git('rev-parse', 'HEAD')
    monkeypatch.setenv('HERMES_CONTROL_URL', 'https://example.invalid')
    monkeypatch.setenv('HERMES_CONTROL_TOKEN', 'test')
    project = SimpleNamespace(PROJECT='demo', SKILL='profiles/frontend/skills/skill/SKILL.md',
                              POLICY={'max_remote_runs': 4, 'run_timeout_seconds': 30})
    runtime = ParallelExperimentRuntime(repo, project, output)
    runtime.experiment_id = 'exp'
    candidate = runtime.candidate_revision('Improved')
    assert git('rev-parse', 'HEAD') == baseline
    assert git('branch', '--show-current') == 'main'
    assert skill.read_text() == '---\nname: skill\n---\n\nBaseline\n'
    refs = git('ls-remote', 'origin', 'refs/heads/*')
    assert baseline in refs and candidate in refs and 'refs/heads/evolution/exp/' in refs
    assert runtime.candidate_revision('Improved') == candidate


def test_resume_submitted_run_keeps_candidate_and_case(tmp_path):
    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.output = tmp_path
    runtime.project = SimpleNamespace(SKILL='profiles/frontend/skills/skill/SKILL.md')
    runtime.initial_body = 'Baseline'
    candidate = 'Improved'
    identity = digest(candidate.encode())
    skill = tmp_path / 'candidates' / identity / 'checkout' / runtime.project.SKILL
    skill.parent.mkdir(parents=True)
    skill.write_text('---\nname: skill\n---\n\nImproved\n')
    write_json(tmp_path / 'trials/t1/receipt.json', {'status': 'running', 'candidate_sha256': identity,
               'case': {'id': 'first', 'topic': 'sort'}})
    write_json(tmp_path / 'trials/t2/receipt.json', {'status': 'collected'})
    resumed = []
    runtime.execute = lambda body, task: resumed.append((body, json.loads(task)))
    runtime.resume_pending()
    assert resumed == [('Improved', {'id': 'first', 'topic': 'sort'})]


def test_unknown_running_task_retains_capacity_until_terminal_recovery(tmp_path):
    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.output, runtime.max_runs, runtime.experiment_id = tmp_path, 5, 'exp'
    runtime.initial_body = 'alpha'
    runtime.project = SimpleNamespace(SKILL='skill.md')
    runtime.condition = threading.Condition()
    runtime.active, runtime.bodies = {'a': 0, 'b': 0}, {'a': None, 'b': None}
    runtime.inflight, runtime.uncertain, runtime.failure = set(), {}, None
    barrier = threading.Barrier(4, timeout=15)
    calls = []
    class Slot:
        def execute(self, body, task):
            case = json.loads(task)
            identity = digest(('exp\0' + body + '\0' + task).encode())
            path = tmp_path / 'trials' / identity / 'receipt.json'
            receipt = json.loads(path.read_text())
            calls.append(case['id'])
            if receipt['status'] == 'running':
                receipt.update(status='collected', terminal={'status': 'completed'}, trace_summary={})
                write_json(path, receipt)
                return json.dumps({'trial': str(path.parent), 'trace': {}})
            receipt.update(status='running', gateway_run_id=case['id'])
            write_json(path, receipt)
            barrier.wait()
            if case['id'] == 'lost':
                raise ConnectionError('poll response lost')
            receipt.update(status='collected', terminal={'status': 'completed'}, trace_summary={})
            write_json(path, receipt)
            return json.dumps({'trial': str(path.parent), 'trace': {}})
    runtime.slots = {'a': Slot(), 'b': Slot()}
    tasks = [json.dumps({'id': name}, sort_keys=True) for name in ('lost', 'two', 'three', 'four')]
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(runtime.execute, 'alpha', task) for task in tasks]
        for future in futures:
            try:
                future.result()
            except ConnectionError:
                pass
    assert sum(runtime.active.values()) == 1 and len(runtime.uncertain) == 1
    with pytest.raises(RuntimeError, match='infrastructure failure'):
        runtime.execute('alpha', json.dumps({'id': 'fifth'}))
    assert 'fifth' not in calls
    runtime.resume_pending()
    assert sum(runtime.active.values()) == 0 and not runtime.uncertain
    assert calls.count('lost') == 2


def test_production_mismatch_blocks_adoption_without_recording_credentials(tmp_path):
    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.output, runtime.baseline_revision = tmp_path, 'baseline-revision'
    runtime.project = SimpleNamespace(PROFILE='frontend', SKILL='profiles/frontend/skills/test/SKILL.md')
    runtime.frontmatter, runtime.initial_body = 'name: test', 'Baseline'
    skill_hash = digest(b'---\nname: test\n---\n\nBaseline\n')
    state = {'revision': 'baseline-revision', 'files': {'skills/test/SKILL.md': skill_hash, 'config.yaml': 'production-hash'}}
    class Production:
        prefix = '/v1/projects/demo'
        def environment(self, *args):
            return state
        def request(self, path, **kwargs):
            return {'version': '0.21.4'} if kwargs.get('gateway') else {'api_server_key': 'sensitive-secret'}
    runtime.production = Production()
    write_json(tmp_path / 'fixed-runtime.json', {'config.yaml': 'experiment-hash'})
    write_json(tmp_path / 'fixed-runtime-version.json', {'version': '0.21.4'})
    with pytest.raises(RuntimeError, match='Production differs'):
        runtime.verify_production_compatibility()
    recorded = json.loads((tmp_path / 'production-compatibility.json').read_text())
    assert not recorded['compatible'] and recorded['changed_files'] == ['config.yaml']
    assert 'sensitive-secret' not in (tmp_path / 'production-compatibility.json').read_text()
    state['files']['config.yaml'] = 'experiment-hash'
    runtime.verify_production_compatibility()
    assert json.loads((tmp_path / 'production-compatibility.json').read_text())['compatible']


def test_production_revision_observation_is_read_only_and_failure_is_unknown(monkeypatch):
    import evolution.experiment_runtime as module
    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.production = SimpleNamespace(base='https://example.invalid', prefix='/v1/projects/demo', token='secret')
    runtime.project = SimpleNamespace(environment_report=lambda result: result['check']['details'])
    calls = []
    def open_request(request, timeout):
        calls.append((request.full_url, request.get_method()))
        return io.BytesIO(json.dumps({'status': 'succeeded', 'result': {'check': {'details': {'revision': 'remote-sha'}}}}).encode())
    monkeypatch.setattr(module.urllib.request, 'urlopen', open_request)
    assert runtime.observe_production_revision() == 'remote-sha'
    assert calls == [('https://example.invalid/v1/projects/demo/environment/check', 'POST')]
    def unavailable(*args, **kwargs):
        raise OSError('offline')
    monkeypatch.setattr(module.urllib.request, 'urlopen', unavailable)
    assert runtime.observe_production_revision() is None


def test_search_reserve_credits_only_reusable_collected_baseline_training_cases(tmp_path):
    from evolution.dspy_loop import cached_training_credit

    runtime = object.__new__(ParallelExperimentRuntime)
    runtime.output, runtime.experiment_id, runtime.initial_body, runtime.max_runs = tmp_path, 'exp', 'baseline', 14
    state = SimpleNamespace(program_candidates=[{'produce': 'baseline'}])
    cases = [{'id': 'train-a'}, {'id': 'train-b'}]

    def save(case, body='baseline', experiment='exp', status='collected'):
        task = json.dumps(case, ensure_ascii=False, sort_keys=True)
        identity = digest((experiment + '\0' + body + '\0' + task).encode())
        write_json(tmp_path / 'trials' / identity / 'receipt.json', {'status': status})

    save({'id': 'validation'})
    save(cases[0])
    save(cases[1], status='running')
    assert cached_training_credit(runtime, state, cases) == 1
    # Receipts already occupy budget; the full held-out reserve stays intact.
    runtime.max_runs = 14
    assert not runtime.has_search_capacity(6, 6)
    assert runtime.has_search_capacity(6 - 1, 6)
    assert not runtime.has_search_capacity(6 - 1, 7)

    save(cases[1], body='other')
    save(cases[1], experiment='old-exp')
    assert cached_training_credit(runtime, state, cases) == 1
    save(cases[1])
    assert cached_training_credit(runtime, state, cases) == 2
    assert cached_training_credit(runtime, state, cases + [{'id': 'train-c'}]) == 1
    assert cached_training_credit(runtime, state, cases + [{'id': 'train-c'}, {'id': 'train-d'}]) == 0
    assert cached_training_credit(runtime, SimpleNamespace(program_candidates=[{'produce': 'changed'}]), cases) == 0
    assert cached_training_credit(runtime, SimpleNamespace(program_candidates=[{'produce': 'baseline'}, {'produce': 'changed'}]), cases) == 0
