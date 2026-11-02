import copy
import json
import os
from pathlib import Path

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
import dspy

from evolution.dspy_loop import HermesSkillProgram


class FakeRemote:
    def __init__(self):
        self.calls = []

    def __deepcopy__(self, memo):
        return self

    def execute(self, instruction, task):
        self.calls.append((instruction, task))
        return json.dumps({"correct": "verify evidence" in instruction, "case": task})


def test_dspy_optimizes_the_instruction_actually_sent_to_remote(tmp_path):
    remote = FakeRemote()
    program = HermesSkillProgram("Produce a useful artifact.", remote)
    # Predict's backend is the remote adapter; this LM is only an interface handle.
    dspy.configure(lm=dspy.LM("openai/test", api_key="unused"))
    data = [dspy.Example(task_input=t).with_inputs("task_input") for t in ("a", "b")]

    def metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
        ok = json.loads(pred.output)["correct"]
        return dspy.Prediction(score=float(ok), feedback="The artifact must verify evidence before changing established content.")

    proposals = []
    def propose(candidate, reflective_dataset, components_to_update):
        proposals.append(reflective_dataset)
        return {name: "Produce a useful artifact; verify evidence before editing." for name in components_to_update}

    optimizer = dspy.GEPA(metric=metric, max_metric_calls=8, instruction_proposer=propose,
                          num_threads=1, reflection_minibatch_size=1, use_merge=False,
                          track_stats=True, log_dir=str(tmp_path / "search"))
    compiled = optimizer.compile(program, trainset=data, valset=data)
    assert proposals and proposals[0]["produce"]
    assert "verify evidence" in compiled.produce.signature.instructions
    assert any("verify evidence" in instruction for instruction, _ in remote.calls)
    compiled.save(str(tmp_path / "program.json"))
    loaded = HermesSkillProgram("placeholder", remote)
    loaded.load(str(tmp_path / "program.json"))
    assert json.loads(loaded(task_input="fresh").output)["correct"]
    assert loaded.produce.signature.instructions == compiled.produce.signature.instructions
    assert copy.deepcopy(remote) is remote


def test_actual_predict_trace_is_preserved():
    remote = FakeRemote()
    program = HermesSkillProgram("Read evidence.", remote)
    dspy.configure(lm=dspy.LM("openai/test", api_key="unused"))
    with dspy.context(trace=[]):
        output = program(task_input="case")
        trace = list(dspy.settings.trace)
    assert trace[0][0] is program.produce
    assert trace[0][1] == {"task_input": "case"}
    assert trace[0][2].output == output.output
