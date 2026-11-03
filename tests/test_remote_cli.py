"""Run the entire CLI with real DSPy search and a deterministic fake transport."""
import json
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import dspy
import pytest
from dspy.teleprompt.gepa.gepa_utils import DspyAdapter

from evolution import dspy_loop
from evolution.hermes_runtime import digest, write_json


@pytest.mark.parametrize('improves, interrupted_case', [(True, None), (False, None), (True, 'validation'), (True, 'train')])
def test_compile_export_holdout_and_final_release(tmp_path, monkeypatch, improves, interrupted_case):
    repo, output = tmp_path / "repo", tmp_path / "evidence"
    repo.mkdir()
    module_path = repo / "project.py"
    module_path.write_text("# frozen test project")
    project = ModuleType("_remote_cli_test_project")
    project.__file__ = str(module_path)
    project.POLICY = {"max_metric_calls": 6, "max_remote_runs": 16}
    project.calibrate = lambda lm: {"passed": True}
    project.grade = lambda folder, case, lm: json.loads((folder / "observation.json").read_text())
    project.decide = lambda comparison: {"adopt": comparison["candidate"][0]["score"] > comparison["baseline"][0]["score"]}
    monkeypatch.setitem(sys.modules, project.__name__, project)
    deployments = []
    executions = []
    execution_lock = threading.Lock()

    class Runtime:
        initial_body = "Produce an artifact."
        frontmatter = "name: reusable-artifact\ndescription: Produce artifacts for varying tasks."
        failure = None
        def __init__(self, repo, project, output):
            self.output = output
        def __deepcopy__(self, memo):
            return self
        def resume_pending(self):
            pass
        def set_run_budget(self, limit):
            self.max_runs = limit
        def observe_production_revision(self):
            return 'observed-production-sha'
        def has_search_capacity(self, next_iteration, holdout):
            return True
        def verify_production_compatibility(self):
            pass
        def execute(self, instructions, task_input):
            with execution_lock:
                executions.append(json.loads(task_input)['id'])
                folder = self.output / "trials" / digest((instructions + task_input).encode())
                if not (folder / "observation.json").exists():
                    write_json(folder / "observation.json", {"score": float("verify evidence" in instructions), "feedback": "Verify evidence."})
                    write_json(folder / "task.json", {"input": "Actual natural-language request for " + task_input})
            return json.dumps({"trial": str(folder), "trace": {"tools": ["actual-test-executor"]}})
        def deploy(self, instructions):
            deployments.append(instructions)
            return "selected-sha", {"installed": instructions}

    monkeypatch.setattr(dspy_loop, "ParallelExperimentRuntime", Runtime)
    batches = []
    original_batch = DspyAdapter.batch_evaluate
    def batch(self, items, **kwargs):
        batches.append(len(items))
        return original_batch(self, items, **kwargs)
    monkeypatch.setattr(DspyAdapter, 'batch_evaluate', batch)
    monkeypatch.setattr(dspy_loop, "git", lambda repo, *args: "" if args[0] == "status" else "baseline-sha")
    prompts = []
    def propose(self, prompt):
        prompts.append(prompt)
        correction = 'verify evidence' if improves else 'check files'
        return [{"text": f"```\nProduce an artifact; {correction}.\n```", "reasoning_content": "unused"}]
    monkeypatch.setattr(dspy.LM, "__call__", propose)
    for name, value in {"EVOLUTION_API_BASE": "https://invalid.example/v1", "EVOLUTION_API_KEY": "unused",
                        "EVOLUTION_MODEL": "openai/test", "EVOLUTION_JUDGE_MODEL": "openai/test"}.items():
        monkeypatch.setenv(name, value)
    dataset = tmp_path / "cases.json"
    write_json(dataset, {split: [{"id": split}] for split in ("train", "validation", "test")})
    context = tmp_path / 'reflection.md'
    context.write_text('Observed missing evidence; test a verify-before-edit procedure.')
    argv = ["hermes-evolve", "--repo", str(repo), "--dataset", str(dataset), "--output", str(output),
            "--project-module", project.__name__, '--reflection-context', str(context), '--max-remote-runs', '15']
    monkeypatch.setattr(sys, "argv", argv)
    if interrupted_case:
        original_grade = project.grade
        def interrupted_grade(folder, case, lm):
            if case['id'] == interrupted_case:
                raise ConnectionError('model endpoint disconnected')
            return original_grade(folder, case, lm)
        monkeypatch.setattr(project, 'grade', interrupted_grade)
        with pytest.raises(RuntimeError, match='remote evidence is invalid'):
            dspy_loop.main()
        assert (output / 'invalid-search.json').is_file()
        assert not (output / 'decision.json').exists()
        assert not deployments
        with pytest.raises(RuntimeError, match='Invalid search checkpoint'):
            dspy_loop.main()
        assert not prompts  # No proposed candidate or selection history to lose.
        preserved_grades = {p: p.read_bytes() for p in (output / 'trials').glob('*/grade.json')}
        assert bool(preserved_grades) is (interrupted_case == 'train')
        # Replay the same cached valid observations before the first proposal;
        # retain both the invalid checkpoint and the original trial ledger.
        (output / 'gepa').rename(output / 'gepa-invalid-initial')
        (output / 'invalid-search.json').rename(output / 'invalid-search-archived.json')
        recovered_grade = Mock(wraps=original_grade)
        monkeypatch.setattr(project, 'grade', recovered_grade)
    dspy_loop.main()
    if interrupted_case:
        assert all(p.read_bytes() == content for p, content in preserved_grades.items())
        assert all(call.args[0] / 'grade.json' not in preserved_grades for call in recovered_grade.call_args_list)
    decision = json.loads((output / "decision.json").read_text())
    assert decision['adopt'] is improves
    assert decision['changed'] is improves
    assert ('test' in executions) is improves
    search = json.loads((output / "search.json").read_text())
    assert ('verify evidence' in search['candidates'][search['best_idx']]['produce']) is improves
    assert bool(deployments) is improves
    if improves:
        assert 'verify evidence' in deployments[-1]
    if not improves:
        assert decision['held_out'] == 'not_run_no_changed_candidate'
        assert json.loads((output / 'comparison.json').read_text()) == {'baseline': [], 'candidate': []}
        assert not deployments
    assert (output / "program.json").is_file()
    assert prompts and "actual_task_request" in prompts[0]
    assert max(batches) >= 2
    assert "Actual natural-language request" in prompts[0]
    assert "reusable-artifact" in prompts[0]
    assert "not the literal message" in prompts[0]
    assert context.read_text() in prompts[0]
    assert (output / 'reflection-context.md').read_text() == context.read_text()
    selected = json.loads((output / "selected-release.json").read_text())
    assert selected['baseline_revision'] == 'baseline-sha'
    assert selected['production_revision'] == ('selected-sha' if improves else 'observed-production-sha')
    assert selected['verification_status'] == ('verified_installed' if improves else 'checkout_observed')

    manifest = json.loads((output / "experiment.json").read_text())
    assert manifest['contract']['max_remote_runs'] == 15
    monkeypatch.setattr(sys, 'argv', argv + ['--max-remote-runs', '16'])
    with pytest.raises(RuntimeError, match='Experiment inputs changed'):
        dspy_loop.main()
    manifest["contract"]["engine_sha256"] = "previous-export-only-version"
    write_json(output / "experiment.json", manifest)
    monkeypatch.setattr(sys, "argv", argv + ["--resume-engine-fix", "Export-only repair; no experimental inputs changed."])
    dspy_loop.main()
    repaired = json.loads((output / "experiment.json").read_text())
    assert repaired["engine_repairs"][0]["previous_sha256"] == "previous-export-only-version"
    assert repaired["experiment_id"] == manifest["experiment_id"]
    original_context = context.read_text()
    context.write_text('A different hypothesis must start a new experiment.')
    with pytest.raises(RuntimeError, match='Experiment inputs changed'):
        dspy_loop.main()
    context.write_text(original_context)
    def unavailable(self, instructions):
        raise RuntimeError("release unavailable")
    monkeypatch.setattr(Runtime, "deploy", unavailable)
    if improves:
        with pytest.raises(RuntimeError, match="release unavailable"):
            dspy_loop.main()
    else:
        dspy_loop.main()
    assert json.loads((output / "selected-release.json").read_text())["status"] == ('publication_failed' if improves else 'not_published')
    repaired["contract"]["dataset_sha256"] = "different-cases"
    write_json(output / "experiment.json", repaired)
    with pytest.raises(RuntimeError, match="Experiment inputs changed"):
        dspy_loop.main()


def test_failed_calibration_stops_search_and_production_release(tmp_path, monkeypatch):
    repo, output = tmp_path / 'repo', tmp_path / 'evidence'
    repo.mkdir()
    project = ModuleType('_bad_calibration_project')
    project.__file__ = str(repo / 'project.py')
    (repo / 'project.py').write_text('# project')
    project.POLICY = {'max_metric_calls': 6, 'max_remote_runs': 16}
    project.calibrate = lambda lm: {'passed': False}
    monkeypatch.setitem(sys.modules, project.__name__, project)
    class Runtime:
        initial_body = 'baseline'
        frontmatter = 'name: test'
        experiment_id = ''
        def __init__(self, *args):
            pass
        def resume_pending(self):
            pass
        def set_run_budget(self, limit):
            pass
        def deploy(self, body):
            raise AssertionError('Production release must not run')
    monkeypatch.setattr(dspy_loop, 'ParallelExperimentRuntime', Runtime)
    monkeypatch.setattr(dspy_loop, 'git', lambda repo, *args: '' if args[0] == 'status' else 'baseline')
    for name, value in {'EVOLUTION_API_BASE': 'https://invalid.example/v1', 'EVOLUTION_API_KEY': 'unused',
                        'EVOLUTION_MODEL': 'openai/test', 'EVOLUTION_JUDGE_MODEL': 'openai/test'}.items():
        monkeypatch.setenv(name, value)
    dataset = tmp_path / 'cases.json'
    write_json(dataset, {s: [{'id': s}] for s in ('train', 'validation', 'test')})
    monkeypatch.setattr(sys, 'argv', ['hermes-evolve', '--repo', str(repo), '--dataset', str(dataset),
                                     '--output', str(output), '--project-module', project.__name__])
    with pytest.raises(RuntimeError, match='calibration failed'):
        dspy_loop.main()
    assert not (output / 'gepa').exists()
    assert not (output / 'selected-release.json').exists()
    for invalid in ('0', '17'):
        monkeypatch.setattr(sys, 'argv', ['hermes-evolve', '--repo', str(repo), '--dataset', str(dataset),
            '--output', str(output), '--project-module', project.__name__, '--max-remote-runs', invalid])
        with pytest.raises(SystemExit):
            dspy_loop.main()


@pytest.mark.parametrize('fail_judge', [False, True])
def test_holdout_runs_four_in_parallel_preserves_pairs_and_blocks_failure(tmp_path, monkeypatch, fail_judge):
    repo, output = tmp_path / 'repo', tmp_path / 'evidence'
    repo.mkdir()
    (repo / 'project.py').write_text('# frozen project')
    project = ModuleType('_parallel_holdout_project')
    project.__file__ = str(repo / 'project.py')
    project.POLICY = {'max_metric_calls': 6, 'max_remote_runs': 16}
    project.calibrate = lambda lm: {'passed': True}
    def grade(folder, case, lm):
        if fail_judge and case['id'] == 'test-a':
            raise ConnectionError('judge unavailable')
        return json.loads((folder / 'observation.json').read_text())
    project.grade = grade
    def decide(comparison):
        assert [row['case_id'] for row in comparison['baseline']] == ['test-a', 'test-b']
        assert [row['case_id'] for row in comparison['candidate']] == ['test-a', 'test-b']
        return {'adopt': True}
    project.decide = decide
    monkeypatch.setitem(sys.modules, project.__name__, project)
    barrier = threading.Barrier(4, timeout=10)
    lock = threading.Lock()
    active, peak, deployments = 0, 0, []
    class Runtime:
        initial_body, frontmatter, failure = 'Baseline', 'name: test', None
        def __init__(self, repo, project, output):
            self.output = output
        def __deepcopy__(self, memo):
            return self
        def set_run_budget(self, limit):
            pass
        def resume_pending(self):
            pass
        def has_search_capacity(self, next_iteration, holdout):
            return True
        def observe_production_revision(self):
            return 'production'
        def verify_production_compatibility(self):
            pass
        def execute(self, instructions, task_input):
            nonlocal active, peak
            case = json.loads(task_input)
            with lock:
                active += 1
                peak = max(peak, active)
            barrier.wait()
            # Finish the second case first, to test result pairing independently of completion order.
            if case['id'] == 'test-a':
                time.sleep(0.05)
            folder = self.output / 'trials' / digest((instructions + task_input).encode())
            write_json(folder / 'observation.json', {'score': float(instructions == 'Candidate')})
            write_json(folder / 'task.json', case)
            with lock:
                active -= 1
            return json.dumps({'trial': str(folder), 'trace': {}})
        def deploy(self, body):
            deployments.append(body)
            return 'selected', {}
    class Optimizer:
        def __init__(self, **kwargs):
            pass
        def compile(self, program, **kwargs):
            candidate = dspy_loop.HermesSkillProgram('Candidate', program.remote_adapter.runtime)
            candidate.detailed_results = SimpleNamespace(
                candidates=[program, candidate], parents=[], val_aggregate_scores=[], val_subscores=[],
                discovery_eval_counts=[], total_metric_calls=0, num_full_val_evals=0, best_idx=1, seed=0,
                per_val_instance_best_candidates={})
            return candidate
    monkeypatch.setattr(dspy_loop, 'ParallelExperimentRuntime', Runtime)
    monkeypatch.setattr(dspy, 'GEPA', Optimizer)
    monkeypatch.setattr(dspy_loop, 'git', lambda repo, *args: '' if args[0] == 'status' else 'baseline')
    for name, value in {'EVOLUTION_API_BASE': 'https://invalid.example/v1', 'EVOLUTION_API_KEY': 'unused',
                        'EVOLUTION_MODEL': 'openai/test', 'EVOLUTION_JUDGE_MODEL': 'openai/test'}.items():
        monkeypatch.setenv(name, value)
    dataset = tmp_path / 'cases.json'
    write_json(dataset, {'train': [{'id': 'train'}], 'validation': [{'id': 'validation'}],
                         'test': [{'id': 'test-a'}, {'id': 'test-b'}]})
    monkeypatch.setattr(sys, 'argv', ['hermes-evolve', '--repo', str(repo), '--dataset', str(dataset),
                                     '--output', str(output), '--project-module', project.__name__])
    if fail_judge:
        with pytest.raises(ConnectionError, match='judge unavailable'):
            dspy_loop.main()
        assert not (output / 'decision.json').exists()
        assert not deployments
    else:
        dspy_loop.main()
        assert json.loads((output / 'decision.json').read_text())['adopt']
        assert deployments == ['Candidate']
    assert peak == 4
