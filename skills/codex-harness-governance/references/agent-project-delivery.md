# Agent project design and delivery loop

Read this module only in full agent-project governance mode: when an agent runtime is part of the product or team's delivery process, when a profile or Skill change must be tested through the runtime, or when the project needs a repeatable path from authored behavior to observed evidence. For an unchanged profile operation, use the narrow runtime references from `SKILL.md` instead.

## What counts as an agent project

An agent project is the combination of:

- authored behavior: profiles, Skills, context, tools, role instructions, and task contracts;
- a runtime adapter: Hermes, Codex, Claude, or another supported runtime;
- an execution target: local, remote, or both;
- observable work: traces, tool results, files, patches, tests, task-state changes, or other artifacts;
- acceptance criteria and evaluation cases.

A change to a profile or prompt is an agent-system change when it is intended to change that project's behavior. It should follow the project delivery loop even if the changed file is small.

## Boundary between local and runtime work

Use these terms explicitly:

- **Local authoring** means editing the repository source and running deterministic checks on the development machine. It proves the source is valid; it does not prove the remote runtime has applied it.
- **Local dry run** means exploratory execution against a local profile or local runtime. It helps discover issues and produce a baseline, but it is not evidence for a remote target unless the target is explicitly local.
- **Remote execution** means submitting the task to the deployed runtime that users or the team will actually use. Its applied revision, trace, state, and artifacts are the authoritative evidence for that target.
- **Runtime operation** means using an unchanged profile or gateway to submit, monitor, approve, stop, or inspect a task. It may still require the runtime's capability, execution, control-plane, or state reference so the interface is used correctly. It becomes an agent-project governance task when the request also changes, publishes, traces for evaluation, or accepts the project.
- **Runtime implementation** means changing Hermes itself, a gateway, a control service, or another runtime component. That is a separate implementation task; this Skill governs the boundary, evidence, and acceptance rather than replacing the runtime's engineering workflow.

Do not call a remote profile "already running" as if that proves the current source is deployed. Always distinguish authored revision, applied revision, and observed run.

## Design before implementation

Define the smallest useful contract before editing:

1. **Outcome** — what useful result should the agent produce?
2. **Inputs** — what task data, context, files, and permissions are available?
3. **Role boundary** — what is this profile responsible for, and what must be handed off?
4. **Tools and environment** — which tools, network surfaces, workspace, sandbox, and credentials are required?
5. **Outputs** — which response, file, patch, test result, board update, or other artifact must exist?
6. **Stopping and escalation** — when does the agent stop, ask for help, or report a blocked state?
7. **Acceptance** — which observable checks distinguish success from a plausible-looking answer?

Prefer a narrow role contract over a broad personality prompt. Keep durable project facts, repeatable procedures, runtime settings, and evaluation evidence in their respective owners.

For a commercial or user-facing deliverable, review the actual product at contract definition and final acceptance. When available, use `product-review` for this specialized judgment rather than duplicating its standards here. Keep three claims separate: improvement relative to baseline, meeting an absolute useful-product floor, and evidence of real use/payment. Automatic proxies can establish the first two within their coverage; they cannot invent market demand or user outcomes. Keep required modality and end-to-end flow in the contract: illustrated stories need pictures; a completed lesson needs its closing experience. Do not silently substitute an easier benchmark.

When authoring or improving profile behavior, use [profile-development.md](profile-development.md) to turn observed failures into a focused procedure and useful examples. Use [evals-and-feedback.md](evals-and-feedback.md) to separate development from adoption evidence and define the bounded search and decision policy.

## Remote environment readiness

If the agent project depends on packages, binaries, browser drivers, services, model access, filesystem layout, or other remote capabilities, make environment readiness an explicit release stage. Keep two reviewed, idempotent checks in the project or deployment wrapper:

- a read-only check that reports versions, paths, required services, credentials presence without printing secrets, and network or model reachability;
- an installation or repair step that uses pinned inputs, a fixed allowlist, and a repeatable result.

Run the check before publishing the profile. If it fails, run the installation step only through the approved deployment boundary, run the check again, and stop if the environment is still not ready. A `distribution.yaml` describes and packages a profile; do not assume it installs arbitrary operating-system or project dependencies unless the runtime explicitly documents that behavior.

## Delivery loop

Use this evidence sequence for profile or agent-project changes. When [DSPy Self-Evolution](dspy-self-evolution.md) owns execution, configure and inspect its receipts instead of manually implementing a second loop. The project owns business evaluation; control-plane owns deployment and artifact transport.

1. Inspect the current source, runtime version, target profile, environment, and existing baseline.
2. State one change hypothesis and the acceptance evidence it should affect.
3. Edit only the authored source owned by this change.
4. Run deterministic local checks and a small local dry run when useful.
5. Commit and push the reviewed revision to the source used by the target runtime.
6. Call the remote `project/sync` operation and verify that the observed revision equals the pushed revision.
7. Call the remote `environment/check` operation. If it is not ready, call the controlled `environment/prepare` operation, poll it, and require the post-prepare check to pass.
8. Trigger the narrow profile deployment or control-plane operation and poll it to a terminal state.
9. Confirm the remote runtime applied the intended revision, expected profile roster, and effective distribution state.
10. Verify Gateway capabilities with the separate profile API key, submit one or more representative cases through `/v1/runs`, and retain their run and event identifiers.
11. Poll each case to a documented terminal state and inspect its trace. Have the runtime write `.harness/results/<delivery-id>/result.json` and an optional `manifest.json`. Retain the separate Gateway run id in the receipt.
12. Call `runs/<delivery-id>/finalize` with a unique idempotency key and poll the finalize operation. Then fetch `runs/<delivery-id>/result`, `runs/<delivery-id>/artifacts`, and each `/v1/artifacts/<artifact-id>/download` response, verifying artifact identity and SHA-256. A status record or event stream alone is not the final result.
13. Inspect the collected result and artifacts: tool calls and outcomes, generated files or patches, tests, state changes, task updates, and failure points. Compare them with deterministic checks, a defined model-based evaluation, and the acceptance criteria. Use the design reflection in [profile-development.md](profile-development.md#reflect-on-the-design-after-each-result): identify the failure mechanism, investigate competing explanations and external methods/tools, and select the appropriate profile asset to change. Keep, revert, or revise based on evidence; the next run must test the stated prediction, not just repeat delivery.

For a remote Hermes target, use [hermes-distribution-and-deployment.md](hermes-distribution-and-deployment.md) and [hermes-control-plane.md](hermes-control-plane.md) for the concrete publish and polling steps. With the supplied LLMHub control plane, the result handoff is explicit: run `environment/check`, use `environment/prepare` when needed, publish and refresh the profiles, run the representative task, write `.harness/results/<delivery-id>/result.json` plus an optional `manifest.json`, call `runs/<delivery-id>/finalize` with an idempotency key, poll the operation, then fetch `result`, `artifacts`, and each `download` response before evaluation.

## Evidence ladder

Keep these claims separate:

- **Intended** — the source commit, target project, expected profiles, and acceptance case chosen before release;
- **Applied** — the deployment operation, terminal result, actual revision, Hermes version or image, and gateway state;
- **Observed** — the run trace, tool outcomes, events, state changes, and terminal status;
- **Collected** — the final response or result object and the files, patches, reports, or artifact bundles it references;
- **Accepted** — the explicit pass/fail decision against the acceptance criteria, including limitations.

A successful HTTP response, a completed deployment operation, a terminal run status, or a fluent final answer is only one piece of evidence. Do not promote it to an acceptance claim without the applied revision, collected final result, required artifacts, and evaluation evidence.

## Evaluation and scoring

Use more than one kind of grader when the project matters:

- **Deterministic checks** verify schemas, files, commands, tests, exit codes, routing, artifact presence, and other facts that should be exact.
- **Model-based evaluation** scores semantic quality that rules cannot reliably express, such as completeness, groundedness, plan quality, tool-use decisions, role adherence, or usefulness. Give the evaluator the task, rubric, relevant evidence, and explicit failure conditions; do not ask it to infer hidden state from the final prose alone.
- Use an independent evaluator model or a separate evaluation pass when the producer model could otherwise grade its own work. Keep fixed example cases and evaluator outputs as regression evidence.

Define dimensions, score ranges, pass thresholds, and hard-fail conditions before running trials. Use multiple representative cases when model output varies, keep the evaluator separate from the producer when practical, and do not let a high average hide a critical failure such as a wrong artifact, unauthorized action, missing required step, or identity mix-up.

## Iteration discipline

- Change one behavior family at a time: role instruction, Skill procedure, tool contract, context, model setting, or runtime/deployment behavior.
- Preserve a comparison baseline and record its revision and known defects. A rollback target is not necessarily an accepted product.
- Inspect traces and artifacts before rewriting prompts; many failures are caused by missing tools, wrong workspace, stale deployment, or task data.
- Classify failures as source, packaging, deployment, runtime, tool, task-data, or evaluation failures so the next change has a clear owner.
- Keep evidence compact and reproducible: retain identifiers, summaries, diffs, test results, and artifact paths rather than copying whole transcripts into policy.

## Completion contract

An agent-project change is complete only when:

- the authored source passes its local checks;
- the remote environment check passes, with any approved dependency preparation recorded;
- the target runtime has applied the intended committed revision;
- a representative task has completed or reached a documented terminal failure;
- the final result and referenced artifacts have been retrieved, not merely observed in a status stream;
- the required traces and artifacts have been inspected;
- deterministic and model-based evaluation has been completed;
- the acceptance decision and remaining limitations are recorded;
- the previous deployed revision, its known limits, and the recovery path remain identifiable.
