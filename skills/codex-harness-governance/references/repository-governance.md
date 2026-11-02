# Repository governance

Treat the repository as the agent system's inspectable source of truth. Keep the entry point short enough to load routinely, and make deeper knowledge discoverable through stable paths.

## Source-of-truth map

- `AGENTS.md`: purpose, layout, commands, conventions, boundaries, and verification map.
- `docs/`: architecture, decisions, contracts, and quality evidence.
- `skills/`: repeatable procedures, each with one job and a discriminating description.
- `agents/`: specialized roles, tool boundaries, and output contracts.
- `harness/`: plans, context, progress, and recovery artifacts for long-running work.
- `evals/`: tasks, graders, outcomes, and regression evidence.
- `adapters/`: runtime-specific mapping and unsupported-feature notes.

These names are conventions, not mandatory folders. Preserve existing project names when they express the same ownership clearly.

## Change discipline

- Add a rule after a real failure, repeated correction, or explicit requirement.
- Prefer links to duplicated prose.
- Version behavior changes through the same review path as code changes.
- Require a concrete acceptance check for changes to routing, tools, subagents, memory, or runtime behavior.
- Keep generated, local, and secret state outside the shared specification.
- Periodically remove stale instructions and merge overlapping documents.

## Review questions

- Can a new agent find the right source of truth from the entry point?
- Is each rule owned by exactly one layer?
- Is the proposed structure proportional to project size and risk?
- Can the intended behavior be observed and tested?
- Can a fresh session resume without relying on hidden conversation history?

## Source material

- [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
- [Codex best practices](https://learn.chatgpt.com/guides/best-practices)
