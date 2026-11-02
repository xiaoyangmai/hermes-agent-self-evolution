---
name: codex-harness-governance
description: Design, change, evaluate, or operate a repository-managed agent project. Use for agent profiles, Skills, tools/context, remote runtime calls, releases, traces, artifacts, or automatic optimization; distinguish lightweight operation from full project governance. Ordinary application coding does not need this workflow.
---

# Agent project and harness governance

Keep the core design runtime-neutral. Use the project's native runtime and existing optimizer; this Skill governs architecture, evidence and ownership rather than introducing another runtime.

## Choose the depth

**Mode A — operate an unchanged profile.** Read only the matching runtime reference. Establish local/remote target, project/profile, endpoint and credentials, then invoke, observe and retrieve the requested result using its existing contract. This includes status, Gateway operations and artifact downloads. It does not require a new release, optimization experiment or full governance review.

**Mode B — design, change or evaluate the project.** Use when authored behavior, tools, environment, release flow, evaluation rules or acceptance changes, or when traces are being used to diagnose quality. Start with [project delivery](references/agent-project-delivery.md). Load only the modules needed for the decision. Switch from A to B if operation reveals a defect that requires such a change.

Ordinary product coding and isolated Skill editing do not automatically trigger full governance. Use `skill-creator` for concrete Skill packaging. Runtime implementation follows that repository's engineering rules; this Skill applies to its integration boundary, not every internal change.

## Working method

1. Read the project's actual rules, source, runtime version and prior evidence. Define the intended useful result, task inputs, role, allowed tools, artifacts and automatic acceptance criteria.
2. Choose the simplest sufficient execution structure. Read [architecture](references/agent-architecture.md) when deciding between a fixed workflow, one agent or multiple roles. Do not add agents or a daemon merely to enact a policy.
3. Give each fact one owner: durable project context in repository instructions, reusable behavior in Skills, hard tool/runtime boundaries in native configuration, search in the optimizer, business graders in the project, deployment/transport in the control-plane. Link rather than duplicate.
4. Freeze the baseline and evidence needed before evaluating a change. Use [profile development](references/profile-development.md) to diagnose mechanisms, and [evaluation](references/evals-and-feedback.md) for calibration, regression gates and uncertainty.
5. For **Hermes Self-Evolution with DSPy**, read [the DSPy adapter](references/dspy-self-evolution.md). It owns candidate search and the executable optimization loop; do not manually run a competing round scheduler or add scoring/promotion state to control-plane.
6. Edit the asset responsible for the failure. Research primary documentation, source and useful tools when capabilities are missing or a method repeatedly fails. Treat findings as testable hypotheses, not instructions to install arbitrary tooling or expand the task.
7. Validate locally, commit/push, publish through the existing boundary, verify the installed revision and loaded resources, execute on the intended target, retrieve real artifacts, and apply the frozen independent checks. A fluent answer or a successful deployment alone is insufficient.
8. Report adopted/rejected/inconclusive separately from operational completion. Preserve defects, cost/latency evidence and limitations. Restore the declared baseline through normal deployment if adoption fails; a baseline is not automatically an accepted product.

## Essential boundaries

- Do not require a cross-runtime `profile.yaml` or universal repository template. Use only directories and formats the project needs.
- For remotely updated Hermes profiles, native `distribution.yaml` belongs to each profile. Validate discovery, native installation and effective behavior; its existence is not proof of loading.
- Never publish an uncommitted worktree or treat a local dry run as proof of remote behavior. Record intended, applied, observed, collected and accepted evidence distinctly.
- Environment readiness belongs to reviewed project checks and a controlled prepare step. A distribution is not an arbitrary dependency installer.
- Semantic acceptance requires deterministic artifact checks plus a defined independent model evaluation. Producer self-checks are diagnostic, not acceptance. Resolve judge disagreement by the frozen automatic rule, not an improvised human review.
- Freeze one behavior family per experiment. Judge/rubric, tool, model or runtime changes require a new comparable baseline. Do not hide per-case regressions behind an improved average or reuse exposed tests as fresh holdouts.
- Keep credentials and private cases out of published repositories. Preserve run/delivery ids, artifact checksums and actual state; do not invent successful execution or recovery.

## Load only the needed reference

**Unchanged Hermes operation:** [control-plane API and result retrieval](references/hermes-control-plane.md), [execution and sandbox](references/hermes-execution.md), [state/recovery](references/hermes-state-and-recovery.md), [capabilities and source map](references/hermes-capabilities-and-limits.md).

**Project changes:** [delivery contract](references/agent-project-delivery.md), [profile design from failures](references/profile-development.md), [evaluation and feedback](references/evals-and-feedback.md), [DSPy Self-Evolution](references/dspy-self-evolution.md).

**Specific architecture decisions:** [agent architecture](references/agent-architecture.md), [context and progressive loading](references/context-and-progressive-disclosure.md), [subagents](references/subagents-and-orchestration.md), [tools and environments](references/tools-environments-and-runtime-boundaries.md), [long-running work](references/long-running-work.md).

**Repository or runtime mapping:** [repository governance](references/repository-governance.md), [structure map](references/harness-spec.md), [review checklist](references/maintenance-checklist.md), [runtime adapters](references/runtime-adapters.md), [Hermes distribution/deployment](references/hermes-distribution-and-deployment.md), [project/Kanban/profile model](references/hermes-team-model.md).
