# Tools, environments, and runtime boundaries

Design the agent-computer interface as part of the system. A tool should make the desired action easy to express, the result easy to inspect, and failure easy to recover from.

## Tool contract

Document each tool's purpose, exact arguments, path and identifier rules, output shape, side effects, failure modes, freshness, and one valid example. Prefer stable identifiers and explicit paths over ambiguous natural-language references.

Keep tools small and composable. Add a tool only when it exposes evidence or an action the agent cannot reliably perform through existing interfaces.

## Environment contract

Describe the workspace, working directory, available commands, persistent state, network assumptions, and how to start or reset the environment. Distinguish temporary session state from repository-shared artifacts.

An environment can be local, Docker-based, remote, or hosted. The neutral specification should describe capabilities and boundaries, not a particular backend.

## Deterministic controls

Put rules that must never be bypassed in sandbox policy, deny rules, hooks, managed settings, or equivalent runtime controls. Put heuristics and collaboration guidance in `AGENTS.md`, Skills, and prompts. A prose rule is not a hard enforcement mechanism.

## Runtime adapter rule

Keep native configuration in an adapter reference. Map concepts such as identity, skills, subagents, MCP, memory, workspace, sandbox, approval, and session state without pretending that the runtime schemas are interchangeable. The adapter must state what is automatic, what is explicit, and what is unsupported.
