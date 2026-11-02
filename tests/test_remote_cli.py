"""Run the entire CLI with real DSPy search and a deterministic fake transport."""
import json
import sys
from types import ModuleType

import dspy
import pytest

from evolution import dspy_loop
from evolution.hermes_runtime import digest, write_json


def test_compile_export_holdout_and_final_release(tmp_path, monkeypatch):
    repo, output = tmp_path / "repo", tmp_path / "evidence"
    repo.mkdir()
    module_path = repo / "project.py"
    module_path.write_text("# frozen test project")
    project = ModuleType("_remote_cli_test_project")
    project.__file__ = str(module_path)
    project.POLICY = {"max_metric_calls": 6}
    project.calibrate = lambda lm: {"passed": True}
    project.grade = lambda folder, case, lm: json.loads((folder / "observation.json").read_text())
    project.decide = lambda comparison: {"adopt": comparison["candidate"][0]["score"] > comparison["baseline"][0]["score"]}
    monkeypatch.setitem(sys.modules, project.__name__, project)
    deployments = []

    class Runtime:
        initial_body = "Produce an artifact."
        frontmatter = "name: reusable-artifact\ndescription: Produce artifacts for varying tasks."
        failure = None
        def __init__(self, repo, project, output):
            self.output = output
        def __deepcopy__(self, memo):
            return self
        def execute(self, instructions, task_input):
            folder = self.output / "trials" / digest((instructions + task_input).encode())
            write_json(folder / "observation.json", {"score": float("verify evidence" in instructions), "feedback": "Verify evidence."})
            write_json(folder / "task.json", {"input": "Actual natural-language request for " + task_input})
            return json.dumps({"trial": str(folder), "trace": {"tools": ["actual-test-executor"]}})
        def deploy(self, instructions):
            deployments.append(instructions)
            return "selected-sha", {"installed": instructions}

    monkeypatch.setattr(dspy_loop, "HermesRuntime", Runtime)
    monkeypatch.setattr(dspy_loop, "git", lambda repo, *args: "" if args[0] == "status" else "baseline-sha")
    prompts = []
    def propose(self, prompt):
        prompts.append(prompt)
        return [{"text": "```\nProduce an artifact; verify evidence.\n```", "reasoning_content": "unused"}]
    monkeypatch.setattr(dspy.LM, "__call__", propose)
    for name, value in {"EVOLUTION_API_BASE": "https://invalid.example/v1", "EVOLUTION_API_KEY": "unused",
                        "EVOLUTION_MODEL": "openai/test", "EVOLUTION_JUDGE_MODEL": "openai/test"}.items():
        monkeypatch.setenv(name, value)
    dataset = tmp_path / "cases.json"
    write_json(dataset, {split: [{"id": split}] for split in ("train", "validation", "test")})
    argv = ["hermes-evolve", "--repo", str(repo), "--dataset", str(dataset), "--output", str(output),
            "--project-module", project.__name__]
    monkeypatch.setattr(sys, "argv", argv)
    dspy_loop.main()
    assert json.loads((output / "decision.json").read_text())["adopt"]
    search = json.loads((output / "search.json").read_text())
    assert "verify evidence" in search["candidates"][search["best_idx"]]["produce"]
    assert "verify evidence" in deployments[-1]
    assert (output / "program.json").is_file()
    assert prompts and "actual_task_request" in prompts[0]
    assert "Actual natural-language request" in prompts[0]
    assert "reusable-artifact" in prompts[0]
    assert "not the literal message" in prompts[0]
    assert json.loads((output / "selected-release.json").read_text())["revision"] == "selected-sha"

    manifest = json.loads((output / "experiment.json").read_text())
    manifest["contract"]["engine_sha256"] = "previous-export-only-version"
    write_json(output / "experiment.json", manifest)
    monkeypatch.setattr(sys, "argv", argv + ["--resume-engine-fix", "Export-only repair; no experimental inputs changed."])
    dspy_loop.main()
    repaired = json.loads((output / "experiment.json").read_text())
    assert repaired["engine_repairs"][0]["previous_sha256"] == "previous-export-only-version"
    assert repaired["experiment_id"] == manifest["experiment_id"]
    def unavailable(self, instructions):
        raise RuntimeError("release unavailable")
    monkeypatch.setattr(Runtime, "deploy", unavailable)
    with pytest.raises(RuntimeError, match="release unavailable"):
        dspy_loop.main()
    assert json.loads((output / "selected-release.json").read_text())["status"] == "pending"
    repaired["contract"]["dataset_sha256"] = "different-cases"
    write_json(output / "experiment.json", repaired)
    with pytest.raises(RuntimeError, match="Experiment inputs changed"):
        dspy_loop.main()
