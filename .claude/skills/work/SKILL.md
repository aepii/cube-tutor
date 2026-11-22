---
name: work
description: Take one GitHub issue to a tested change. Pulls the issue with comments, parent and blocked-by links, branches from master, gets the plan approved (with [yours] / [Claude] ownership), builds Claude's part plus failing tests for the user's part, reviews the user's code, runs /verify, then stops with a manual test checklist mapped to the acceptance criteria. Never commits.
disable-model-invocation: true
argument-hint: "<issue number>"
---

# Work: GitHub issue → tested change

Input: `$ARGUMENTS` = an issue number (`#` optional). If it's missing, run `gh issue list --state open --json number,title,labels` and ask which one.

## Hard rules

- **Never commit, push, or open a PR.** This skill ends at a verified working tree plus a test checklist. The user tests by hand, then runs `/pr`.
- **Don't write the user's code.** Pieces tagged **[yours]** in the approved plan are the user's to write (root CLAUDE.md, "Working with the user"). Claude writes their failing tests, signatures, and wiring, and then reviews. If the user is stuck, escalate one step at a time: a hint, then a pointer to the exact docs section, then a slightly bigger example of the pattern. Write the real code only if the user asks for it.
- **The issue's AC define done.** Don't add scope. Note anything out of scope for a follow-up issue instead (see step 6).
- Writes to GitHub (comments, body edits) happen only in step 6, and only after the user agrees to the change.

## 1. Load the issue and its context

```bash
n=<number>
gh issue view $n --json number,title,state,body,labels,comments,url
gh api repos/{owner}/{repo}/issues/$n/dependencies/blocked_by --jq '.[] | {number, title, state}'
gh api repos/{owner}/{repo}/issues/$n/dependencies/blocking   --jq '.[] | {number, title, state}'
gh api repos/{owner}/{repo}/issues/$n/sub_issues              --jq '.[] | {number, title, state}'
gh api repos/{owner}/{repo}/issues/$n/parent --jq '{number, title, body}' 2>/dev/null   # 404 = no parent
```

Also read any issue referenced in the body or comments (`#N`) when it bears on the work. Comments that came later override the body. Read them all.

Stop and report, without branching, if any of these is true:
- The issue is closed.
- A blocked-by issue is still **open**. Show it. Proceed only if the user explicitly says to (per CLAUDE.md: if work depends on something unmerged, ask first).
- **Not ready:** the body has no `### Acceptance criteria` with checkable items, or no `### Test plan`. Suggest `/groom <n>` to refine it.
- `### Open questions` lists anything unresolved and no comment answers it. Ask those questions (AskUserQuestion) before planning.

## 2. Branch from master

```bash
git status --short          # must be clean; if not, stop and ask
git fetch origin master
git switch -c <type>/$n-<short-slug> origin/master
```

`<type>` comes from the label: `enhancement` → `feat`, `bug` → `fix`, `spike` → `spike`, `documentation` → `docs`, otherwise `chore`. If a branch for this issue already exists (`git branch --list "*/$n-*"`), switch to it and resume. Check `git log origin/master..HEAD` and the diff to see what's already done.

The branch's output folder is `.claude-output/<issue#>-<short-slug>/` (the branch name without its type; gitignored, local only; see [`.claude-output/README.md`](../../../.claude-output/README.md)). `/groom` normally left `issue.md` there. If it's missing (an ad-hoc issue, or one groomed before this folder existed), write it now from the loaded issue, in the format `/groom` uses. If a groomed folder has a different slug than the branch, rename the folder to match the branch.

## 3. Read before planning

- The docs the root CLAUDE.md "Docs" map names for every area the issue touches, plus related ADRs.
- `frontend/CLAUDE.md` / `backend/CLAUDE.md` and matching `.claude/rules/*` for touched paths.
- For UI work: `docs/ui.md` if it exists. If it doesn't (`needs:design`), keep styling minimal and consistent with existing screens, and don't introduce a styling library.
- The actual code. Where the issue's *Context* no longer matches the code, note it for the plan.

## 4. Plan, and get approval

Write the full plan to `.claude-output/<issue#>-<slug>/plan.md` first, then present it. The folder is the branch name without its type prefix; see [`.claude-output/README.md`](../../../.claude-output/README.md). Start the file with `# Plan: #<n> <issue title>`, then a line `Status: draft`. Write it **before** entering plan mode, because plan mode blocks edits to any file except its own plan file. The plan covers:

1. **AC → change map:** for each AC, the files to change and how, and the test that proves it.
2. **Key design choices:** one or two sentences each on why. The user must be able to explain them.
3. **Tests first:** for logic (engine, parser, store, auth, SQL, stats), write the failing test before the code.
4. **Deviations:** anything in the issue that's wrong, stale, or needs an AC change. Give a recommendation, not a survey.
5. **Review hotspots:** which files will be **[review closely]**.
6. **Ownership:** tag every piece **[yours]** or **[Claude]** (rules: root CLAUDE.md, "Working with the user"). For each **[yours]** piece, include:
   - **What to build:** the file, the signature/interface Claude will create, and the behavior. Name the failing tests that define done.
   - **Read first:** 1–3 resources. Prefer official docs sections (FastAPI, SQLAlchemy/SQLModel, Postgres, pytest, React, Zustand, Expo), plus a ROADMAP §3 note or an existing file in this repo that shows the pattern.
   - **Skeleton:** a tiny code block (about 3–10 lines) showing the *pattern* or API shape, not the solution. For example, how a context manager or `SELECT … FOR UPDATE SKIP LOCKED` looks in SQLAlchemy, with names that aren't ours.
   - **Gotchas:** 1–3 edge cases the tests will check.
   Infra-only issues have no **[yours]** pieces.

Then enter plan mode (EnterPlanMode). The plan-mode text is a **summary plus the path** to `plan.md`: one line per AC → change, the key design choices, deviations, and the **[yours]** pieces by name. The user reads the full plan in their editor. Exit plan mode for approval. Don't write code until the user approves. If they change the plan in ways that alter the AC, that's a deviation (step 6).

Once approved, fold any changes the user asked for into `plan.md` and switch it to `Status: approved`. If the plan is re-approved later, overwrite it (back to `draft` while it's under review).

## 5. Implement

- **Claude's part first:**
  - All **[Claude]** pieces.
  - For each **[yours]** piece:
    - the **failing tests**
    - the file with its signature and docstring, plus a body that raises `NotImplementedError("yours: <issue#> <piece>")` in Python, or `throw new Error("yours: …")` in TS
    - the wiring that calls it
  Run the tests and confirm that only the **[yours]** tests fail.
- **Then hand over ("your turn"):** write `.claude-output/<issue#>-<slug>/your-turn.md` (heading `# Your turn: #<n> <issue title>`) listing each **[yours]** piece with its file, the tests to make pass, and the command to run them (`uv run pytest -q tests/test_x.py`, `npx jest x`), plus the plan's read-first links, skeleton and gotchas for it. In chat, show the path and one line per piece (file → tests). Then **stop** and wait for the user to say they're done.
- **Review their code** when they say so. Check correctness and edge cases against the AC, idioms and existing patterns, and naming. Tell the user what to change and why; don't rewrite it. Fix their code only when they ask. Repeat until the tests pass and the user is happy, then continue with step 7.
- Stay inside the Scope. Follow existing patterns in the feature folder.
- Keep the AC list as a running checklist (TaskCreate/todo). Tick each one when its test passes.
- Docs ship with the code (root CLAUDE.md "Docs" rules): update the doc that describes changed behavior, and add an ADR for significant choices.
- If the issue has an AC to update ROADMAP §6 (new sub-step letters, stale text), do it now. Ticking ROADMAP checkboxes is `/pr`'s job.

## 6. Deviations and follow-ups

- **The AC must change** (impossible, wrong, or the user changed direction): draft the change as files in the issue folder, then confirm with the user:
  - `deviation.md`: the issue comment that records the decision (`**Scope change:** <what> — **Why:** <reason>`), with no header.
  - `issue.md`: edit the body in place to the proposed version, and append `· Proposed edit (not on GitHub yet)` to its line 3.

  In chat, show the comment (it's short) and a one-line summary of the body change, plus both paths. Once the user agrees, remove the marker from line 3, then post the comment and edit the body so the issue stays the source of truth. `tail -n +5` strips `issue.md`'s 4-line header:
  ```bash
  gh issue comment $n --body-file .claude-output/<issue#>-<slug>/deviation.md
  tail -n +5 .claude-output/<issue#>-<slug>/issue.md | gh issue edit $n --body-file -
  ```
  Then note the change in `plan.md`. If the user rejects it, restore `issue.md`'s body from `gh issue view $n --json body` and delete `deviation.md`.
- **Out-of-scope findings** (bugs, refactors, ideas): don't fix them. List them in the handoff as proposed follow-ups. The user can `/groom` them.

## 7. Verify

Run the `verify` skill (`bash .claude/skills/verify/verify.sh`, timeout 600000). If it fails, fix the problem and rerun the whole script. Don't hand off until it ends with `All checks passed.`

For UI changes, also launch the app (`run` skill) and look at it. Type-checking alone doesn't prove a screen works.

## 8. Hand off and stop

Report, in this order:

1. **Branch:** `<branch>` off `origin/master` @ `<sha>`, uncommitted.
2. **AC status table:** AC → done / changed (with link to the comment) → proven by (test name, or manual step #).
3. **Verify:** each step's PASS/FAIL/SKIP line.
4. **Test by hand:** numbered steps on web (`npm run web`) and/or Expo Go, saying what to do and what should happen. Cover every AC that no automated test proves.
5. **Review hotspots:** files to read closely, one line each. Mark which ones the user wrote.
6. **Follow-ups:** proposed issues for out-of-scope findings, or none.

Write the same report to `.claude-output/<issue#>-<slug>/implementation.md` (heading `# Implementation: #<n> <issue title>`), plus a short **Changes from the plan** section if anything differed from `plan.md`. If the work changes after handoff, update the file.

End with: "Once you've tested it, run `/pr`." Then stop.
