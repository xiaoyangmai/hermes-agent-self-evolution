# Hermes Self-Evolution with DSPy

Read this only for an authorized Hermes optimization project. For an unchanged task invocation, use [control-plane operation](hermes-control-plane.md). The maintained executable implementation is [the Self-Evolution fork](https://github.com/xiaoyangmai/hermes-agent-self-evolution); its README and current source define the CLI and adapter contract. [demo-team](https://github.com/xiaoyangmai/demo-team) supplies one concrete project adapter.

## One owner for each loop

| Layer | Owns | Does not own |
|---|---|---|
| Codex and this Skill | Goal, architecture, diagnosis, capability research, experiment contract, interpretation | A second candidate scheduler running alongside GEPA |
| DSPy GEPA in Self-Evolution | Candidate instructions, reflective proposals, validation selection, search checkpoint | Task execution runtime or Kubernetes management |
| Self-Evolution remote client | Finite deploy/run/collect/evaluate workflow, compiled Skill export, final adopt/restore | A new daemon, API service, general task scheduler |
| Project adapter | Task, artifact schema, grader calibration, quality dimensions and adoption policy | Generic optimization engine |
| Hermes profile/Gateway | Actual tools, task execution, session trace and artifact production | Independent acceptance of its own work |
| LLMHub control-plane | Repository sync, controlled environment, profile release, result/artifact transport | Candidate search, reflection, quality score, winner registry |

Do not remove environment/check/prepare or finalize/result/artifacts/download merely because the optimizer calls them. These provide remote authority and artifact transport the optimizer needs. Remove genuinely duplicated search, scoring or promotion code only after checking callers; the current LLMHub control service has no such optimization subsystem.

## What DSPy actually changes

The selected native Skill body is the `dspy.Predict` signature instructions. The remote adapter writes those exact instructions into the repository Skill, preserving frontmatter; commits/pushes; publishes; and executes Hermes. GEPA's normal predictor trace therefore contains the actual remote output and feedback. The candidate tested remotely must match `program.json`. After rejection, the final installed Skill intentionally matches the baseline instead; `selected-release.json` records that final applied choice. Do not mistake a saved compiled candidate for an adopted release.

Do not optimize an unused prompt while exporting an unchanged `skill_text` member. Do not fabricate a DSPy trace, simulate Hermes with a direct LLM answer, or present a text-only Skill experiment as remote acceptance.

The current remote CLI optimizes one Skill body per experiment. It does not search SOUL, tools, dependencies, four roles or model settings simultaneously. If failure evidence points to one of those owners, Codex researches and changes that asset separately, verifies it, then creates a new comparable experiment. GEPA's reflection model has no automatic web/tool research capability in this adapter; do not claim it has one.

Bind reflection to the fixed Skill identity and the actual runtime request, not merely serialized optimizer inputs. Use contrasting training cases and keep domain rules conditional. The adapter supplies these facts through a custom GEPA instruction proposer; it requests a small procedural correction rather than a longer prompt. Inspect the installed DSPy adapter before assuming a native GEPA template option reaches the proposer. A scope diagnostic can check this mechanism, but only fresh remote artifacts can establish its quality effect.

## Prepare the experiment

1. Read current engine README, project adapter and applicable repository instructions. Verify installed DSPy/GEPA versions and actual Gateway capabilities. The validated pins are DSPy 3.2.1 and GEPA 0.0.27; upgrades need integration verification.
2. State the useful output and observable failure mechanism. Choose the optimizable file and freeze other behavior inputs. The current demo targets a four-page illustrated children's comic with two interactive questions and a practical ending. Earlier learning-page experiments remain different contracts; their scores are not comparable.
3. Define the project task, result/manifest, fixed environment scripts, trace-loading check, artifact checker, independent model rubric and adoption rule in its adapter. Do not copy the demo's educational rubric to unrelated products.
4. Keep private cases and evidence outside the producer repository. Train feeds proposals, validation selects candidates, held-out cases decide adoption once. Give replicas different ids; repeated evaluation of the same candidate/case is a cached observation, not a new replicate.
5. Freeze cases, policy, code, models, budgets and baseline before production. Calibrate semantic boundaries automatically using positive/negative controls. No human grading fallback; a failed or uncertain gate prevents adoption.
6. Reserve the shared project/Gateway during search. This control-plane syncs the registered remote HEAD and refreshes the registered roster, so serial operation and exact revision checks matter. Never invent per-profile update isolation the API does not provide.

## Execute and inspect

Use the installed `hermes-evolve --repo ... --dataset ... --output ...` entrypoint; credentials come from environment variables documented by the engine, never from this Skill. Obtain profile Gateway keys through the control API; model API credentials are separate.

Resolve the engine's Python environment before invoking it; a virtual-environment installation is not necessarily on PATH. Use its `bin/hermes-evolve` or Windows `Scripts/hermes-evolve.exe`, or activate the environment. Verify the configured model endpoint is reachable separately from the Hermes task API.

The engine owns commit/push, sync, environment check/prepare, refresh, installed hash verification, actual task submission, terminal observation, trace collection, finalize and downloads. See [control-plane contracts](hermes-control-plane.md) for the transport. Do not additionally invoke a manual release/round loop around each engine call.

Check five concrete connections in the evidence:

- optimized signature → exported Skill body;
- candidate commit → remotely checked-out revision → installed file hash;
- fresh Gateway run → trace proving the intended Skill was loaded;
- run/delivery binding → registered result → downloaded artifact id and checksum;
- artifact and interaction evidence → independent grades → frozen adoption decision.

`gateway_run_id` and `delivery_id` are different identifiers. The latter names `.harness/results/<delivery_id>/` and the control-plane finalize/result path. Preserve both in the local receipt.

Infrastructure, model access and context-drift errors invalidate an experiment; they must not masquerade as a bad prompt score. A correctly observed artifact defect is a real quality failure. Keep failed samples and any incomplete restoration visible. Resume the original receipt and deadline rather than rerunning anonymously until success.

Check `invalid-search.json` before resuming after an evaluation failure: DSPy may have cached the exception as a zero. Preserve the invalid optimizer state. A failure on the initial evaluation, before any proposal, can restart search after quarantining that state and marker while reusing the original collected artifact. Later failures require a known valid checkpoint or a new, explicitly budgeted experiment. Follow the engine's recovery contract; never quietly accept the cached zero or erase prior valid search work.

If only transport or result export code was repaired, the engine supports `--resume-engine-fix "audited reason"` while retaining previous/new engine hashes. All other frozen inputs must still match. Verify the diff did not change proposals, production behavior or grading; otherwise start a new experiment. This preserves valid observations without disguising changed experimental conditions.

## Decide without concealing regression

Validation selection is not adoption. Evaluate the frozen winner and baseline on the reserved comparison; counterbalance order where practical. Require required artifacts and semantic gates, then check per-case dimensions and meaningful gain. A higher average must not hide a regression in an already-working capability. The demo's exact thresholds belong to its adapter, not this Skill.

When validation retains the unchanged baseline, the engine records `search_retained_baseline`, leaves the held-out comparison empty, and restores/verifies that baseline. No new version exists to justify expensive comparison runs. Report this as no selected improvement, not as passing a held-out evaluation; preserve those unexecuted cases for a later experiment.

Report completed run count, delivered artifacts, per-case paired scores, grader disagreement, hard failures, time/usage evidence and final applied revision. Separate search evaluations from unique executions and held-out replicas. Small same-family model comparisons support a local proxy decision, not external ground truth, stable population-level improvement or demonstrated learning by children.

On rejection, restore the declared baseline through Git and the ordinary release path and verify installed state. If the service is unavailable or a run is still active, report restoration pending; a `finally` block alone does not prove recovery. If budgets end without improvement, retain that result. Another experiment needs a justified hypothesis and fresh held-out evidence when previous outcomes informed the edit.

Codex still performs the higher-level reflection in [profile development](profile-development.md): inspect mechanism, research methods/tools when appropriate, choose the correct owner, and test a prediction. It does not hand-edit the optimized Skill midway through a running GEPA experiment.

Pass a concise reviewed hypothesis and relevant research/previous failures through `--reflection-context <file>` when continuing a bounded project iteration. The engine hashes and retains this input; changing it requires a new experiment. It informs GEPA's proposal, not the independent grader. Keep current held-out outcomes out of it until that experiment ends, then relabel exposed cases as development/regression. This connects outer diagnosis to the existing optimizer without adding a second scheduler. If three iterations are authorized, finish three bounded experiments or report a demonstrated blocker; do not count three executions of one unchanged prompt as three iterations.

## Progressive loading and maintenance

Keep API details in the control reference, project quality rules in the project, engine behavior in its versioned source, and architecture here. The global Codex installation is a copy of `skills/codex-harness-governance` in the fork; validate and compare it after updates. Do not install this governance Skill into producer profiles or introduce `profile-workmode`.

Primary implementation references: [upstream Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution), [DSPy GEPA](https://dspy.ai/api/optimizers/GEPA/), [GEPA source](https://github.com/gepa-ai/gepa). Check source at the installed version before relying on callbacks, metrics, resume or serialization behavior.
