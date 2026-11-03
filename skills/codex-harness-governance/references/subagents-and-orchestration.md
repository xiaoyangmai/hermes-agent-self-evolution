# Subagents and orchestration

Subagents are a context and ownership tool, not a default sign of a sophisticated system.

For Codex-led product acceptance, candidate comparison or claims of quality improvement, delegate an independent assessment without inheriting the development conversation. Give the evaluator the user goal, frozen rubric, anonymized actual artifact, and necessary interaction evidence; omit author explanations, candidate identities, previous scores, and optimization hypotheses. A fresh conversation still inherits system instructions and may access shared files: constrain the evidence packet and record any exposure. If delegation is unavailable, report that limitation rather than claiming a blind review. Existing independent project evaluators need not be duplicated by a Codex subagent for every sample.

For diagnosis, ask for observations before supplying candidate history or trace interpretations, then provide the relevant raw trace for causal analysis. Independent research or rubric review can also be delegated without the parent's favored conclusion. In contrast, retain baseline, exposed cases, prior failures, receipts and consumed budget in the orchestrator; a fresh evaluator must not reset experiment history. Summarize independently obtained findings only after each assessment has finished.

## Use a subagent when

- the work can run independently and in parallel;
- a specialist needs a distinct tool set or domain context;
- exploration would otherwise flood the main agent's context;
- a reviewer or evaluator should be independent from the producer;
- the orchestrator cannot predict the needed subtasks in advance.

## Work directly when

- the task is small, sequential, or limited to one file;
- each step depends on the previous step's shared context;
- delegation would add more handoff text than useful work;
- the agent must maintain one coherent plan through consecutive edits.

## Define each role

Every subagent should have a purpose, trigger/assignment rule, allowed tools, context inputs, expected output, stopping condition, and escalation path. Limit the role's tools and write output contracts that another agent can consume without guessing.

## Orchestration patterns

- **Sequential:** use when each stage depends on the prior stage and a gate can reject bad intermediate state.
- **Parallel sectioning:** use for independent research, file groups, or separate review dimensions; aggregate results explicitly.
- **Routing:** classify first when distinct task categories need different tools or instructions.
- **Orchestrator-workers:** use when the necessary subtasks depend on what discovery reveals; require a clear synthesis step.
- **Evaluator-optimizer:** use when criteria are explicit and feedback can improve the output measurably.

Keep delegation visible in plans or traces. Add budgets, maximum turns, failure handling, and a rule for returning to the parent when the subtask is blocked.

## Source material

- [Anthropic: Building effective AI agents](https://www.anthropic.com/research/building-effective-agents)
- [Claude Code: Subagents](https://code.claude.com/docs/en/sub-agents)
