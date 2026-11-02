# Hermes extensions and source-reading map

Read this module for MCP, plugins, Tool Search, Skill installation, or when a documented behavior must be checked in the Hermes source.

## MCP and plugins

MCP connects Hermes to external tool servers. Catalog entries can run clone, bootstrap, dependency-install, and transport commands; inspect the manifest and source repository before enabling one. A project-local plugin directory is not automatically equivalent to a profile-installed and enabled plugin.

Plugins can extend tools, hooks, slash commands, CLI commands, MCP, context engines, terminal backends, delegation providers, and memory providers. Treat an extension point as a runtime capability, not as a reason to add a second runtime to the repository.

Tool Search and delayed tool loading can reduce schema pressure, but core tools, Skills, MCP servers, and plugin availability still depend on configuration and the current session. Verify what the model actually sees with the runtime's status/help surfaces.

## Skill installation and provenance

Hermes can install Skills from the local profile, project directories, external directories, GitHub taps, URLs, and the Skills Hub. Only files explicitly referenced by a Skill manifest are intended to be copied for remote installs. Record source, revision/hash, platform requirements, and approval state for shared Skills. A Skill that can self-modify should be governed like code: review the diff, run a representative task, and keep an easy rollback path.

## Source-reading route

When docs and observed behavior disagree, read the current checkout in this order:

1. `website/docs/` page for the user-facing contract;
2. `AGENTS.md` in the relevant source directory;
3. the entry point (`run_agent.py`, CLI, gateway, or tool module);
4. the state/config helper that owns the boundary;
5. focused tests and regression fixtures;
6. a narrow runtime probe.

Useful source areas:

- `run_agent.py`, `agent/prompt_builder.py`, `agent/system_prompt.py` — agent loop and prompt assembly;
- `agent/context_engine.py`, `agent/context_compressor.py` — context and compaction;
- `hermes_cli/main.py`, `hermes_cli/profiles.py`, `hermes_constants.py` — startup and profile resolution;
- `model_tools.py`, `toolsets.py`, `tools/registry.py` — tool discovery and dispatch;
- `tools/delegate_tool.py` and `tools/delegate_tool_*` — child lifecycle and routing;
- `tools/environments/` — terminal backend implementations;
- `tools/mcp_tool_*.py`, `plugins/`, `optional-mcps/`, `skills/`, `optional-skills/` — extensions and distribution;
- `hermes_state*.py`, `gateway/`, `cron/` — persistence and long-running surfaces.

## Primary references

- [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
- [Plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins)
- [Tool Search](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search)
- [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Hermes source](https://github.com/NousResearch/hermes-agent)
- [Terminal provider plugin guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/terminal-environment-plugin.md)
- [Skills source guidance](https://github.com/NousResearch/hermes-agent/blob/main/skills/AGENTS.md)
