# Hermes Agent Self-Evolution: remote DSPy loop

This fork of [Nous Research Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution) runs DSPy + GEPA against **actual deployed Hermes work**, not an LLM pretending to use a Skill. Upstream base: `0a929e3aa20e15cf04dc7c28492a7d41a5139125`.

The implemented production path is `hermes-evolve`. It optimizes one declared Skill body per experiment. Tool descriptions, runtime source and whole-profile topology are not optimized by this command. No new server, daemon, task runtime or control-plane optimizer is introduced.

## Ownership

| Owner | Responsibility |
|---|---|
| DSPy / GEPA | Candidate instructions, reflection from real feedback, search, validation selection, search checkpoint |
| Self-Evolution client | Deploy candidate, run Hermes, collect evidence, bind compiled instructions to installed Skill, final comparison and restore/adopt |
| Project adapter | Task and artifact contract, environment facts, deterministic checks, independent semantic grader, calibration, adoption gates |
| Hermes | Execute the task with its installed profile, native tools, session state and trace |
| LLMHub control-plane | Git registration/sync, fixed environment scripts, profile refresh, result/artifact registration and download |
| Codex governance Skill | Architecture, capability research, experiment design and interpretation; it does not run a competing search loop |

`HermesSkillProgram.produce` is a real `dspy.Predict`. Its adapter uses `signature.instructions` as the exact deployed Skill body. Standard DSPy traces therefore connect the same optimized predictor to the remote artifact; a unit test compiles and reloads it to verify this connection. A separate evaluator sees the artifact and task, not the candidate instructions or producer self-score.

## Install

Use Python 3.11+ for the demo project:

```bash
git clone https://github.com/xiaoyangmai/hermes-agent-self-evolution.git
cd hermes-agent-self-evolution
pip install -e '.[dev,browser]'
```

Dependencies pin DSPy 3.2.1 and GEPA 0.0.27. The [demo project](https://github.com/xiaoyangmai/demo-team) uses Playwright with an installed Edge browser. Another project may use different artifact checks without installing browser dependencies. `LITELLM_LOCAL_MODEL_COST_MAP=True` is set before DSPy import so startup does not depend on downloading a cost map; no cost estimate is asserted from that map.

Set these environment variables using your credential manager or local session, never a committed file:

```text
HERMES_CONTROL_URL       control service base URL
HERMES_CONTROL_TOKEN     control service bearer token
HERMES_GATEWAY_URL       optional; defaults to CONTROL_URL/gateway
EVOLUTION_API_BASE      OpenAI-compatible model API base, including /v1
EVOLUTION_API_KEY       model API credential
EVOLUTION_MODEL         DSPy model id for reflection, e.g. openai/<served-model>
EVOLUTION_JUDGE_MODEL   DSPy model id for independent assessment
```

Profile Gateway keys are fetched from the existing authenticated control API and kept in memory. The model API is separate from the Hermes Gateway task API. The client does not require SSH; a tunnel is one optional development connection to a private model endpoint.

## Project contract and execution

A project module, by default `harness.dspy_project`, exports:

- `PROJECT`, `PROFILE`, `PROFILES`, `SKILL`, `POLICY` (metric/run budgets, run deadline and project decision thresholds).
- `task(case, delivery_id, revision)` produces the real Gateway request.
- `environment_report(operation_result)` exposes readiness, installed file hashes and source revision from the project's fixed check script.
- `trace_summary(rows)` and `verify_trace(summary)` retain useful evidence and verify the target Skill was loaded.
- `calibrate(judge_lm)` returns a persisted automatic calibration result with `passed`.
- `grade(trial_folder, case, judge_lm)` checks downloaded artifacts and returns score, dimensions, pass/fail and evidence.
- `decide(comparison)` returns the final `adopt` decision and reasons. This runs after search, outside GEPA.

Keep private cases and outputs outside the deployed Git repository. Dataset JSON contains exactly `train`, `validation`, `test`, each a nonempty list of cases with globally unique `id`; case-specific fields belong to the project. Different replica ids mean separate real runs. Train and validation feed search; test results never feed another candidate in that experiment.

```bash
hermes-evolve --repo /path/to/demo-team \
  --dataset /private/experiment/cases.json \
  --output /private/experiment/evidence
```

Commit authored changes before invocation. The command intentionally creates and pushes ordinary candidate commits to the registered repository's current branch. LLMHub sync currently pulls remote HEAD, so reserve this project for the experiment and do not concurrently edit/push it. A local git status and exact remote revision comparison enforce the observed source boundary. Four named demo profiles are retained; only frontend's declared Skill body is optimized.

The finite loop performs:

1. Freeze dataset, project/engine source hashes, policy, models and baseline. Calibrate automatic graders.
2. GEPA proposes/evaluates candidates within the metric-call budget. Unique candidate/case executions have durable receipts; repeated optimizer evaluation uses the same observation, not a fresh best-of sample.
3. Commit/push → project sync → environment check/controlled prepare → idle-profile check → one refresh → installed hash verification.
4. Submit a fresh remote task, poll the original run/deadline, collect durable tool history and verify Skill loading. Check runtime context again at termination.
5. Finalize the explicit delivery id, fetch result and manifest, download bytes, verify artifact id and SHA-256, and evaluate independently.
6. Save the compiled DSPy program, select by validation, then run a counterbalanced baseline/candidate held-out comparison.
7. Apply the project's frozen adoption gate. Restore baseline on rejection/error using a normal commit and HTTP release; verify effective installed state. No force push, hidden runtime patch or human grading.

GEPA's metric-call budget counts evaluations, including cached observations. `max_remote_runs` separately caps actual task submissions. Each task has a fixed elapsed-time budget. A stop request is not terminal evidence; an unresolved active task blocks refresh and must be recovered before continuing.

## Evidence, failures and resume

The output directory contains `experiment.json`, `calibration.json`, `fixed-runtime.json`, `gepa/`, compiled `program.json`, `search.json`, `candidate_skill.md`, `comparison.json`, `decision.json`, and `selected-release.json`. Per-trial receipts bind experiment/case/candidate, source revision, Gateway run id and delivery id to downloaded artifacts, trace, browser screenshots and `grade.json`. Release receipts retain asynchronous operation results and capabilities.

Reuse the same output directory to resume the same frozen experiment. Changed experimental inputs require a new directory. A reviewed transport/export-only code repair can resume with `--resume-engine-fix "reason"`: the manifest retains old/new engine hashes and the reason, and still rejects changed cases, project/grader source, models or policy. Do not use this for a changed proposal method, runtime behavior or scoring. Completed observations and operations are reused; do not delete receipts to obtain more favorable outputs. A different experiment gets different delivery ids. Infra/transport/invalid-trace failures stop search rather than becoming misleading prompt-quality zeros. An artifact failing its deterministic contract is a real scored defect and cannot be adopted.

If the client is interrupted during a run, restore its model/API connectivity and rerun with the original output. If automatic restoration cannot finish because a run remains active or the service is unavailable, the missing `selected-release.json` means restoration is **not confirmed**; inspect the retained run/operation receipts before further mutation.

A rejected candidate is a valid optimization outcome, not a quality-improvement claim. Repeated runs support only the cases and proxy rubric tested. Same-family model judges have correlated bias; automatic calibration does not establish real-world user benefit. This fork does not promise fixed per-run cost or statistically significant improvement.

## Governance Skill and validation

`skills/codex-harness-governance` is the versioned source installed into Codex global Skills. Its entrypoint routes lightweight runtime operation separately from project design and DSPy optimization. It is not installed into Hermes producer profiles.

```bash
LITELLM_LOCAL_MODEL_COST_MAP=True python -m pytest -q
```

Upstream text-only `python -m evolution.skills.evolve_skill` remains available for local text experiments. It now exports the actually optimized signature and uses semantic grading; it does **not** establish remote Hermes behavior, perform the remote artifact loop, or replace `hermes-evolve`. [PLAN.md](PLAN.md) is upstream design context, not a claim of implemented capabilities in this fork.

MIT — original work © 2026 Nous Research. See [LICENSE](LICENSE).
