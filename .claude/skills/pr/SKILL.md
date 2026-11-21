---
name: pr
description: Prepare a pull request for a finished change the user has tested locally. Checks that the branch comes straight off master (not stacked), then drafts the PR description. Never commits, pushes, or opens the PR without the user's explicit go-ahead.
disable-model-invocation: true
---

# PR workflow

Use this only after the user has tested the change locally and said so.

## Hard rule

**Don't commit, push, or run `gh pr create` until the user explicitly says to in this session**, after they've seen the draft. Invoking `/pr` is not that go-ahead. Read-only commands (`git status`, `log`, `diff`, `fetch`, `branch`, `gh pr list/view`) are fine.

## 1. Check the branch

```bash
git fetch origin master
git branch --show-current
git status --short
git log --oneline origin/master..HEAD
git merge-base --is-ancestor origin/master HEAD && echo "up to date with master" || echo "BEHIND master"
# Other branches whose tips are inside this branch but not in master = stacked
for b in $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes/origin); do
  case "$b" in master|origin/master|origin/HEAD|origin|"$(git branch --show-current)"|origin/"$(git branch --show-current)") continue;; esac
  git merge-base --is-ancestor "$b" HEAD && ! git merge-base --is-ancestor "$b" origin/master && echo "STACKED ON: $b"
done
gh pr list --head "$(git branch --show-current)" --state all --json number,state,baseRefName
```

Stop and report to the user, without drafting anything, if any of these is true:
- The current branch is `master`. Work needs its own branch.
- Any `STACKED ON:` line appears. Stacked PRs on this repo merged into stale bases (PRs #2–#5 had to be re-landed). Offer to rebase onto `origin/master`, but only after the user agrees.
- An existing PR for this branch has a base other than `master`.

Also report these, but you can keep drafting:
- The branch is behind `master`. Suggest a rebase.
- There are uncommitted changes. List them and propose a commit message ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Don't commit yet.

## 2. Gather the evidence

- **Linked issue.** Branches made by `/work` are named `<type>/<issue#>-<slug>`. Take the number from the branch name (or ask the user if there isn't one) and load it with `gh issue view <n> --json number,title,body,comments`. Comments recording a scope change override the body. Check every acceptance criterion against the diff. An AC that isn't met and wasn't changed by agreement (no issue comment recording it) **stops the PR**. Report it instead of drafting.
- `git diff --stat origin/master...HEAD` (plus uncommitted changes) to list the changed files.
- Run the `verify` skill (`bash .claude/skills/verify/verify.sh`) unless it already passed on this exact tree in this session. A failure stops the PR.
- Check the ROADMAP.md §6 phase tags (**[review closely]** / **[review diff]**) and tick the checkboxes this change completes.

## 3. Docs check

The root CLAUDE.md "Docs" section maps code areas to docs. For each changed file:

1. **Area has a doc.** If the change alters behavior that the doc describes (or should describe), the doc must change in this PR. Reread the relevant sections against the new code. Look for: renamed or moved files the doc links to, changed flows, new endpoints/tables/stores/gestures, resolved or new "Open question:" items.
2. **New feature.** Add a section to the relevant doc, or a new doc in `docs/` plus a pointer line in the CLAUDE.md Docs section if it fits none of the existing ones. Describe what is built, never plans.
3. **New significant choice** (a framework, a data model, a storage or queue, a protocol, or reversing an earlier choice). Add an ADR in `docs/decisions/` (Context, Decision, Alternatives, Consequences; mark inferred rationale) and a row in its README. If it reverses an existing ADR, mark that one superseded and link the new one.
4. **Links still resolve.** Check every relative link in `docs/` still points at an existing file (renames break them silently).

Stop and fix before drafting if a doc is now wrong. "No doc change needed" is allowed only with a one-line reason, which goes in the PR description.

## 4. Draft the description

Title: the issue title (e.g. `4a: Add pytest suite and ruff config`). Leave out `Closes #` only if the branch has no issue. Show the title and body to the user in chat, and write the body to the session scratchpad for `--body-file`. Use exactly these sections:

```markdown
Closes #<issue>

## Summary
What changed and why, 2–5 bullets. Briefly explain the key design choices, since the user has to be able to talk about them.

## Acceptance criteria
The issue's AC as a checklist, each ticked with how it's proven (test name or manual step #). Changed AC: link the issue comment that records the change.

## How it was verified
The verify-skill result per step (tsc, jest with test count, lint, web/android export, backend checks or "none configured"), plus any new or changed tests.

## What to check by hand
Numbered, concrete steps on web and on a phone (Expo Go): what to do, what should happen.

## Close review vs skim
**Close review (core logic, be ready to explain in an interview):** file — one line on what to understand.
**Skim:** file — why it's routine (wiring, styling, config, renames).

## Docs
Docs and ADRs updated or added (path — what changed), or "No doc change: <reason>".

## Base/stack notes
Base: `master` @ <short sha>. Not stacked / depends on <…>. Rebased: yes/no.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

How to sort files into close review vs skim: the cube engine, parser, turn/playback store logic, input/turn math, auth/token logic, and anything else that encodes a rule or algorithm go under close review. Components that only wire things up, styles, config, and generated or mechanical changes go under skim.

## 5. Wait for the go-ahead

End with the exact commands that would run, and don't run them:

```bash
git push -u origin <branch>
gh pr create --base master --head <branch> --title "<title>" --body-file <scratchpad>/pr-body.md
```

Run them (plus any commit you proposed) only after the user says to. Then report the PR URL.
