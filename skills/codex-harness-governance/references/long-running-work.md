# Long-running work and handoff

Long tasks should be designed as a sequence of recoverable increments. A fresh session must be able to understand the current state without reconstructing the entire transcript.

## Minimum durable state

- the approved outcome and non-goals;
- the current phase and one next step;
- acceptance checks and their observed status;
- material decisions, constraints, and unresolved questions;
- commands or environment setup needed to continue;
- the last clean state and any known recovery action.

Use a repository-local plan, progress log, context note, or equivalent only when the task benefits from persistence. Do not create all of these files by default.

## Session protocol

1. Initialize the environment and verify the baseline.
2. Select one bounded feature or phase.
3. Read the relevant plan, context, source files, and prior evidence.
4. Make the smallest coherent change.
5. Run focused checks and record the actual result.
6. Leave the workspace in a clean, resumable state with a next step.

Avoid one-shot implementation of an entire open-ended product. If a phase cannot be completed cleanly, record the partial state and recovery instructions rather than declaring success.

## Source material

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
- [OpenAI: Iterating development workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)
