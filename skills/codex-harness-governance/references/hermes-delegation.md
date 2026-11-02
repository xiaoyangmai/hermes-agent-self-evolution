# Hermes delegation and subagents

Read this module for `delegate_task`, parallel work, model routing, isolation, or child lifetime.

## What delegation provides

`delegate_task` starts a child agent with a fresh conversation, its own task identity and terminal session, inherited parent capabilities, and a focused goal/context. The parent normally receives only a final summary. The child does not automatically know the parent's conversation, decisions, or intermediate tool results; pass the necessary context explicitly.

Use delegation when work is independent and parallel, needs a specialist context/tool boundary, would flood the parent context, or requires an independent reviewer. Work directly for small sequential edits or any task that depends on one continuous plan.

## Limits that affect design

- A child inherits the parent's enabled tools; it cannot widen its own tool access through the model-facing call.
- Leaf children cannot delegate again, clarify with the user, write shared persistent memory, send cross-platform messages, or create cron jobs.
- Nested orchestration is opt-in and bounded by `max_spawn_depth`; default behavior is a flat tree.
- Batch width, total child count, child iterations, output schema, and finite-session caps must be checked in the active profile. In the inspected Hermes 0.21.4 path, `delegation.max_iterations` owns the child iteration budget; a model-supplied per-call override is ignored.
- Distinguish a finite CLI session from one HTTP request. Finite CLI consumption (`-Q`, `--oneshot`, or non-TTY) and sessions with no later-result consumer join delegated children. Ordinary `/v1/runs` calls declare resumable server history: they return a background handle, persist child completion for the next client turn, and do not automatically wake the producer. Verify the actual transport/history contract before making artifact assembly depend on a child result. In the inspected top-level dispatch, `background=false` does not force a join. Do not add a continuation service merely to make a proposed reviewer work.
- Background children belong to the parent session. Unfinished processes can be terminated when the owner ends unless the child explicitly hands them off or durable scheduling owns the work.
- Worktree isolation is opt-in, Git-only, and backend-dependent. Without it, parallel children can modify the same checkout.

## Model and profile routing

Basic delegation can route children to a configured provider/model. Advanced delegation plugins can route by model map or by Hermes profile. A profile route may expose that profile's model, credentials, Skills, personality, and terminal policy to the child. Treat this as a deliberate capability and credential boundary; do not list a profile route merely to get a different prompt.

When a child must produce a machine-consumable result, define an output schema and validate the returned artifact. A summary is not proof that the child changed the intended files, ran the intended checks, or completed its background process.

## Source map

- Docs: [Subagent delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation)
- Code: [`tools/delegate_tool.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool.py), [`tools/delegate_tool_config.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_config.py), [`tools/delegate_tool_child_run.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_child_run.py), [`tools/delegate_tool_toolsets.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_toolsets.py), [`tools/delegate_tool_dispatch.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/delegate_tool_dispatch.py), [`gateway/platforms/api_server_runs.py`](https://github.com/NousResearch/hermes-agent/blob/main/gateway/platforms/api_server_runs.py), [`gateway/wake.py`](https://github.com/NousResearch/hermes-agent/blob/main/gateway/wake.py)
