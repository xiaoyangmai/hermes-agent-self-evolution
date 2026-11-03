# Hermes control-plane API

Read this module when a remote Hermes host is managed through the supplied control service instead of SSH.

For the team-level relationship between a Git project, Hermes project, Kanban board, and multiple profiles, read [hermes-team-model.md](hermes-team-model.md) as well.

## Connection

Use the configured control-plane endpoint:

```bash
export HERMES_CONTROL_URL="https://hermes-control.llmhub.space"
export HERMES_CONTROL_TOKEN="<provided through the local secret environment>"
export HERMES_GATEWAY_URL="<the reachable Hermes API Server base URL>"
```

Never write the token into a Skill, Git repository, deployment manifest, log, prompt, or request body. The Skill should refer to `HERMES_CONTROL_TOKEN`; the operator or secret manager supplies its value at execution time.

The public probes do not need a token:

```bash
curl "$HERMES_CONTROL_URL/healthz"
curl "$HERMES_CONTROL_URL/readyz"
```

Management endpoints require:

```http
Authorization: Bearer $HERMES_CONTROL_TOKEN
```

The control plane and the Hermes Gateway are separate interfaces. Before a full agent run, verify that `$HERMES_GATEWAY_URL/p/<profile>/v1/capabilities` is reachable with the target profile's `API_SERVER_KEY` and advertises `run_submission`, `run_status`, and `run_events_sse`. The control token must not be reused as the Gateway key. If no reachable Gateway URL exists, stop at the control-plane checks and report a runtime exposure/deployment gap; do not treat `finalize` as proof that a task ran.

For isolated experiments the supplied control-plane exposes slots `a` and `b`. Submit `POST /v1/projects/<project>/experiments/<slot>/release` with a full Git `revision` and idempotency key, then poll the operation. The same slot prefix supports `environment/check`, `environment/prepare`, `profiles/<profile>/gateway-key` and `runs/<delivery>/finalize|result|artifacts`; artifact download remains `/v1/artifacts/<artifact-id>/download`. Slot Gateways are `/gateway-experiment-a` and `/gateway-experiment-b`. Each slot has its own checkout and Hermes home; inside either Gateway the project path is `/opt/data/projects/<project>`. Slot environment checks compare profile configuration with production; prepare requires an idle slot and reconciles drift. When the installed service supports a project-declared curator disable, check both `production_profile_configs_match` (strict equality) and `experiment_profile_configs_compatible` (the declared controlled difference); compatible is not identical. Confirm the actual project check verifies the curator is disabled and reassess production compatibility before promotion. Subsequent release for the same project uses native profile update to preserve prepared config. Slots isolate runtime operations, not untrusted code, and one optimization process must exclusively own them; there is no cross-client lease.

The deployed control plane supports `GET /v1/projects/<project-id>/profiles/<profile>/gateway-key` for a registered named profile. The control token authenticates this request; its `api_server_key` response is the existing Gateway credential, not a short-lived token. The service only supports the single-line URL-safe format `API_SERVER_KEY=<key>`; unsupported formats return 503, an unregistered profile returns 404, and `default` returns 409. The control token remains a global management credential, not project-scoped authorization. Keep the returned key in process memory or an authorized secret store; never print it or put it in a Skill, repository, task input, or log. If the interface is unavailable on another target, use that target's existing authorized secret-delivery mechanism and report any gap.

The [local HTTP operator](../scripts/hermes_operator.py) provides `release`, `run`, and `collect` for lightweight or standalone operations; it is not an optimizer. In a [DSPy Self-Evolution experiment](dspy-self-evolution.md), use that engine's integrated client instead of wrapping it in another release/round loop. The operator requires Python 3 and the environment variables above. `run` also accepts an existing `HERMES_GATEWAY_API_KEY`; if unset, pass `--project` and it retrieves the registered named profile key into memory. An explicitly set Gateway key takes precedence. Credentials are never recorded or printed.

The operator retries a GET connection failure once, including timeouts raised while opening the request or receiving its response headers, and reports the retry on stderr. It does not retry HTTP errors or automatically resend POST requests. This does not reconnect an established SSE stream or recover missing events.

```bash
# Use the full committed SHA; sync fetches HEAD and compares after checkout.
python "<skill-folder>/scripts/hermes_operator.py" release --project "<project-id>" --expected-revision "<full-git-sha>" --receipt release.json

# task.json is a JSON object containing an input string and optional instructions.
python "<skill-folder>/scripts/hermes_operator.py" run --project "<project-id>" --profile "<named-profile>" --input task.json --request-key "<stable-key>" --events events.sse --receipt run.json

# The producer must already have written the result and declared artifacts.
python "<skill-folder>/scripts/hermes_operator.py" collect --project "<project-id>" --delivery-id "<delivery-id>" --gateway-run-id "<gateway-run-id>" --output artifacts --receipt collect.json
```

Use `release` only for an intended project release: it compares the sync SHA, checks the environment, then calls one `gateway/refresh` and polls. A `skipped` environment check is recorded, not proof of dependency readiness; a non-ready check stops, and prepare is a separate operation. The script does not verify effective runtime profile contents. Use `run` for a Gateway task: after successful submission it immediately saves the run ID and an `in_progress` receipt, then captures a partial SSE stream and updates the receipt on exit. This makes the run ID available before the first event or terminal status. It does not independently check capabilities, and its timeout does not send `stop`. Use `collect` after the producer has written `.harness/results/<delivery-id>/result.json` and, when there are artifacts to register, `manifest.json`. The caller chooses and supplies the delivery ID before submission; the Gateway run ID is a separate value returned after submission. `collect` registers and downloads files, verifying IDs and SHA-256; it does not create missing producer files or verify a binding between the caller-supplied Gateway run ID, delivery ID, artifact contents, and source revision. Neither a successful collection nor a caller-supplied revision is acceptance evidence by itself.

`collect` normally derives a stable finalize idempotency key from the project and delivery ID. If a finalize is confirmed failed and its cause has been corrected, use a new unique `--finalize-key` for that new operation; do not change keys while the original outcome is unknown. The operator does not perform the project's deterministic or model-based evaluation.

## Project registration

Register a project once before using its profile or gateway controls:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/register" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: <unique-register-key>" \
  -d '{
    "project_id": "<project-id>",
    "git_url": "https://<host>/<org>/<repo>.git"
  }'
```

The body contains only `project_id` and `git_url`. The Git URL must be HTTPS and must not contain credentials, query parameters, or fragments. The service chooses the internal checkout path; the caller never sends a local path.

Registration returns `202` and an asynchronous operation id:

```json
{
  "id": "<operation-id>",
  "action": "project_register",
  "status": "queued"
}
```

Poll it until it reaches a terminal state:

```bash
curl "$HERMES_CONTROL_URL/v1/operations/<operation-id>" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"
```

Do not start later actions while registration is still queued or running.

The registration operation pulls and records the Git project, creates or confirms the Hermes project and same-named Kanban board, sets the default workspace, and discovers and installs the distributions present at registration. It records that profile roster for later updates. The current service uses shared, globally named Hermes profiles: a different project using the same profile name can overwrite the installed distribution. Verify that names do not conflict before registering another project; a project identifier does not by itself isolate profiles.

## Update sequence

For a newly registered project, use this order and wait for each operation to finish:

1. Register the project and poll the operation.
2. Run the remote environment check. If it is not ready, run the controlled prepare operation and require its post-install recheck to pass.
3. Compare the intended roster with the registration receipt and the source distributions. If the registered roster does not match, stop and resolve the roster through a supported administrative workflow; this API currently has no endpoint for independently adding a role to an existing project.
4. When updating the registered profiles and restarting the gateway, submit `gateway/refresh` once and poll it. Registration has already installed the initial profiles; do not run an extra profile update solely because registration completed.
5. Check Gateway capabilities, run a representative task through the Hermes API, and retain its run identifier.
6. Write the terminal result and declared artifacts into the project's result directory, finalize the run through the control plane, and poll the finalize operation.
7. Fetch the stored result and artifact list, download referenced artifacts, and verify their checksums before acceptance.

In this service, `gateway/refresh` first runs `profile/update` for every profile in the registered project roster, and on success restarts the registered gateway Deployment. It is not a hot reload. The Deployment can be shared by projects, so the restart may interrupt their active runs. Choose a safe time and track the operation to completion. `gateway/restart` restarts the Deployment without the profile update. `profile/update` alone updates the registered profiles without restarting the gateway. Do not call `profile/update` immediately before `gateway/refresh` unless a distinct update-only step is needed: refresh would update the same profiles again.

For a deliberate update-only operation:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/profile/update" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"
```

For the alternative update-and-restart operation:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/gateway/refresh" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"
```

`profile/update` is project-level and processes the registered roster as a set; it does not take a single-profile body. Normal registered projects have a persisted roster. Later Git sync, update, and refresh do not add newly introduced `profiles/*/distribution.yaml` directories to that roster. There is no supported roster-edit HTTP endpoint in the current service; verify the live API or use a separately supported administrative procedure instead of assuming an added role is active. The service has no project/roster GET endpoint, so retain the registration receipt and any later authoritative administrative evidence.

These actions are asynchronous. A returned operation id is only a queued-operation handle, not a success result. Poll `/v1/operations/<operation-id>` after each request and retain the terminal status as part of the release receipt. For a multi-profile update, the receipt must include the discovered profile list and the profiles actually updated.

For later authored changes, the normal flow is:

```text
local validation
  -> commit and push Git
  -> POST /v1/projects/<project-id>/sync and poll the actual revision
  -> environment/check (and environment/prepare when needed)
  -> poll operation
  -> compare expected source profiles with the registered roster
  -> gateway/refresh (updates registered profiles, then restarts the gateway)
  -> poll operation
  -> health + representative run + trace
  -> write result.json and manifest.json
  -> runs/<delivery-id>/finalize
  -> poll operation
  -> fetch result, artifacts, and downloads
  -> evaluate
```

Use `gateway/restart` when only a process restart is needed. Use `gateway/refresh` when the registered profile distributions must be updated and the gateway restarted. If using `profile/update` separately for a deliberate update-only operation, choose and document the later lifecycle action based on the actual service contract.

`profile/update` uses the registered checkout; it does not pull newly pushed Git by itself. Call the asynchronous sync operation first:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/sync" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN" \
  -H "Idempotency-Key: <unique-sync-key>"
```

The sync operation uses only the registered Git URL and service-owned workspace, rejects a tracked dirty checkout, preserves untracked `.harness/results`, and returns the observed revision. It fetches the registered remote's HEAD; this API accepts no requested or expected revision. Compare the returned SHA with the intended commit and stop before later steps if they differ. Sync cannot directly select an older commit for rollback; use a supported source-release procedure and verify the resulting revision.

## Effective configuration and unattended tools

A tool appearing in `/p/<profile>/v1/toolsets` does not prove that the execution mode permits it. Verify the intended tool path in a real unattended task. In the audited Hermes version, `code_execution` exposes `execute_code` when its sandbox is available, but unattended approval policy can still reject every invocation. For a profile dedicated to that execution mode, the native `agent.disabled_toolsets: [code_execution]` setting removes the unusable toolset while retaining normal file and terminal tools. Do not disable approvals to make the advertised tool work. Check the installed version and actual policy before applying this example elsewhere.

Keep stable, non-secret configuration intent in the profile's native `config.yaml`. The current control plane invokes normal profile update without `--force-config`, so existing runtime configuration is preserved: a successful refresh does not prove that a newly authored setting took effect. Apply a needed configuration migration through the already authorized deployment path, record the specific keys changed, refresh or restart as appropriate, and compare effective `/v1/toolsets` plus a new session's behavior. In an explicitly authorized development SSH session, the native CLI can migrate one key, for example `hermes --profile <profile> config set agent.disabled_toolsets '["code_execution"]'`; this is not a requirement to use SSH in normal operation. Do not replace the whole live configuration or invent a new control-plane API for this migration. If the available deployment path cannot apply the setting, report that concrete gap.

Keep an operational repair probe separate from a frozen quality comparison. A short task that verifies usable tools and artifact delivery does not establish improved semantic quality or faster performance on the original task.

## Controlled environment and run result APIs

The supplied control plane exposes a narrow environment boundary. It runs only the project's fixed scripts; callers cannot submit arbitrary shell commands or paths.

The project may provide:

```text
ops/check-environment
ops/install-environment
```

`check-environment` is read-only. Exit code 0 means the check command completed; its JSON output may include `ready: true|false` and machine-readable check details, returned under the operation result's `check.details`. The service executes both fixed scripts with `/bin/sh`; use a shell wrapper for Python or another language instead of relying only on its shebang. `install-environment` prepares the declared remote dependencies and should be idempotent. The service supplies `HERMES_PROJECT_ID`, `HERMES_PROJECT_HOME`, `HERMES_ENVIRONMENT_OPERATION`, and a project-local `HOME` to both scripts.

Run the check as an asynchronous operation:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/environment/check" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"
```

If it reports `ready: false`, prepare the environment and wait for the service to run the check again:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/environment/prepare" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN" \
  -H "Idempotency-Key: <unique-prepare-key>"
```

Both endpoints return `202` with an operation id. Poll `/v1/operations/<operation-id>` and stop if the operation fails or the post-prepare result is still not ready. If the check script is absent, the service returns `skipped: true` and `ready: true`; treat that as an explicit declaration that the project has no control-plane environment check, not as proof that every external dependency exists.

A completed runtime task is finalized from files already written in the project checkout. This control plane does not start a Hermes task; trigger the task through the Hermes runtime API and use these endpoints for environment preparation and result handoff. The required file is:

```text
.harness/results/<delivery-id>/result.json
```

The JSON should contain the machine-readable terminal result, profile, source revision, and evaluation-relevant fields. An optional `manifest.json` declares files to register:

```json
{
  "artifacts": [
    {
      "path": "patch.diff",
      "name": "patch.diff",
      "kind": "patch",
      "content_type": "text/plain"
    }
  ]
}
```

Finalize with an idempotency key and an empty request body:

```bash
curl -X POST "$HERMES_CONTROL_URL/v1/projects/<project-id>/runs/<delivery-id>/finalize" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN" \
  -H "Idempotency-Key: <unique-finalize-key>"
```

Poll the returned operation to a terminal state. `finalize` registers the result and declared artifacts; it does not execute the task. A successful queue response is not acceptance evidence. Then retrieve the stored result and artifact metadata:

```bash
curl "$HERMES_CONTROL_URL/v1/projects/<project-id>/runs/<delivery-id>/result" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"

curl "$HERMES_CONTROL_URL/v1/projects/<project-id>/runs/<delivery-id>/artifacts" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN"
```

Download each referenced artifact and verify the response checksum before using it locally:

```bash
curl -fL "$HERMES_CONTROL_URL/v1/artifacts/<artifact-id>/download" \
  -H "Authorization: Bearer $HERMES_CONTROL_TOKEN" \
  -o "<local-output-file>"
```

The download response includes `X-Artifact-Id` and `X-Artifact-Sha256`. The local harness should compute SHA-256 for the downloaded file and compare it with the returned metadata. Treat missing `result.json`, invalid manifests, path escapes, size-limit failures, checksum mismatches, and failed finalize operations as acceptance failures.

The complete control-plane loop is:

```text
healthz/readyz
  -> project register and poll
  -> environment/check and poll
  -> environment/prepare and poll when needed
  -> gateway/refresh and poll (registered profile updates + gateway restart)
  -> run representative task and trace it
  -> write .harness/results/<delivery-id>/result.json and manifest.json
  -> runs/<delivery-id>/finalize and poll
  -> runs/<delivery-id>/result
  -> runs/<delivery-id>/artifacts
  -> artifacts/<artifact-id>/download and checksum verification
  -> deterministic + model-based evaluation
```

The real Hermes task stage uses the Gateway API, with a separate profile key:

```bash
curl "$HERMES_GATEWAY_URL/p/<profile>/v1/capabilities" \
  -H "Authorization: Bearer $HERMES_PROFILE_API_KEY"

curl -X POST "$HERMES_GATEWAY_URL/p/<profile>/v1/runs" \
  -H "Authorization: Bearer $HERMES_PROFILE_API_KEY" \
  -H "Idempotency-Key: <unique-run-key>" \
  -H "Content-Type: application/json" \
  -d '{"input":"<fixed task input>","instructions":"<run contract>"}'

curl "$HERMES_GATEWAY_URL/p/<profile>/v1/runs/<gateway-run-id>" \
  -H "Authorization: Bearer $HERMES_PROFILE_API_KEY"

curl "$HERMES_GATEWAY_URL/p/<profile>/v1/runs/<gateway-run-id>/events" \
  -H "Authorization: Bearer $HERMES_PROFILE_API_KEY"
```

Capture the `run_id`, status, and available events while the run is active before writing the result files and calling control-plane `finalize`. In the audited Gateway, SSE is an in-memory partial stream: it omits some events, tool results are truncated previews, and disconnection is not a replayable durable trace. Preserve what is available and record gaps; do not claim a complete tool or subagent trace from SSE alone. The control-plane endpoint has no task-start or event-stream behavior of its own, and finalize does not authenticate a result's claimed run id or source revision against the Gateway.

When SSE tool previews are insufficient, use the returned session identifier and the same profile Gateway key to fetch `GET $HERMES_GATEWAY_URL/p/<profile>/api/sessions/<session-id>/messages?order=oldest&limit=500&offset=0` after the run. The current API returns stored conversation and tool messages in `data`, plus `pagination`; without explicit pagination it defaults to the latest 500 messages. Preserve each page, advance `offset` by `pagination.returned`, and continue until fewer than `pagination.limit` messages are returned. This supplements execution evidence with session history; it is not an SSE replay or a guarantee of complete tool/subagent traces, and does not replace result/artifact collection.

For optimization, use the project's frozen search budget and adoption comparison; there is no universal two-round schedule. [DSPy Self-Evolution](dspy-self-evolution.md) owns the executable search/release/evaluation loop when configured. Keep separate Gateway run and delivery ids, revisions, traces, results, artifact checksums and evaluator scores. Control-plane does not score quality, choose candidates or own promotion policy. Its environment and artifact endpoints remain necessary infrastructure.

## Distribution prerequisite

`profile/update` and `gateway/refresh` require the target profile to be a Hermes distribution. The current `foundation/default` profile has no `distribution.yaml`; requests against it return `409 profile_not_distribution`. This is a packaging/update limitation of that profile, not a failure of project registration, Kanban setup, or task routing.

Before choosing a target profile, verify that the project's authored profile contains a valid `distribution.yaml` and the distribution files are in the expected Git source. Do not try to work around this error by copying a full live profile directory.

The harness-governance Skill should generate this manifest during Hermes project bootstrap when the profile is intended to be remotely updated, then validate the manifest before registration or deployment.

The supplied control service discovers root and `profiles/*/distribution.yaml` files at registration and records the roster. Later it verifies manifests for that roster, invokes Hermes profile updates, and reports failure when a command exits non-zero. It does not prove that every manifest field, dependency, or runtime behavior is effective. Confirm that separately with Hermes profile metadata, gateway state, and representative tasks.

## Failure handling

- A `202` means the operation was queued, not that it succeeded.
- Poll the operation until success or failure before starting the next step.
- A failed environment prepare must stop publication until the recheck passes.
- A failed batch update can leave earlier profiles updated; the service does not automatically roll them back. Inspect the actual installed state, stop further release steps, and restore or otherwise reconcile the last known-good version through a supported workflow before resuming. Report any unresolved partial state.
- Do not treat a completed run status or finalize status as the final answer; fetch `/result`, `/artifacts`, and each `/download` response.
- Record a complete release receipt: project id, intended SHA, actual checkout SHA and its evidence source, effective runtime/profile evidence, Hermes version or image, registered and served profiles, environment check and prepare results, operation ids, terminal statuses, restart behavior, smoke run, final result, artifact identifiers, evaluation evidence, and the previous known-good revision for rollback. A sync SHA proves the checkout revision only; an update or refresh response does not by itself bind the running profile to that SHA. Verify effective state where an authorized surface permits it; otherwise record that gap.
- Never log or echo the control token.

## Multi-profile acceptance

Do not mark a team release successful from the project-level operation alone. Verify all of the following:

- the repository discovery step found every intended `distribution.yaml` profile and no unintended profile;
- the update operation reports the expected profile set;
- the gateway's `served_profiles` (and, when exposed, its standalone/multiplex reason) matches the intended roster and does not show an unintended standalone fallback;
- each intended profile answers a minimal model or chat request through its profile route, such as `/p/<profile>/v1/models` and one minimal chat call;
- profile-specific configuration is present where required, while secrets and live state remain outside the distribution;
- health, capabilities, and the smoke task pass after the refresh or restart.

For a behavior change, the smoke call is only the entry point. Follow the representative run through its status or event stream, inspect the generated files, patches, tests, tool outcomes, and task-state changes required by the acceptance case, and record the run or artifact identifiers in the release receipt.

## Final result collection

Keep these steps separate:

1. submit the task through the Hermes runtime and retain the run or operation id;
2. follow status, events, and traces until a documented terminal state;
3. ensure the runtime has written `.harness/results/<delivery-id>/result.json` and any `manifest.json`;
4. call `runs/<delivery-id>/finalize` with a unique idempotency key and poll the finalize operation;
5. fetch `runs/<delivery-id>/result` and `runs/<delivery-id>/artifacts`;
6. download every referenced artifact from `/v1/artifacts/<artifact-id>/download` and verify `X-Artifact-Sha256` locally;
7. verify the collected result against the acceptance case and record the result and artifact identifiers.

A completed operation, `run.completed` event, or status record is not necessarily the final answer or artifact. The control-plane `finalize` operation is the handoff from remote workspace files to the local consumer; it does not run the task or perform semantic evaluation. If the runtime only exposes a stream, persist the terminal result event and artifact references it carries before finalizing and evaluating the task.

## Source verification

This control-plane contract was supplied for the remote Hermes deployment service. If the service implementation changes, verify the live `/healthz`, `/readyz`, operation response shape, environment check/prepare behavior, finalize idempotency requirement, result and artifact response shapes, download checksum headers, `409 profile_not_distribution` behavior, and the project's `distribution.yaml` before changing this guidance.
