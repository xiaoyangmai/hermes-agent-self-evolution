# Runtime-neutral harness shape

This is a design map, not a required directory tree and not a runtime schema. Add only the parts that the project actually needs.

```text
agent-system/
├── AGENTS.md                         # short entry point and verification map
├── docs/                             # durable architecture and operating knowledge
│   ├── architecture/                 # boundaries, ownership, dependency rules
│   ├── decisions/                    # accepted decisions and trade-offs
│   └── quality/                      # known gaps, evidence, and follow-ups
├── skills/                           # reusable procedures, one job per Skill
│   └── <skill-name>/SKILL.md
├── agents/                           # optional specialized subagent definitions
│   └── <agent-name>.md
├── tools/                            # optional tool contracts and setup notes
├── harness/                          # optional plans, context, progress, and logs
│   ├── plans/
│   ├── context/
│   └── progress.md
├── evals/                            # tasks, graders, expected outcomes, reports
└── adapters/                         # optional runtime mapping; never the core spec
    └── <runtime>.md
```

Use these ownership rules:

- `AGENTS.md` is a short map: purpose, commands, important paths, constraints, and where the deeper source of truth lives.
- `docs/` holds durable knowledge that agents need to discover but should not receive in full on every task.
- `skills/` holds repeatable methods with explicit inputs, outputs, and trigger boundaries.
- `agents/` holds specialized roles and their tool/context boundaries; do not use it as a second policy store.
- `tools/` documents interfaces, examples, failure behavior, and freshness expectations. Credentials remain outside the repository.
- `harness/` holds task-specific plans, decisions, progress, and recovery notes for work that spans sessions.
- `evals/` makes behavior observable through tasks, trials, graders, outcomes, and regression evidence.
- `adapters/` maps a runtime's native concepts to this repository's neutral concepts. It does not redefine the neutral concepts.

Do not create a universal profile manifest. If Hermes, Codex, Claude, or another runtime needs a native profile file, keep it in that runtime's adapter and validate it against that runtime's documentation.
