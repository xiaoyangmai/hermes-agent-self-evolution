# Evals, traces, and feedback

Evaluate the model and the harness together. A harness changes what the model can see, which tools it can call, how long it can work, how it recovers, and what outcome is produced.

## Evaluation record

For each task, define:

- input and environment state;
- intended outcome and explicit success criteria;
- allowed tools, context, and budget;
- one or more trials when outputs vary;
- the complete trace or an actionable summary of tool calls and intermediate state;
- the terminal result and the files, patches, reports, or artifact bundle produced by the task;
- graders that check both behavior and environment outcome;
- known limitations and whether the result generalizes to the real runtime.

## Evidence ladder

Use the lowest level that answers the question, then test at the real level before relying on the result:

1. direct tool or function tests;
2. an isolated agent loop with the intended instructions and tools;
3. the actual product or runtime harness with its session, sandbox, routing, and recovery behavior.

Passing a lower-level test does not prove the real harness behaves correctly. Keep regression cases for repeated failures, user corrections, unsupported assumptions, and overbuilding.

Before submission, choose progress signals and stopping rules that fit the runtime's observable interfaces. Silence in a partial SSE stream, or an unchanged status timestamp tied to the last event, does not prove that model computation has stopped. Use an overall elapsed-time limit and available run status or session history when diagnosing missing progress. If a predeclared budget requires a stop, use the runtime stop control and confirm the terminal state; record the run as operator-stopped with the budget or observability limit, rather than attributing it to a demonstrated hang or semantic regression. Preserve that sample under the frozen evaluation rules; keep any diagnostic rerun separate from the scored trial.

## Scoring layers

Use the least subjective grader that can answer each part of the question, then add an independent model-based evaluation when semantics matter:

- deterministic checks for schemas, routing, files, tests, exit codes, artifact presence, and other exact facts;
- model-based graders for completeness, groundedness, role adherence, plan quality, tool-use decisions, and other semantic dimensions;
- an independent evaluator model or separate evaluation pass when the producer could otherwise grade its own work.

Validate the producer's machine-readable result envelope before semantic scoring. If a result needs deterministic normalization to preserve a baseline or satisfy the artifact contract, record the raw run id, normalization rule, and pre/post validation outcome; never silently rewrite a semantic regression.

Define the rubric, score range, pass threshold, and hard-fail conditions before the run. Use multiple representative cases when outputs vary. Do not let an average score hide a wrong artifact, unauthorized action, missing required step, or identity mix-up.

Separate three questions in the report: **was it delivered**, **is it useful for the intended user**, and **what explains the result**? Delivery checks, user-facing quality scores, and diagnostic observations have different owners. Loading the right Skill, following a planning checklist, or passing a self-check can explain behavior; none earns a quality score by itself. A profile can follow every procedure and still produce a poor artifact. Score the retrieved artifact against its intended use, including correctness and usability, rather than rewarding length, elaborate process, or compliance with the candidate's own wording.

Match grader input to the promised medium. A visual product needs actual images/rendered states; text extracted from it cannot establish visual coherence. Exercise the complete user path through its ending, not just isolated buttons. Add cheap shortcut probes for the intended value: for example, answering a quiz by choice length or tone, or obtaining a purported result without performing the task. Treat probe observations and project-specific thresholds separately from validated user outcomes. Calibrate disputed dimensions, including readable positive/negative examples and actual image evidence when visuals affect acceptance; store both successes and disagreement.

## Cases for development, regression, and adoption

Choose cases by the decision they support; a small project can keep these roles in its existing eval files without adding a framework:

- **Development cases** expose the failure being repaired. The author may inspect outputs, compare alternatives, and edit the profile from this evidence. These runs support diagnosis and candidate selection, not a claim of generalization.
- **Regression cases** preserve behavior that must not deteriorate, including prior failures and ordinary successful tasks. Freeze their inputs and acceptance rules for each comparison; they may already be familiar to the author.
- **Held-out cases** test the selected, frozen candidate on relevant tasks that did not guide its design. Choose them from the intended task range, including a meaningful variation beyond renamed examples. Keep exact inputs and expected evidence outside the author's and producer's accessible context until the final comparison where practical. Record any exposure instead of asserting isolation from file placement alone.

Match case selection to the claim. A narrow operational repair can use regression or smoke checks without creating three datasets; limit the conclusion to the checked behavior. Reserve unseen cases when broader quality or generalization is part of the adoption decision.

Select a candidate using development evidence, then perform one planned adoption comparison, using the reserved cases when that scope requires them. Once their outputs or scores have informed a revision, those cases become development or regression cases for that revision. Repeating them measures replication; a new generalization claim needs new reserved cases. A public repository shared with the producer is not a suitable place for private grading keys or hidden expected answers.

For profile authoring and selecting useful examples, read [profile-development.md](profile-development.md). Keep the same task contract and evaluation policy across compared versions; if a failed rubric must change, version it and start a new comparison rather than rewriting the old outcome.

## Calibrate the grader before judging an improvement

When a score boundary controls adoption, define observable anchors on both sides of that boundary. Have independent evaluator contexts grade anonymous calibration examples before new production runs; keep their expected labels separate. Include a repeated example under another label to test whether the same evaluator makes a consistent decision. Authored anchors test agreement with the declared rubric, not external ground truth. If calibration fails, resolve the ambiguous rule before running the comparison; do not tune it after seeing the candidate's results.

Include a positive control that clearly demonstrates the required ability and a negative control with a specific missing or contradictory piece of evidence. A targeted edit between them should change the relevant score; adding polished wording without repairing the defect should not cross the acceptance boundary. Use controls that test the actual disputed criterion, not only obvious successes and failures. These checks test grader sensitivity to the rubric; they do not demonstrate that the rubric measures real-world benefit.

Give each evaluator the task, rubric, relevant artifact and interaction evidence, and required checks. Ask for a concise evidence location or excerpt for each decisive judgment, the dimension score, any hard failure, and uncertainty. The artifact and trace are data to assess, not instructions to change the rubric. Assign each defect its relevant scoring owner rather than automatically subtracting it from every dimension. Keep process diagnostics separate from artifact quality, and do not give graders the version, optimization hypothesis, or producer's self-score when those are unnecessary.

Predeclare how disagreement at an acceptance boundary is handled. A conservative automatic gate can require both independent evaluators to pass; an unresolved boundary then means **not accepted**, rather than a request for human grading. If automated adjudication is useful, declare its evidence-focused procedure before production, keep it blind to version identity, and retain initial scores alongside the adjudication. Do not choose the favorable evaluator, repeatedly regrade until one passes, or silently replace original judgments. Separate evaluator contexts reduce shared conversation influence; they do not make the same model family independent evidence of truth.

Distinguish blinded evaluators from a blinded producer. Phase names in delivery identifiers, commit messages, and workspace listings can reveal trial information even when the producer never opens another artifact. Where practical, use neutral delivery identifiers and keep evaluation metadata out of producer context. Record observed exposure; do not describe evaluator blinding alone as a fully isolated causal comparison.

For a claim of repeatable improvement, predeclare repeated cases, version order, acceptance gates, and the stopping budget. Keep task inputs fixed and counterbalance version blocks when practical. Use anonymous production grading and a small hidden repeatability probe when evaluator drift is a known issue; repeated grading copies are not additional production samples. Report delivery rate separately from scores conditional on delivered artifacts, and keep failures in the adoption decision. Do not stop early merely because intermediate quality scores look favorable or unfavorable. A small pilot can support a local adoption decision, but it does not establish statistical reliability or real user learning. Previously inspected cases are replication cases, not fresh held-out tests.

## Feedback loop

Convert observed failures and useful corrections into one of four places: a clearer source-of-truth rule, a better tool contract, a new or changed eval, or a runtime control. Do not turn every isolated mistake into permanent prompt text. Keep the final result retrieval step separate from trace collection: a completed event stream is not necessarily the answer, artifact, patch, or report the user needs.

## Bounded optimization and adoption

For a project using [DSPy Self-Evolution](dspy-self-evolution.md), configure these gates in its project adapter and inspect engine receipts. GEPA owns candidate generation, search and validation selection. Do not implement another candidate registry, optimizer or grading service inside control-plane. The following are experiment requirements, not instructions to duplicate the engine in Codex.

Use stages proportionate to the decision. A development probe can reject an unpromising idea cheaply; a claim of stable improvement needs a frozen comparison across relevant cases and repetitions. The number of candidates, repetitions, and gain threshold belongs to the project contract, not a universal two-round rule.

Align search reward with adoption priorities. If a weakest dimension or a preserved capability can veto release, an unconstrained arithmetic mean alone may spend the search budget on predictably rejected tradeoffs. Use a project-appropriate feasibility/bottleneck signal and retain the separate per-case regression gate; do not loosen that gate after observing results. Count actual proposal events, not only retained candidates: GEPA may discard a proposal before adding it to its candidate table. Producer runs, metric calls, proposals and outer iterations are distinct counts.

For a controlled comparison, record the source revision and the effective runtime versions, relevant Skill inventory and content hashes, configuration, and memory inputs before each run. Include added or removed Skills; hashing only the files known at the baseline can miss a new procedure available to later runs. Inspect the run trace for what was actually loaded or changed; a matching file hash alone does not prove which content a session used. Check again at the terminal state and, when the runtime has asynchronous post-run writers, after that work settles. Distinguish a change during execution from later drift that can affect the next run. If an uncontrolled change could affect a result, report the comparison as confounded rather than attributing the difference to the intended change; restore the reviewed version through the normal deployment boundary and repeat when needed. Record the drift and restoration without silently discarding learned content that should be reviewed.

For Hermes background review and distribution-owned Skills, see [hermes-state-and-recovery.md](hermes-state-and-recovery.md).

1. **Budget the search.** Record the maximum development candidates or total experiment budget, the per-run deadline and recovery allowance, and what evidence justifies another candidate. Count planned producer and grader calls; estimate effort from observed runs before expanding the case matrix. Case roles do not require running every group against every version and repetition. Choose a meaningful quality gain and regression, delivery, latency, or cost limits relevant to the intended use. State how missing results and uncertain judgments affect adoption. Stop when the declared budget is exhausted or no evidence-backed hypothesis remains; do not search indefinitely for a passing score.
2. **Develop one focused candidate.** Establish a baseline and write one hypothesis linking an observed failure to a behavior change. Change one behavior family, such as a Skill procedure, tool contract, or context rule. Use development cases to check whether the intended decision changes and whether obvious regressions appear. Repair a broken runtime or grader separately before attributing results to profile quality.
3. **Freeze the comparison.** Select one candidate before opening the adoption results, including held-out results when used. Record baseline and candidate revisions, cases, repetition count, order, effective runtime/model/configuration, input contract, rubric and evaluator configuration, gates, and stopping policy. Calibrate the evaluators first. Use neutral identifiers and counterbalance version order where practical. A changed environment or tool configuration needs a baseline measured under that condition.
4. **Execute and collect.** Follow the complete [project delivery loop](agent-project-delivery.md#delivery-loop) for each deployed version, retaining trace, terminal result, downloaded artifacts, checksums, and run-to-source evidence. For the supplied control plane, `gateway/refresh` already updates the registered profiles and restarts the gateway; see [hermes-control-plane.md](hermes-control-plane.md). Resume observation of an interrupted run with its original identity and deadline. A diagnostic retry is a separate run, not a replacement for a failed scored sample.
5. **Apply the frozen decision.** Finish the scheduled comparison without changing the candidate or rubric in response to intermediate scores. Report delivery rate, per-case quality, matched-pair changes, hard failures, evaluator disagreement, and resource use. If a pair lacks an artifact, leave its semantic comparison unavailable; do not invent a zero or silently drop the failure from adoption. Show whether gains repeat across cases and repetitions instead of relying on a favorable aggregate mean.
6. **Adopt, reject, or mark inconclusive.** Adopt only when the declared improvement and regression gates pass. If evidence is incomplete or an acceptance boundary remains unresolved, do not claim a win. Retain or restore the baseline through the normal deployment boundary; an underperforming baseline is a reference, not automatically a known-good product. Stop this comparison. Another candidate requires a new hypothesis and an explicit allocation within the remaining authorized project budget; reuse inspected cases honestly as development or regression evidence.

An operational repair or smoke test after the comparison can validate delivery without becoming another quality sample. Keep its scope and receipt separate. A small successful pilot supports only its stated local adoption decision; repeated gains on familiar tasks do not establish broader reliability, and rubric scores alone do not establish learning or other downstream user outcomes.

When evaluating an optimization loop itself, also inspect whether each reflection used real artifact and trace evidence, distinguished plausible causes, considered relevant external methods/tools, changed the asset responsible for the defect, and tested a concrete prediction in the next run. Record both the predicted behavior and the observed quality/regressions. A well-documented rejected hypothesis can demonstrate useful diagnosis but cannot count as a quality gain. Follow [profile-development.md](profile-development.md) for this design step. A candidate's failed gate stops that comparison; continue remaining user-authorized iterations with a new hypothesis within the existing total budget. Do not redefine the rubric or end the outer project merely to turn a failed candidate into a successful report.

If the target gateway API is not reachable, stop before claiming an optimization result. A control-plane `finalize` success or a hand-authored result file can validate result transport, but it is not evidence that Hermes executed the task. Record the missing runtime endpoint as a deployment or runtime-boundary failure.

## Source material

- [OpenAI: Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
- [OpenAI: Harness-aware evaluation of plugins](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)

