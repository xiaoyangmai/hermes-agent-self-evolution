# Hermes state, sessions, and recovery

Read this module for prompt refresh, context compression, session persistence, checkpoints, cron, gateways, or restart behavior.

## Sessions and prompt snapshots

Hermes stores conversations per profile in SQLite `state.db`, including message history, tool calls, token counts, and the system-prompt snapshot. SQLite sidecars such as `state.db-wal` and `state.db-shm` are part of the live store; do not copy or rewrite only the main file while another process writes.

A continuing session normally reuses the original system prompt to preserve prompt-cache prefixes. Changes to `SOUL.md`, Skills, memory, or project context do not reach a running session until `hermes sessions refresh-prompts` is requested. Refresh rebuilds the prompt but not the session's tool list, and the refresh turn pays a cache miss. A new session is the simplest way to guarantee a fresh tool/context assembly.

## Background review and mutable Skills

Hermes versions with background self-improvement can create or modify profile Skills after a run has completed. A `run.completed` event therefore does not by itself prove that the profile's files have stopped changing or still match the Git distribution. Check the installed version and effective configuration, and inspect the relevant Skill content or hash, trace, and available review history at the points required by the task. For a comparison, distinguish the Skill actually loaded during each run from any later automatic change that affects the next run; use [evals-and-feedback.md](evals-and-feedback.md) for the comparison procedure.

Fingerprint the available profile Skill inventory as paths and content hashes, alongside the relevant SOUL, effective configuration, and memory inputs; keep secret values out of evidence. Record `skills/.usage.json` separately: reading a Skill updates usage counters, which is not itself a change to the Skill's behavioral instructions.

When drift occurs, preserve enough evidence to review the generated change and determine ownership. If the intended version is distribution-owned, restore the reviewed committed version through the project's normal deployment workflow after the background writer has finished; verify the effective content again. With the supplied control plane, `gateway/refresh` updates the registered profiles and restarts the gateway; see [hermes-control-plane.md](hermes-control-plane.md). Do not assume profile update overwrites every local file or setting, discard unrelated local state, or disable self-improvement solely because it exists.

For a controlled experiment, a deployed Hermes version exposing native per-profile `auxiliary.background_review.enabled` can disable background review for the target profile through the authorized environment preparation boundary. Record and freeze its effective configuration. Restore a temporary override when the experiment ends. If the project deliberately assigns durable Skill ownership to Git and DSPy Self-Evolution, keep that declared setting in the project instead; competing background writers would invalidate the chosen ownership. This is not a universal requirement to disable background review. Distribution update preserves local settings, so verify the actual value.

CLI startup is a separate state writer. In the inspected 0.21.4 installation, starting `hermes chat` synchronizes bundled Skills before `--ignore-rules` takes effect, even when background review is disabled. The `.no-bundled-skills` opt-out still permits essential Skill seeding. Do not treat a nested one-shot CLI as a fresh, state-free reviewer for a shared profile. Probe the actual invocation and inventory changes first, or use the existing profile APIs with an explicit caller-owned production/review/repair handoff. If startup adds files during an experiment, preserve the failed attempt, identify newly added files by provenance and hashes, and recover only that owned delta after writers stop; do not erase unrelated profile state.

## Compression and long tasks

Hermes has context-compression and pruning paths that protect recent and important content, but compaction can still lose detail. A long-running harness should leave durable plans, progress, decisions, and next steps in repository artifacts rather than relying on the compressed transcript. Verify the active context engine and compression settings in the installed version before making budget claims.

## Checkpoints and rollback

Checkpoints are opt-in. Hermes can snapshot before file writes and destructive terminal operations, but support depends on the path and backend. Container-side paths, nested repositories, very large directories, and large files can be excluded or refuse restore. A checkpoint listing is not proof that every file in a container workspace is recoverable.

## Cron and process ownership

Cron can run one-shot or recurring agent sessions, attach Skills, set a work directory, and deliver results. Deliveries are fire-and-forget by default; continuable delivery must be enabled. Cron runs have their own model and approval resolution and cannot recursively create more cron jobs.

Gateway, Desktop, CLI, cron, and dashboard processes may share the profile's SQLite store, but store maintenance and repair require the documented ownership/locking workflow. Background child processes belong to the child/parent lifecycle described in the delegation module; a session restart is not a durable job queue.

## Source map

- Docs: [Sessions](https://hermes-agent.nousresearch.com/docs/user-guide/sessions), [Session storage recovery](https://hermes-agent.nousresearch.com/docs/user-guide/session-storage-recovery), [Checkpoints and rollback](https://hermes-agent.nousresearch.com/docs/user-guide/checkpoints-and-rollback), [Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)
- Code: [`agent/context_compressor.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/context_compressor.py), [`agent/background_review.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/background_review.py), [`hermes_state.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_state.py), [`hermes_state_wal.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_state_wal.py), [`hermes_state_prompt_refresh.py`](https://github.com/NousResearch/hermes-agent/blob/main/hermes_state_prompt_refresh.py), [`tools/skills_sync.py`](https://github.com/NousResearch/hermes-agent/blob/main/tools/skills_sync.py), [`agent/skill_utils.py`](https://github.com/NousResearch/hermes-agent/blob/main/agent/skill_utils.py), [`cron/`](https://github.com/NousResearch/hermes-agent/tree/main/cron)
