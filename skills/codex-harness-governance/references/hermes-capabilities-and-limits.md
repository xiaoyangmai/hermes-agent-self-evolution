# Hermes capabilities and limits

Read this file when the target system runs on Hermes Agent. It is a router and verification guide; load only the Hermes module that matches the current decision.

Hermes changes quickly. Treat the installed version, current official docs, current checkout, and a narrow runtime probe as stronger evidence than this summary.

## Hermes decision map

| Decision | Read next |
|---|---|
| Profile, `HERMES_HOME`, project context, Skills, memory, or distribution | [hermes-model-and-context.md](hermes-model-and-context.md) |
| Profile distribution, release, remote update, or rollback | [hermes-distribution-and-deployment.md](hermes-distribution-and-deployment.md) |
| Remote Hermes control service, project registration, async operations, or gateway refresh | [hermes-control-plane.md](hermes-control-plane.md) |
| Git project, Hermes project, Kanban board, profile roles, or task worktrees | [hermes-team-model.md](hermes-team-model.md) |
| `delegate_task`, subagents, model routing, worktrees, or child lifetime | [hermes-delegation.md](hermes-delegation.md) |
| Tools, `execute_code`, terminal backends, Docker, browser, Windows, or sandboxing | [hermes-execution.md](hermes-execution.md) |
| Sessions, prompt refresh, compression, checkpoints, cron, or restart/recovery | [hermes-state-and-recovery.md](hermes-state-and-recovery.md) |
| MCP, plugins, Tool Search, Skill installation, or source-code verification | [hermes-extension-map.md](hermes-extension-map.md) |

## Non-negotiable distinctions

- A Hermes profile is a persistent identity/state home, not a sandbox.
- `HERMES_HOME`, the working directory, and the subprocess `HOME` are different boundaries.
- Skills are on-demand procedures; memory is compact durable facts; project context is instructions; sessions are history and state. Do not merge them into one large prompt or one universal manifest.
- A child agent receives a fresh conversation and normally returns only a summary. It is not a continuation of the parent conversation.
- A container backend changes the execution environment, but persistence, mounts, checkpoints, and live-process recovery still depend on the backend.
- Installing a plugin, MCP catalog entry, or third-party Skill can execute code. Review the source and bootstrap path before enabling it.

## Verification order

When an implementation claim matters:

1. Read the matching page in the [Hermes documentation](https://hermes-agent.nousresearch.com/docs).
2. Inspect the matching file in the current Hermes checkout under `website/docs/`.
3. Inspect the implementation and tests named by the module.
4. Run a narrow check such as `hermes --help`, `hermes status`, `hermes doctor`, `hermes tools`, `hermes skills list`, or `hermes profile list`.
5. Record the Hermes version/commit, profile, backend, workspace, and observed result.

Do not infer behavior from a copied profile, an old post, or an unrelated fork. The source of truth is the official [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) repository.

## Runtime-neutral rule

Hermes-native files belong in the Hermes adapter. They may describe a role, model, Skills, tools, memory, workspace, schedule, and delivery behavior, but they must not become a cross-runtime repository schema. In particular, a native Hermes identity file that the implementation happens to recognize is not a requirement for every project or runtime.

## Primary references

- [Hermes documentation](https://hermes-agent.nousresearch.com/docs)
- [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Hermes context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)
- [Hermes configuration and terminal backends](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)
- [Hermes source repository](https://github.com/NousResearch/hermes-agent)
