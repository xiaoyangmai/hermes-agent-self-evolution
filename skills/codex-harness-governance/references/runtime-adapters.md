# Runtime adapters

The neutral governance rules describe concepts, not vendor schemas. Use this reference only when the task needs a mapping to a concrete runtime.

When the target is Hermes Agent, read [hermes-capabilities-and-limits.md](hermes-capabilities-and-limits.md) before proposing a profile, Skill layout, sandbox contract, delegation policy, or long-running workflow. It contains the current capability/limitation map and the documentation/source paths to verify against.

## Adapter contents

For each runtime, record:

- where the runtime discovers durable instructions and Skills;
- how it defines profiles, agents, subagents, tools, MCP, memory, and sessions;
- what is automatically loaded versus explicitly selected;
- how workspaces, sandboxes, approvals, and hooks are enforced;
- which repository artifacts are shared and which are local;
- how authored runtime artifacts are packaged, released, updated, and rolled back;
- unsupported concepts and migration constraints.

## Hermes example boundary

Hermes-native profile state, memory, sessions, and Skills belong to the Hermes adapter. Repository governance should describe the desired role, context, tools, persistence, and acceptance behavior without inventing a cross-runtime profile manifest.

## Codex and Claude example boundary

Codex and Claude may discover different instruction files, Skills, subagent definitions, configuration layers, and runtime controls. Keep those mappings in adapter notes and validate them against the installed version. Do not assume that a native profile selected in one runtime is automatically selected in another.

## Official runtime references

- [Hermes profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles)
- [Hermes profile distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)
- [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Codex skills](https://developers.openai.com/api/docs/guides/tools-skills)
- [Claude Code memory](https://code.claude.com/docs/en/memory)
