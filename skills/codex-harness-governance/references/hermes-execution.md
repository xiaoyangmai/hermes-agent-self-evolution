# Hermes execution, tools, and sandbox boundaries

Read this module for tool contracts, code execution, terminal backends, browser automation, Windows support, or sandbox claims.

## Tool surface

Hermes uses a registry-driven tool surface covering files, terminal commands, web search, browser automation, memory, delegation, cron, code execution, and plugins. Toolsets can be enabled or disabled per surface. A tool being visible does not mean an action is authorized; approval settings, environment policy, provider configuration, and the backend still apply.

`execute_code` lets the model write a Python script that calls Hermes tools through RPC. Only the script's printed output returns to the model, so it is useful for filtering large intermediate results and reducing context growth. Use `terminal` for ordinary commands, builds, tests, and background processes. Verify the active execution mode and its limits before relying on API keys, nested tool calls, or long-running processes.

## Terminal backends

Hermes supports local, Docker, SSH, Modal, Daytona, Vercel Sandbox, and a Singularity/Apptainer plugin:

- `local`: direct host execution with no filesystem isolation;
- `docker`: hardened container, commonly persistent and shared by sessions/subagents according to mount settings;
- `ssh`: remote execution with remote credentials and policy;
- `modal`, `daytona`, `vercel_sandbox`: cloud execution with configurable filesystem persistence, but snapshots do not preserve live processes or PID space;
- `singularity`: plugin-provided container execution for HPC/shared hosts.

The workspace mount, `terminal.cwd`, container persistence, and subprocess `HOME` must be stated separately. A profile name or a selected working directory does not, by itself, create a new sandbox.

## Approval and security boundary

Hermes combines dangerous-command approval, file-write controls, tool allow/deny settings, container isolation, MCP credential filtering, context-file scanning, session isolation, and working-directory validation. Local execution is still host execution. Container backends may skip host dangerous-command checks because the container is the intended boundary; confirm the backend and mount before calling a change safe.

## Browser and Windows

Browser automation normally uses Hermes' packaged headless Chromium through CDP-based tools. Reproducibility depends on the browser provider, session lifecycle, credentials, and profile state. A browser capability is not the same as a visible desktop-control capability.

Native Windows supports the core CLI/TUI/gateway/cron/browser/MCP paths, but optional dependencies and shell behavior can differ from Linux/macOS. Inspect the active shell/backend and use Docker or WSL2 when the task requires a POSIX-like or isolated environment.

## Source map

- Docs: [Tools and toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools), [Code execution](https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution), [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration), [Browser](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser), [Security](https://hermes-agent.nousresearch.com/docs/user-guide/security), [Windows](https://hermes-agent.nousresearch.com/docs/user-guide/windows-native)
- Code: [`tools/registry.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/registry.py), [`model_tools.py`](https://github.com/NousResearch/hermes-agent/blob/main/model_tools.py), [`toolsets.py`](https://github.com/NousResearch/hermes-agent/blob/main/toolsets.py), [`tools/terminal_tool.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/terminal_tool.py), [`tools/environments/`](https://github.com/NousResearch/hermes-agent/tree/main/tools/environments), [`tools/browser_session_lifecycle.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/browser_session_lifecycle.py)
