# Maintenance checklist

## Before editing

- [ ] Classify the request as Mode A runtime guidance or Mode B full Agent-project governance; then classify the specific change: architecture, context, Skill, subagent, tool/environment, long-running state, evaluation, release, or repository maintenance.
- [ ] Read the nearest `AGENTS.md` and the relevant repository map before reading every detailed document.
- [ ] Inspect existing Skills, agent definitions, tool declarations, memory/index files, plans, evals, and validation commands.
- [ ] Identify the current source of truth for each rule and any conflicts or duplicated instructions.
- [ ] Define the target behavior, acceptance criteria, stopping conditions, and validation commands.
- [ ] If agent behavior is changing, name the local authoring target, remote runtime target, representative task, trace, artifacts, and evidence that will decide acceptance.
- [ ] If the remote environment has dependencies, define a read-only environment check and an approved idempotent install or repair step.
- [ ] Decide whether the request needs a new artifact at all; preserve local conventions when they already work.

## During editing

- [ ] Keep the entry point short and navigational; move details to linked references.
- [ ] Keep runtime-neutral rules separate from Hermes/Codex/Claude adapter notes.
- [ ] Give each rule one owner: repository map, Skill, subagent, runtime control, memory, or evidence artifact.
- [ ] Add subagents only for isolated context, specialization, parallel independent work, or dynamic decomposition.
- [ ] Record only material decisions and evidence; do not turn transcripts into policy.
- [ ] Keep one change hypothesis per iteration and retain a known-good baseline for comparison.
- [ ] Keep paths repository-relative where possible and keep credentials outside version control.
- [ ] If a remote runtime is involved, separate authored distribution files from remote state and secrets.
- [ ] Require a clean, committed, pushed revision before triggering a remote update; record the target profile and source revision.
- [ ] Treat distribution validation as separate layers: repository checks, control-plane discovery, Hermes install/update, and effective runtime verification.

## After editing

- [ ] Run the relevant project checks and the Skill Creator validator for any changed Skill.
- [ ] Verify every referenced file exists and every example matches the actual layout.
- [ ] Verify no runtime-specific profile field has been promoted into the neutral specification.
- [ ] Check that changed behavior has an observable eval, test, or documented reason why one is unnecessary.
- [ ] After a remote update, compare the expected and discovered profile rosters, verify every expected profile is served, run a minimal model or chat check per profile, verify health and capabilities, retain the complete release receipt, and keep a known-good revision for rollback.
- [ ] For behavior changes, inspect the run trace and required artifacts before accepting the final response.
- [ ] Retrieve the terminal result and referenced artifacts separately from status or event tracking.
- [ ] Use deterministic checks plus a defined model-based evaluation with fixed thresholds and hard-fail conditions.
- [ ] Inspect the final diff for unrelated edits, duplicated rules, stale links, and unsupported claims.
- [ ] Report what was actually verified, what was skipped, and what remains uncertain.
