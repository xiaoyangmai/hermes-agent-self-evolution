# Hermes project, Kanban, and profile team model

Read this module when one Git repository is operated by several Hermes profiles through one shared Kanban board.

## The model

```text
one Git repository
  -> one Hermes work project
  -> one Kanban board
  -> multiple Hermes profiles for agent roles
```

Example:

```text
project: llmhub-team
git:     https://git.example.com/llmhub-team.git
board:   llmhub-team
profiles: architect, backend, frontend, reviewer
```

These are different objects:

- **Git project** is the shared source code and review history.
- **Hermes project** records the workspace and connects the Git source to the board.
- **Kanban board** is the shared task pool, including tasks, dependencies, status, and assignment.
- **Profile** is one agent identity and runtime environment. A profile may represent `architect`, `backend`, `frontend`, or `reviewer`.
- **Gateway** hosts the profiles and serves their runtime connections.
- **Kubernetes namespace** is only a deployment boundary. It is not a team, board, or profile concept.

Do not collapse these objects into one universal profile or project manifest.

## Team workflow

1. Register the Git repository as a Hermes work project.
2. Create or confirm a Kanban board with the same project identity.
3. Set the project's default working directory and record the project-to-board relationship.
4. Discover and register the role profiles declared by the repository's Hermes distributions. For an externally managed roster, verify the actual supported registration workflow; the supplied control plane has no independent role-add HTTP endpoint.
5. Put all tasks into the same board.
6. Assign each task to one profile at a time.
7. Let the assigned profile implement, test, and commit in the project workspace.
8. Review and merge the change through the repository workflow.
9. Update the Kanban task only after the corresponding work or review state is observable.

The board owns task state. Git owns source state. The profile owns agent identity and runtime state. A gateway restart owns process lifecycle. Keep these update paths separate.

## Update granularity

| Change | Affects |
|---|---|
| Pull or refresh the Git work project | Shared project workspace |
| Create, assign, or move a Kanban task | Board state only |
| Change `backend` distribution source | The backend Hermes distribution only |
| Change `reviewer` distribution source | The reviewer Hermes distribution only |
| Run project-level profile update | All profiles in the registered roster, as reported by the operation |
| Refresh gateway through the supplied control plane | Update the registered roster, then restart the registered gateway Deployment |
| Restart gateway through the supplied control plane | Restart the registered gateway Deployment without a profile update |
| Change Kubernetes namespace | Deployment placement only |

Changing one profile in source does not imply that the service can update only that profile: the supplied project-level update and refresh act on the whole registered roster. Report the actual scope. Updating a task is not a profile deployment, and pulling the Git project is not itself a profile update.

## Registration boundary

The registration request remains small:

```json
{
  "project_id": "llmhub-team",
  "git_url": "https://git.example.com/llmhub-team.git"
}
```

The registration operation currently completes these project-level actions:

- pull and record the Git repository;
- create or confirm the same-named Kanban board;
- set the default workspace;
- record the project-to-board relationship;
- discover and register the role profiles declared by the repository's Hermes distributions.

Profile distribution updates remain separate from project registration. The supplied control plane stores the role roster discovered during registration; subsequent `sync`, `profile/update`, and `gateway/refresh` do not automatically add a new distribution. It has no independent role-add HTTP endpoint. If the desired roles change, identify a supported administrative procedure and verify the resulting roster rather than assuming the new role was registered. Record the registered and updated profiles in the release receipt.

The current registration flow is a complete project/team registration operation: it pulls and records the Git repository, creates or confirms the Hermes project and Kanban board, sets the workspace, records their relationship, and discovers or registers the role profiles declared by the repository's Hermes distributions. Profile distribution updates remain a separate lifecycle even when the initial role roster is created during registration.

The supplied service installs profiles by globally shared Hermes profile names. Different projects using the same role name can overwrite the existing distribution; a project or board does not isolate profile storage. Check for conflicts through an authorized supported mechanism before registering another project. Gateway Deployments can also be shared, so a refresh or restart may affect other projects' active runs.

## Profile distribution bootstrap

When a role profile is expected to receive `profile/update` or `gateway/refresh`, bootstrap it as a Hermes distribution before deployment. Each updateable role should have its own native manifest in the authored profile source. The control plane discovers manifests at registration and checks the stored roster during later updates; adding a manifest later does not itself register a role. A role without a manifest is not an updateable Hermes distribution:

```text
profiles/
├── architect/
│   ├── distribution.yaml
│   ├── SOUL.md
│   └── skills/
├── backend/
│   ├── distribution.yaml
│   ├── SOUL.md
│   └── skills/
└── reviewer/
    ├── distribution.yaml
    ├── SOUL.md
    └── skills/
```

The minimal manifest is:

```yaml
name: backend
version: 0.1.0
description: "Backend development agent"
```

Add `hermes_requires`, `env_requires`, and `distribution_owned` only when the profile needs them. Never put token values or other secrets in the manifest. A profile without this file may still run, but the control service must reject its distribution update rather than pretending it was deployed.

## Evidence

For a team run, retain enough information to answer:

- Which Git project and revision was used?
- Which Kanban board and task were assigned?
- Which profile owned the task?
- Which commit or review changed the shared repository?
- Which profile distribution or gateway operation was updated separately?
