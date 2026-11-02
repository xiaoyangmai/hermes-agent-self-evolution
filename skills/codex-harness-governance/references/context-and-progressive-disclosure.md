# Context, memory, and progressive disclosure

Treat context as a finite attention budget. The goal is the smallest high-signal set of instructions, state, evidence, and references that lets the agent make the next correct decision.

## Layering

- **Entry point:** a short `AGENTS.md` or equivalent map with purpose, commands, boundaries, and links.
- **Durable knowledge:** architecture, decisions, contracts, and quality notes in discoverable repository files.
- **Reusable procedure:** a Skill with a narrow trigger, main workflow, and explicit inputs/outputs.
- **Specialized role:** a subagent definition with its own tool and context boundary.
- **Working state:** current plan, progress, unresolved questions, and next step for one task or phase.
- **Runtime controls:** sandbox, permissions, hooks, deny rules, and other deterministic enforcement.

Do not put all of these in one large instruction file. A short map should tell the agent where to look next.

## Loading policy

1. Load the entry point and the task-specific path context.
2. Identify the current decision or phase.
3. Read only the linked reference needed for that decision.
4. Load detailed examples, schemas, or logs just in time.
5. Summarize durable discoveries into the appropriate artifact; do not preserve every transcript.

## Memory rules

- Memory records durable facts, decisions, preferences, and unresolved questions; it is not a second policy file.
- Keep an index or summary small enough to load routinely; keep topic files for details.
- Separate repository-shared memory from runtime-local memory. Do not assume a local runtime memory is portable.
- Record provenance and freshness when a fact can go stale.
- Promote a repeated correction into the right source of truth only after confirming it is a durable rule.

## Context failure signals

Reduce or restructure context when the agent ignores important rules, repeats discovery, reads large irrelevant files, contradicts itself, or spends more time navigating instructions than doing the task. Fix the layer or retrieval path before adding more prose.

## Source material

- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)
- [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
- [OpenAI: Skills](https://developers.openai.com/api/docs/guides/tools-skills)
