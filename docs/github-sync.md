# GitHub Two-Way Sync

Two-way sync between GitHub Issues / Discussions and the Bitable base. No paid third-party service required — the sync runs on a GitHub Actions workflow plus Bitable outbound automations.

## Direction & responsibility

| Direction | Mechanism | What flows |
|---|---|---|
| GitHub → Bitable | GitHub Actions workflow (`.github/workflows/sync-to-bitable.yml`) | Issue create/edit/close, label add/remove, assignee, comments |
| Bitable → GitHub | Automations A12 + a Bitable outbound webhook | Status `Done`/`Fixed` closes the issue |

## Routing (label-based)

When a GitHub issue is opened, the workflow routes it:

| Label(s) | Target table | Defaults set |
|---|---|---|
| `bug` | Bugs | `Status = New`, `Severity` from label (`severity:s0`…`severity:s3`), default `S2` |
| `enhancement`, `feature` | Features (+ child Tasks of type Feature) | `Status = Idea` |
| `documentation` | Tasks | `Type = Doc` |
| `community`, `question`, `support` | Community Feedback | `Source = GitHub Issue`, `Type = Question` |
| (none of the above) | Tasks | `Type = Feature` (catch-all) |

Multiple labels: first match wins, in the order above.

## Sync key

The GitHub **Issue number** is the sync key. The workflow upserts on `GitHub Issue #` so re-running the workflow on the same issue is idempotent.

## Field mapping

| GitHub | Bitable field |
|---|---|
| `issue.number` | `GitHub Issue #` |
| `issue.html_url` | `GitHub URL` |
| `issue.title` | `Title` |
| `issue.body` | `Description` |
| `issue.assignee.login` | `Assignee` (resolved via `Members.GitHub Handle`) |
| `issue.labels[*].name` | `Tags` (multi-select; severity labels are stripped and routed to `Severity` instead) |
| `issue.state` (`closed`) | `Status = Done` (Tasks) or `Status = Closed` (Bugs) |
| `issue.milestone.number` | `Sprint` (Tasks) — resolved via `Milestones.GitHub Milestone #` |

## Conflict policy

- **GitHub wins** on `Title`, `Description`, `Tags`.
- **Bitable wins** on `Status`, `Priority`, `Sprint`, `Severity`.

If both sides change `Status` at the same time, GitHub's `closed` always lands as `Done` because A11's webhook fires after the close event.

## Required secrets

Set in repo Settings → Secrets:

| Secret | Description |
|---|---|
| `LARK_APP_ID` | App ID of the Lark Custom App with Bitable read/write |
| `LARK_APP_SECRET` | App Secret |
| `LARK_BITABLE_APP_TOKEN` | Bitable Base App Token (from base URL) |
| `LARK_TASKS_TABLE_ID` | `tbl…` ID for Tasks |
| `LARK_BUGS_TABLE_ID` | `tbl…` ID for Bugs |
| `LARK_FEATURES_TABLE_ID` | `tbl…` ID for Features |
| `LARK_FEEDBACK_TABLE_ID` | `tbl…` ID for Community Feedback |
| `LARK_MEMBERS_TABLE_ID` | `tbl…` ID for Members (used to resolve assignee) |

`GITHUB_TOKEN` is built into Actions — no need to set it manually.

## Workflow walkthrough

The workflow (`.github/workflows/sync-to-bitable.yml`) listens to `issues` and `issue_comment` events and POSTs a JSON payload to a small inline script that calls Bitable's Open API:

1. **Authenticate**: `tenant_access_token` from `https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal`.
2. **Resolve target table** by label match.
3. **Resolve assignee**: query `Members` table where `GitHub Handle = {assignee.login}`, take the record ID.
4. **Upsert**: search the target table for a row with `GitHub Issue # = {n}`. If exists → `PUT`; else → `POST`.
5. **Reflect close**: on `issues.closed`, set `Status` to the table's terminal state.

A complete, copy-pasteable YAML lives at [`.github/workflows/sync-to-bitable.yml`](../.github/workflows/sync-to-bitable.yml).

## Bitable → GitHub (A12)

The Bitable automation calls a GitHub REST endpoint via the "Send HTTP Request" action:

```
PATCH https://api.github.com/repos/{owner}/{repo}/issues/{GitHub Issue #}
Authorization: Bearer {github_pat_with_issues_write}
Content-Type: application/json

{ "state": "closed", "state_reason": "completed" }
```

Followed by a `POST .../comments` call with the closing message.

The PAT lives in Bitable as a hidden Constants row (or in Lark's vault if the org has one).

## Testing the sync

1. In a sandbox repo, open an issue titled `Test sync` with label `bug`.
2. Within 60s, a `B-NNNN` row appears in Bugs with the right Title and Assignee.
3. Edit the issue title in GitHub → row title updates.
4. Mark the Bug `Fixed` in Bitable → issue closes on GitHub with the comment from A12.
5. Reopen the issue → row Status flips back to `Triaged`.

If any step fails, check the GitHub Actions run log and Bitable's Automation history (both surface API responses).
