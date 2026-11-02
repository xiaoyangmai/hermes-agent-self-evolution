# Hermes model and context boundaries

Read this module for profile layout, context files, Skills, memory, or sharing a Hermes agent.

## Profile and home

A Hermes profile is a separate Hermes home. It normally owns `config.yaml`, provider credentials, `SOUL.md`, memories, sessions, Skills, cron data, plugins, gateway state, and `state.db`. `HERMES_HOME` is the authoritative state boundary in the implementation. The working directory is where tools start; it is not the profile home.

Hermes' native implementation may recognize several identity files when discovering a named profile, including a native profile manifest. That is an implementation detail of Hermes profile discovery, not a repository-wide standard; do not add a native file to the neutral harness layout just to make the concepts look portable.

Never run two agents against the same profile home. Automatic memory and session writes can mix their state. If agents need shared knowledge, use a deliberately shared repository artifact or an external memory provider.

Host installs normally keep the real OS-user `HOME`, so Git, SSH, `gh`, npm, cloud CLIs, Claude, and Codex credentials may be visible across profiles. `terminal.home_mode: profile` changes subprocess `HOME` to the profile home, but then those tools need profile-local configuration or links. A profile is therefore an identity/state boundary; the terminal backend and `home_mode` determine execution isolation.

## Project context

Hermes supports project context files with this precedence:

`.hermes.md`/`HERMES.md` → `AGENTS.override.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`.

Only the first matching project context type is used, while `SOUL.md` is loaded separately from `HERMES_HOME`. Inside a Git repository, `AGENTS.md` files are merged from the Git root to the working directory, with deeper files more specific. As the agent enters subdirectories through tool calls, Hermes can discover additional context files just in time.

Startup context is scanned and truncated. Keep it short, put durable detail behind links, and do not treat prompt-injection scanning as a complete review of untrusted repositories.

Implementation anchors:

- `agent/prompt_builder.py` — system-prompt and context assembly;
- `agent/subdirectory_hints.py` — progressive subdirectory discovery;
- `hermes_constants.py` — profile/home resolution.

## Skills

Hermes Skills follow the Agent Skills shape and load progressively:

1. the index exposes name and description;
2. `skill_view(name)` loads `SKILL.md`;
3. linked references, scripts, templates, or assets load only when needed.

The usual profile-local source is `~/.hermes/skills/`. Trusted repositories can provide project-local `.hermes/skills/` or `.agents/skills/`; project Skills take precedence for that repository. External directories, bundled Skills, and hub/tap sources have their own precedence and provenance.

Hermes can create, patch, and delete Skills. `skills.write_approval` can stage writes for review. A Skill created by an agent is therefore a mutable procedure, not automatically a reviewed policy. Review third-party Skill bundles and only copy files explicitly referenced by their `SKILL.md`.

Use the rule of thumb: Skills explain **how** to do a repeatable procedure; memory stores compact **what** facts; project context states durable **rules**. Do not put a long workflow into memory merely because the agent can write memory.

## Memory and sharing

Built-in memory is bounded and profile-scoped. `MEMORY.md` and `USER.md` are injected as a snapshot at session start. Current Hermes documentation exposes configurable character limits (the current documented defaults are approximately 2200 and 1375 characters); verify the installed version before relying on exact numbers. Memory does not silently discard old entries when full: a write can fail until the agent consolidates or removes content.

External memory providers are additive to built-in memory, and only one external provider is active at a time. A local provider or profile memory is not automatically shared with another profile or another machine.

Profile distributions can ship personality, configuration, Skills, cron jobs, and MCP connections. Credentials, memories, sessions, and machine-specific installs remain local. Use the native distribution workflow for Hermes; do not encode it as a cross-runtime profile schema.

## Source map

- Docs: [Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles), [Context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files), [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory), [Profile distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)
- Code: [`hermes_cli/profiles.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_cli/profiles.py), [`agent/prompt_builder.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/prompt_builder.py), [`agent/subdirectory_hints.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/subdirectory_hints.py), [`hermes_constants.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_constants.py)
