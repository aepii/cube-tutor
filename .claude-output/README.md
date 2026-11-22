# .claude-output

A local record of what Claude planned, built and proposed for each unit of work: issue snapshots, plans, handoffs, PR drafts, plus learning guides. **Gitignored:** only this README is tracked, so everyone gets the same conventions. The files live on your machine and survive across sessions and branch switches, but never go into a commit or PR.

`docs/` describes the system as built. GitHub issues and PRs stay the source of truth for scope and review. This folder is a working copy of what was said, for reading back later.

## Layout

```
.claude-output/
  README.md                        tracked: these conventions
  guides/                          learning material, not tied to one issue
    phases-4-9-23.md
  <issue#>-<slug>/                 one folder per issue/branch
    issue.md                       the issue as created (and as later edited)
    plan.md                        the plan the user approved
    implementation.md              the handoff report
    pr.md                          the PR title and description
```

**Folder name:** the branch name without its type prefix. Branch `chore/42-web-swa-previews-telemetry` → `.claude-output/42-web-swa-previews-telemetry/`. Issue numbers keep the folders in order; the slug says what it was.

## Who writes what

| File | Written by | When | Contents |
|---|---|---|---|
| `issue.md` | `/groom` step 4 (or `/work` step 2 if missing) | right after `gh issue create` | Title, URL, labels, links, and the body as created. Updated when the body is edited (refinement, scope change). |
| `plan.md` | `/work` step 4 | when the user approves the plan | Context, AC → change map, key design choices, deviations, review hotspots. Overwritten if the plan is re-approved after changes. |
| `implementation.md` | `/work` step 8 | at handoff | Branch + base SHA, AC status table, verify results, manual test steps, review hotspots, follow-ups, changes from the plan. Updated if the work changes after handoff. |
| `pr.md` | `/pr` step 4 | when the draft is shown to the user | Line 1 `<!-- title: <PR title> -->` (GitHub doesn't render it), then the exact PR body. `gh pr create --body-file` takes the file as is. |

- Because the folder is ignored, it never shows up in `git status`, and the clean-tree checks are unaffected. `/groom` can write folders for issues that haven't started yet.
- Scope changes still go to the issue (comment + body edit). These files mirror them; the issue stays the source of truth for AC.
- No secrets, tokens or connection strings, even though it's local.
