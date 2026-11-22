# .claude-output

A local record of what Claude planned, built and proposed for each unit of work: issue drafts and snapshots, plans, handoffs, PR and commit drafts, plus learning guides. **Gitignored:** only this README is tracked, so everyone gets the same conventions. The files live on your machine and survive across sessions and branch switches, but never go into a commit or PR.

`docs/` describes the system as built. GitHub issues and PRs stay the source of truth for scope and review. This folder is a working copy of what was said, for reading back later.

## Layout

```
.claude-output/
  README.md                        tracked: these conventions
  guides/                          learning material, not tied to one issue
    phases-4-9-23.md
  drafts/                          /groom issue drafts that have no number yet
    <step-or-short-slug>.md        e.g. 4a.md; moved to <issue#>-<slug>/issue.md once created
  <issue#>-<slug>/                 one folder per issue/branch
    issue.md                       the issue as created (and as later edited)
    plan.md                        the plan (Status: draft while under review, then approved)
    your-turn.md                   the [yours] pieces handed to the user
    deviation.md                   a proposed scope-change comment
    implementation.md              the handoff report
    pr.md                          the PR title and description
    commit.md                      the proposed commit message
```

**Folder name:** the branch name without its type prefix. Branch `chore/42-web-swa-previews-telemetry` → `.claude-output/42-web-swa-previews-telemetry/`. Issue numbers keep the folders in order; the slug says what it was.

## Who writes what

| File | Written by | When | Contents |
|---|---|---|---|
| `drafts/<step-or-slug>.md` | `/groom` step 3 | before the drafts are shown for approval | 4-line header (`# Draft: <title>`, blank, `Labels: … · Blocked by: … · Parent: …`, blank), then the issue body. The issue is created from it (`tail -n +5`); then it moves to `issue.md` and is deleted. |
| `issue.md` | `/groom` step 4 (or `/work` step 2 if missing) | right after `gh issue create` | Title, URL, labels, links, and the body as created. Updated when the body is edited (refinement, scope change). During a `/work` scope change it holds the proposed body, marked `Proposed edit (not on GitHub yet)` on line 3 until it's applied. |
| `plan.md` | `/work` step 4 | when the plan is presented (`Status: draft`), then on approval (`Status: approved`) | Context, AC → change map, key design choices, deviations, review hotspots, ownership. Overwritten if the plan is re-approved after changes. |
| `your-turn.md` | `/work` step 5 | at the "your turn" handover | Each **[yours]** piece: file, tests to pass, command to run them, read-first links, skeleton, gotchas. |
| `deviation.md` | `/work` step 6 | when a scope change is proposed | The exact issue comment (`**Scope change:** … — **Why:** …`), posted with `--body-file` once the user agrees. |
| `implementation.md` | `/work` step 8 | at handoff | Branch + base SHA, AC status table, verify results, manual test steps, review hotspots, follow-ups, changes from the plan. Updated if the work changes after handoff. |
| `pr.md` | `/pr` step 4 | when the draft is shown to the user | Line 1 `<!-- title: <PR title> -->` (GitHub doesn't render it), then the exact PR body. `gh pr create --body-file` takes the file as is. |
| `commit.md` | `/pr` step 1 | when there are uncommitted changes | The exact commit message, ending with the `Co-Authored-By` line. Used with `git commit -F`. |

- **Drafts live here, not in chat.** Anything the user has to review or approve is written to a file first. Chat shows a summary plus the path, so the user reads it in their editor and can point another session at it. Short items (under ~10 lines, such as a commit message or a scope-change comment) are shown in full as well. Nothing is created or posted without approval, as before.
- Because the folder is ignored, it never shows up in `git status`, and the clean-tree checks are unaffected. `/groom` can write folders for issues that haven't started yet.
- Scope changes still go to the issue (comment + body edit). These files mirror them; the issue stays the source of truth for AC.
- No secrets, tokens or connection strings, even though it's local.
