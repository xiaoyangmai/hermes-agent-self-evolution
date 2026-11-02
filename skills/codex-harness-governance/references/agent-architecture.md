# Choosing an agent architecture

Start with the smallest design that can meet the outcome. Increasing autonomy, orchestration, or persistence adds latency, cost, failure modes, and maintenance work; add complexity only when evidence shows that the simpler design is insufficient.

## Decision sequence

1. **Direct call.** Use one model call with retrieval or a small tool set when the task is bounded and the output is easy to check.
2. **Fixed workflow.** Use a known sequence of model/tool steps when the subtasks and gates are predictable and repeatability matters more than flexibility.
3. **Single agent.** Use a tool-using loop when the number and order of steps depend on what the agent discovers and the environment provides ground truth.
4. **Multiple agents.** Add specialized workers only when independent work can run in parallel, a role needs isolated context, or a generalist would be distracted by unrelated domains.
5. **Evaluator or reviewer.** Add a separate evaluator when the output has clear criteria and an iteration loop can measurably improve it.

## Architecture questions

- What outcome must be true in the environment, not merely stated in the final answer?
- Which steps are fixed enough to encode, and which require model judgment?
- What evidence can the agent inspect after each action?
- Which workstreams are truly independent, and what shared state or handoff is required?
- Where can the agent stop, ask the user, or recover without guessing?
- What is the smallest set of tools and context that allows the task to succeed?

## Guardrails against overdesign

- Do not create a supervisor, router, or subagent for a one-file or sequential task.
- Do not split agents merely to make a diagram look modular; split when the context, tools, ownership, or evaluation boundary is real.
- Keep the agent-computer interface explicit: tool names, arguments, paths, outputs, failure behavior, and examples matter as much as the system prompt.
- Preserve transparency: make plans, delegation, checkpoints, and stopping conditions inspectable.
- Treat the harness and model as one evaluated system. A model result measured without its real tools, context, and loop does not prove the product behavior.

## Source material

- [Anthropic: Building effective AI agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
