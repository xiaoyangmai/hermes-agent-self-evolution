# Hermes profile distribution and remote deployment

Read this module when Codex is developing a Hermes profile locally while a Hermes gateway runs on another machine, or when a change must move from a repository into a live profile.

## The boundary

Keep three planes separate:

1. **Source plane** — the Git repository containing the authored agent definition and its validation evidence.
2. **Deployment plane** — the command, CI job, or narrow deployment hook that applies a recorded revision to a remote profile.
3. **Runtime plane** — Hermes Gateway APIs that submit, observe, steer, approve, and stop agent work.

Do not use the Gateway API as a release channel. It can execute agent work, but it is not a safe substitute for a deployment boundary. Keep an explicit reachable Gateway API base URL and the target profile's API key separate from the control-plane URL and token. If the deployment exposes only the control plane and no `/v1/capabilities` or `/v1/runs` endpoint, the runtime execution gate is unavailable; stop before claiming a task or optimization succeeded. Do not let a running agent pull arbitrary profile code or execute an unreviewed deployment command.

## Agent project delivery loop

When Codex is developing a Hermes profile for a remote gateway, the local machine is the authoring and checking environment; the remote Hermes project is the delivery target. The normal loop is:

```text
edit profile source and distribution files locally
  -> run local checks and optional dry run
  -> check the remote environment and prepare approved dependencies
  -> commit and push
  -> project/sync and verify the observed revision
  -> gateway/refresh and poll (registered profile update + gateway restart)
  -> run representative cases on the remote profile
  -> poll to terminal state and fetch the final result
  -> trace the run and inspect referenced artifacts
  -> apply deterministic and model-based evaluation when needed
  -> compare with acceptance criteria
  -> keep, revert, or make the next focused change
```

Do not accept a local dry run as proof that the remote profile is correct. For each iteration, retain the source revision, environment-check result, operation identifiers, run or event identifiers, final result identifier, produced files or patches, test and evaluation results, and the decision made from the evidence. Read [agent-project-delivery.md](agent-project-delivery.md) for the runtime-neutral design and iteration method.

## What belongs in the distribution

Hermes' native profile distribution is the right packaging boundary. A distribution repository can contain:

- `distribution.yaml` — Hermes' native distribution manifest and version metadata;
- `SOUL.md` — the profile's durable identity and role;
- `skills/` — Hermes Skills, references, scripts, and assets owned by the distribution;
- `mcp.json` — reviewed MCP declarations, when the deployment needs them;
- `cron/jobs.json` — authored scheduled jobs, reviewed separately;
- `config.yaml` — only stable, non-secret defaults that the deployment intentionally owns;
- `AGENTS.md` or other project context files when they are part of the working repository;
- `README.md` and validation notes for release review.

Do not put these in the distribution:

- `.env`, `auth.json`, OAuth or bot credentials;
- `memories/`, `sessions/`, `state.db*`, response stores, logs, plans, workspace, or caches;
- machine-specific browser, SSH, cloud, or CLI credential directories;
- live gateway state or files being written by a running Hermes process.

The remote profile is the running instance. It keeps its own credentials, memory, conversations, state, and workspace. Never synchronize a live profile home with `rsync`, a full directory copy, or a second writer while the gateway is running.

## Distribution validation and effective state

Validation has four owners and four different questions:

1. **Repository or harness checks** — Is the manifest present, parseable, named for the intended profile, compatible with the project's policy, and consistent with the files it claims to own?
2. **Control plane** — Did project registration discover the expected distributions, and did the update operation process the expected profile set? The supplied control service checks manifest presence and then invokes Hermes; it does not by itself prove every manifest field is effective.
3. **Hermes CLI and installer** — Did `hermes profile install` or `hermes profile update` accept the manifest, satisfy `hermes_requires`, apply `distribution_owned` paths, and exit successfully? A non-zero CLI result must fail the operation.
4. **Runtime acceptance** — Do available remote evidence surfaces (for example `hermes profile info/list/show` on the host, control-plane results, gateway capability and served-profile state, the profile route, and a representative task) show that the intended distribution is actually active?

`distribution.yaml` is therefore both a package declaration and a runtime input, but it is not an acceptance result. Record the manifest version, source revision, Hermes profile metadata, effective owned files or configuration, and the runtime checks that confirm it took effect.

## Remote dependencies

If a distribution needs packages, binaries, browser drivers, services, model access, or a particular filesystem layout, add two reviewed, idempotent project or deployment scripts:

- `check-environment` reports versions, paths, required services, non-secret credential presence, and reachability;
- `install-environment` or `repair-environment` uses pinned inputs and an allowlisted installer to prepare the host.

Run the check before the profile update. If it fails, call the supplied control plane's `environment/prepare` operation; it runs the fixed `ops/install-environment` script and then repeats the check. The current control plane registers projects, discovers distributions, invokes Hermes profile install/update, seeds profile runtime configuration, and provides this controlled environment preparation boundary. It does not accept arbitrary commands or automatically install dependencies merely because they appear in `distribution.yaml`. Do not hide dependency installation inside a profile prompt.

Keep these scripts under a reviewed project or deployment path such as `ops/` or `scripts/`, with a documented exit code and machine-readable summary. A distribution may ship helper files, but Hermes must explicitly support and authorize their execution before they become part of the release path.

## Default release workflow

Use this workflow unless the project has a stronger release system:

1. Identify the target profile, repository revision, Hermes version, gateway process, remote environment, and current work in flight.
2. Inspect the local worktree. Refuse deployment when it contains uncommitted or unpushed changes.
3. Run the smallest relevant checks: Skill validation, manifest checks, linting, and a representative local smoke task when available. Run the remote environment check before the profile update.
4. If the environment check fails, run the approved idempotent installation or repair step, recheck, and stop if it remains unready.
5. Commit the authored changes. Push the commit to the repository branch used by the remote deployment.
6. Call the control plane's `project/sync` operation and verify that its returned revision is the pushed commit. Do not treat a successful Git push alone as remote source evidence.
7. Record the source commit, target project, discovered profile set, requested deployer, environment result, and intended restart or prompt-refresh behavior.
8. Trigger the existing deployment boundary. For the supplied control plane, use `gateway/refresh` once to update all profiles in the registered roster and restart the registered gateway Deployment; poll it and account for any other projects using that Deployment. `profile/update` alone is update-only and `gateway/restart` alone is restart-only. Calling update immediately before refresh repeats the update. See [hermes-control-plane.md](hermes-control-plane.md). If a different deployment explicitly allows SSH, its authenticated command or CI job might run:

   ```bash
   hermes profile update <profile> --yes
   hermes -p <profile> gateway restart
   ```

   When SSH is disallowed, use the existing authorized control plane or CI/deployer. If none is available, report the deployment gap instead of assuming a deployer exists or introducing a new service. For an alternative runtime with a true prompt-only refresh, check the installed runtime's documented behavior; do not treat this service's `gateway/refresh` as prompt-only.

9. Verify the remote result with the deployment log, `health/detailed`, `capabilities`, and the effective distribution metadata. For a multi-profile project, also verify the gateway's served profile set and one minimal model or chat request per intended profile.
10. Run representative acceptance cases through the Gateway `/v1/runs` API. Poll each run to a terminal state, retain the event trace, have the runtime write `.harness/results/<delivery-id>/result.json` and an optional `manifest.json`, call the control plane's `runs/<delivery-id>/finalize` with an idempotency key, poll the finalize operation, then fetch `runs/<delivery-id>/result`, `runs/<delivery-id>/artifacts`, and each `artifacts/<artifact-id>/download` response. Verify the returned SHA-256 values before applying the defined deterministic and model-based evaluation.
11. Mark the deployment and project iteration successful only after the environment, effective distribution, Gateway run trace, final result, downloaded artifacts, and evaluation checks pass. On failure, stop routing new work if necessary, restore the last known-good authored revision, restart or refresh the gateway, and repeat the checks.

The commit is the handoff boundary. A deployment may be triggered manually at first; it must still apply a committed revision and produce an observable result. The resulting release receipt should contain:

- source repository and revision intended and observed, with the evidence source for the applied revision;
- target Hermes project and discovered/served profiles;
- Hermes version or image digest;
- operation or deployment ids and terminal states;
- restart versus refresh choice;
- environment check and dependency-preparation result;
- health, capabilities, effective distribution metadata, and per-profile smoke results;
- run ids, terminal statuses, final result identifiers, artifact references, and evaluation scores;
- previous known-good revision and rollback result if recovery was needed.

## Choosing the deployer

### No-SSH deployment boundary

When SSH is disallowed, prefer an existing authorized control plane or CI/deployer. For the supplied Hermes control plane, follow [hermes-control-plane.md](hermes-control-plane.md) for registration, operation polling, Git sync, and `gateway/refresh`. That service fetches the registered remote's HEAD and returns the observed SHA; it cannot accept an arbitrary revision. If no supported deployment boundary exists, report the gap instead of assuming or requiring a new service.

Do not auto-deploy every local save. Deploy after a commit has passed the repository checks and is visible in the remote Git source.

## Reproducibility and rollback

Hermes profile distributions currently update from the recorded Git source and default branch; do not assume that a Git tag or commit suffix pins the installed revision. If exact reproducibility matters, let CI check out a known commit and hand a reviewed artifact or deployment checkout to the remote wrapper. Otherwise, use a protected deployment branch and record its head before and after each update.

Keep the last known-good revision and a deployment record outside the live session transcript. A rollback means restoring distribution-owned files and restarting or refreshing the gateway; it must not delete memory, sessions, credentials, or the profile's runtime database unless the incident specifically concerns that state and the documented recovery procedure allows it.

## Codex-to-Hermes sharing

Codex's global Skills are not automatically visible to Hermes. If the same governance idea must guide Hermes, maintain a Hermes-adapted copy under the distribution's `skills/` tree. Keep the source relationship explicit in the repository and validate both copies; do not silently rely on a machine-local Codex path.

Hermes documentation and behavior change quickly. Before changing this workflow, read the current [profile distribution documentation](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions) and [API Server documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server), inspect the installed Hermes version, and verify the active profile, gateway, terminal backend, and API surface.

## Evidence to retain

For each remote update, retain enough evidence to answer:

- Which source commit or release was intended and applied?
- Which Hermes profile and host received it?
- Which authored files changed?
- Was the gateway restarted or merely refreshed?
- Did the remote environment pass its check and, when needed, its controlled preparation and recheck?
- Did the effective distribution metadata and served profile state match the source?
- Which run was finalized, what final result was returned, and where are the downloaded artifacts and their checksums?
- Did health, capabilities, the smoke task, and the defined evaluation pass?
- What is the previous known-good revision and how would it be restored?
