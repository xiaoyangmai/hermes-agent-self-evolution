# Developing a profile from observed behavior

Read this module when creating or improving the instructions, Skills, examples, or context that shape an agent's work. Use [agent-project-delivery.md](agent-project-delivery.md) for publication and result retrieval, and [evals-and-feedback.md](evals-and-feedback.md) for grader calibration and acceptance gates.

A candidate profile is a testable hypothesis. A clearer-looking prompt, a successful deployment, or one attractive artifact does not establish improved production quality.

In Mode B, local Codex owns architecture and experiment design: inspect remote results, identify the responsible asset, research alternatives and define the comparison. When the project uses [DSPy Self-Evolution](dspy-self-evolution.md), that engine owns candidate proposals, search and the executable deployment/evaluation loop. Do not also hand-edit the candidate or schedule competing rounds during search. Hermes owns the inner task loop and bounded self-check. Improving this governance Skill alone does not improve the deployed profile. Mode A remains lightweight.

## Start with a useful outcome and a failure mechanism

Describe the intended user, useful deliverable, inputs, allowed resources, and observable quality requirements in the project's existing task contract. Translate broad goals into decisions the producer must make: for example, which evidence supports an answer, which changed condition requires a different action, or which part of an artifact the recipient must be able to use. Keep this compact; a new profile schema is unnecessary.

Before adding instructions, inspect the relevant trace and actual artifact. Record the smallest evidence that explains the problem: the task condition, observed decision, tool result or artifact excerpt, and its consequence. Separate observed facts from the proposed explanation.

For a decisive artifact defect, distinguish whether the instructions requested the correct behavior, the tool output violated it, the observer detected it, and the producer acted on the observation. Choose the owning layer before changing a profile. Inspect independently observed evidence first, then use the trace and prior hypotheses to test plausible causes rather than treating correlation as proof.

| Observed problem | First place to investigate |
| --- | --- |
| Instructions were absent, stale, or not loaded | Packaging, deployment, discovery, and context loading |
| A required tool is unavailable or rejected | Effective runtime configuration and tool permissions |
| The producer loaded the intended instructions but made the wrong decision | Role fit, procedure, domain knowledge, task facts, or tool/model capability |
| The artifact is useful but the result cannot be retrieved | Delivery contract and artifact handoff |
| Graders disagree about the same evidence or reward extra length | Rubric, calibration examples, and evaluator input |

## Reflect on the design after each result

Use this reflection to decide the next profile experiment, including after a technically successful delivery with weak quality. Keep the reasoning in the existing experiment note; no new manifest, framework, or agent is required.

1. **Recover the evidence.** Read the task and acceptance criteria, effective deployed resources, relevant trace decisions, retrieved artifact, and independent evaluation together. Locate the actual defect and its consequence. Separate a missing capability or wrong decision from a delivery failure, a misleading self-check, or a grader defect. A score or the producer's explanation alone does not identify the cause.
2. **Compare plausible causes.** State the leading explanation and credible alternatives supported by the evidence. For example, copying an earlier answer could reflect an unclear procedure, missing domain knowledge, or an unsuitable task decomposition. When those imply different changes, run the smallest diagnostic that can disprove one: inspect loaded instructions, test a decision in isolation, or provide a relevant fact and see whether the decision changes. Keep this probe separate from scored production trials.
3. **Look outside the current design.** Proactively search the web when a method, domain concept, tool, or capability is missing or unclear, and when the same failure survives an instruction change. Search the concrete failure mechanism and possible approaches; do not limit the search to better prompt wording. Prefer primary documentation, research, and maintained source code. Record useful links, the mechanism they suggest, and current compatibility with the target runtime, version, and available tools. A judgment probe and an integration probe establish different things: test a chosen tool's actual entrypoint, input/output and state effects in the target environment before relying on it; documentation or `--help` alone is not execution evidence. Treat external ideas as hypotheses to test, not instructions to obey. Research does not itself authorize installing tools, granting access, or spending beyond the approved scope.
4. **Choose the smallest justified change.** Compare likely benefit, evidence, cost, and the diagnostic result across method/procedure, examples or domain references, context and task inputs, tools or project scripts, model/configuration, role boundaries, and work sequence. Change the actual asset that owns the failure. A reviewer or another agent is an option only when a probe shows the missing judgment can be supplied and the extra coordination is worthwhile; it is not the default response to low scores. If runtime or grading is at fault, repair that separately before claiming profile improvement.
5. **Make the prediction reviewable.** Record **evidence → competing causes → diagnostic/research finding → selected asset and edit → predicted observable behavior → verification case and regressions**. Explain why this option was chosen and what result would disprove it. Choose one behavior family per candidate. Remove superseded wording; do not attach a new permanent rule to every isolated mistake or encode acceptance answers into the profile.
6. **Close the loop with the next result.** Publish and verify the authored resources, execute on the target runtime, collect traces and final artifacts, and apply the unchanged comparison rules. Check whether the predicted decision actually changed, whether user-facing quality improved, and what regressed or cost more. Preserve failed hypotheses. If the same failure remains, revisit the cause and research alternatives instead of merely intensifying the same instruction. A justified no-change or rejected candidate is a valid experiment outcome, but not evidence that the user's goal is complete.

Keep stopping scopes distinct: a task's self-repair allowance limits that agent run; an adoption gate can reject one candidate; the user's iteration count, total project budget, achieved goal, or demonstrated blocker determines the outer loop. Continue authorized iterations with a new evidence-backed hypothesis after a candidate fails, within the agreed budget. Do not silently end the project because one comparison rejected an idea, or extend experiments indefinitely to obtain a passing score.

## Author the decision procedure

Codex authors repository-owned profile resources and project evaluation contracts. An authorized optimizer may edit the declared asset within a frozen experiment; its exported candidate must be the actual resource deployed and used. The deployed agent executes tasks with that version. Keep independent evaluation outside the producer's self-check and optimizer instructions, and use the target runtime for behavioral evidence.

Place each change with its owner: role boundaries in the profile, reusable steps in the relevant Skill, stable facts in project context, and enforceable tool restrictions in native runtime configuration. Remove conflicting or superseded wording instead of accumulating instructions.

For a recurring reasoning error, prefer a short decision procedure supported by a contrasting example over another abstract demand to be careful:

1. Identify the decision and the facts available for making it.
2. Show one plausible failure and one acceptable response to a comparable situation.
3. Explain the decisive difference in observable terms.
4. Show how that distinction applies when a relevant condition changes.

Examples should teach the mechanism and its limits. They should not encode the answers, names, or layouts of the acceptance cases. Keep examples separate from fresh evaluation cases, vary incidental details, and include an adjacent counterexample where useful. More examples are justified when they resolve a demonstrated ambiguity, not merely because space is available.

### Illustrative contrast: applying a rule

Suppose an educational artifact teaches a child to read the current sorting rule. In its story, a basket says “round,” so a child places a red ball inside.

- **Recall only:** “Which object did the child put in the basket?” The story already supplies the answer; changing the child's name does not add a decision.
- **A new application:** The question explicitly changes the basket label to “blue” and offers a blue block and a red ball. Choosing the blue block applies the target principle to a new condition. Choosing the red ball is a plausible attempt to repeat the story's action.
- **An unsupported premise:** The explanation cannot say that an undescribed object is blue. The facts needed to choose must appear in the story or question.

This is an illustrative authoring example, not an evaluation case or a universal educational template. The procedure still has to preserve age-appropriate wording, factual consistency, and usable output. Adding complexity can damage those requirements.

## Add a bounded producer self-check

Ask the producer to check the few decisions most likely to fail before packaging the result. For the example above, it can identify the new condition, the supporting sentence, and the reason each plausible alternative is incomplete. If those cannot be identified from the artifact, repair that item within the task budget.

Use a short, explicit repair allowance appropriate to the task. Do not instruct the agent to keep revising until it believes its score is high enough. Preserve the normal terminal failure or limitation report when the budget is exhausted. A producer self-check can prevent defects; it is not an independent acceptance score and does not replace external artifact inspection.

When repeated low-level output assembly consumes effort or introduces regressions, consider one maintained project/Skill template or script for that repeated work, leaving the agent to author the meaningful variable content. Verify the template's actual user flow. This is appropriate for repeated delivery, not a reason to extract one-off helpers or build another runtime. Freeze the template during a Skill-body experiment so its benefits are not misattributed to prompt search.

## Develop, freeze, then evaluate

Use small development cases to inspect whether the intended mechanism appears in the deployed trace and artifacts. Examine regressions and cost as well as the target score. If the new procedure is not being followed, diagnose loading or clarity before making the process longer. Bound the number of development revisions before starting; an unpromising candidate can be abandoned.

Keep three purposes distinct using the repository's existing files:

- **Development cases:** visible examples and failures used to design or revise the profile.
- **Regression cases:** previously observed behavior that must remain acceptable.
- **Held-out cases:** representative tasks whose outputs and labels have not been used to select or edit this candidate.

A small project can use a small collection. These are roles for cases, not three mandatory datasets or a required directory layout. A narrow repair may need only regression or smoke evidence; use reserved cases when the intended quality or generalization claim warrants them. Keep evaluator packets and private labels outside the producer's accessible task context where practical. A “do not read” instruction alone does not establish isolation when repository or workspace access exposes them.

Freeze the selected profile revision, task inputs, runtime conditions, rubric, acceptance gates, and stopping policy before the adoption comparison. Recheck the baseline if runtime configuration changed during development; compare both versions under the same conditions. Run the actual deployment, execution, trace, and artifact retrieval loop described in [agent-project-delivery.md](agent-project-delivery.md).

Use the calibrated independent evaluation and repeated comparisons in [evals-and-feedback.md](evals-and-feedback.md). Preserve unsuccessful deliveries and grader disagreement. Report whether the candidate improves the target behavior without unacceptable regressions, whether the evidence supports adoption, and what remains uncertain.

Once held-out results inform a further edit, those cases become development or regression evidence for the next candidate. Do not describe repeated tuning against them as fresh generalization. When adoption gates fail, retain or restore the previous deployed version and record its known defects; a comparison baseline is not necessarily an accepted product.

