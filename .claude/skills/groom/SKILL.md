---
name: groom
description: Turn the next ROADMAP sub-step (or a new idea, bug, or spike) into 1–3 ready GitHub issues with scope, acceptance criteria, test plan, labels, and blocked-by / sub-issue links. Drafts first; creates nothing until the user approves.
disable-model-invocation: true
argument-hint: "<ROADMAP step like 4a | Phase 4 | free-form idea or bug>"
---

# Groom: ROADMAP → GitHub issues

ROADMAP.md is the strategy doc and keeps changing. Issues are **just-in-time specs**: groom only the next 1–3 units of work, never a whole phase "for later". One issue = one PR = one branch from `master`.

Input: `$ARGUMENTS`, which is a ROADMAP sub-step (`4a`), a phase (`Phase 4`), or a free-form idea, bug, or spike. If it's empty, propose the next unstarted sub-step(s) from the ROADMAP §6 "Recommended order", skipping ones that already have an open issue, and confirm with the user.

## Hard rule

Read-only until the user approves the drafts. Don't run `gh issue create`, `gh issue edit`, `gh label create`, or any `gh api` write before that. The only file grooming writes is each created issue's `.claude-output/<issue#>-<slug>/issue.md` (step 4). Grooming doesn't edit ROADMAP.md either. ROADMAP changes ship in a PR (see step 4).

## 1. Check what exists

```bash
gh issue list --state all --limit 50 --json number,title,state,labels
```

- If an issue already covers the request, show it and ask whether to refine it (edit its body) instead of creating a duplicate.
- Note open issues the new work depends on. They become blocked-by links.

## 2. Research (before drafting)

1. **ROADMAP.md:** the named §6 phase/sub-step, its *Builds on* / *Done when*, its review tag, and every § it references (e.g. §3.x design decisions, §4.1 bug numbers).
2. **Docs:** the doc(s) the root CLAUDE.md "Docs" map names for this area, plus related ADRs in `docs/decisions/`.
3. **Code:** the files the work will touch. Confirm the roadmap's description still matches the code. The roadmap is often stale; trust the code, and flag differences.
4. **Prerequisites:** check whether each *Builds on* item is actually merged on `master`, not just ticked.
5. **UI work:** if the issue changes screens or components and `docs/ui.md` doesn't exist yet, add the `needs:design` label and say in Notes that styling should stay minimal and follow existing patterns until the design-direction spike lands.

## 3. Draft

Split the request into units of **one reviewable PR each**. Split when one part is a prerequisite for another, when parts need different review levels, or when one diff would be too big to review in one sitting. Prefer the ROADMAP's existing sub-step letters. If a phase has no sub-steps and needs a split, propose the letters (they get written into ROADMAP §6 by the first PR of that phase).

Per issue, write a title and body in exactly this shape. The headings match `.github/ISSUE_TEMPLATE/feature.yml`, and `/work` parses them.

```markdown
### Context
Why this exists and what it unblocks. Link: ROADMAP §6 Phase N / sub-step Na (and §x.y design notes). Current state in the code, with paths.

### Scope
- Concrete changes, each one line. Name files/modules where known.

### Out of scope
- Things a reasonable implementer might also do here but must not (and where they belong instead, e.g. "→ 4e").

### Acceptance criteria
- [ ] AC1: Observable and testable. Use Given/When/Then for behavior ("Given an expired access token, when a request returns 401, then the client refreshes once and retries").
- [ ] AC2: …
- [ ] Docs: <doc path> updated for <what> (or "no doc change: <reason>")

### Test plan
- **Automated:** which jest/pytest tests to add or extend, and which identities/edge cases they cover.
- **Manual:** what the user will click through on web and/or Expo Go.

### Dependencies
- Blocked by: #N (title) / none
- Parent: #N / none

### Open questions
- Decisions the user must make before or during `/work` (or "none").

### Notes
Implementation hints, gotchas, relevant ADRs, review level (**[review closely]** on X / **[review diff]**).
```

AC quality bar. Every AC must be checkable by a test or by one concrete manual step. Avoid "works well", "is clean", "is robust". Keep it to 3–8 AC per issue; more means the issue should be split.

**Spikes** (design direction, library choice, research) use the same shape. Their AC are *decisions and artifacts* (e.g. "ADR written in `docs/decisions/` choosing X, with alternatives", "2–3 clickable directions shown, one chosen"), not production code.

**Labels** (pick all that apply):
- Type: `enhancement` (feature), `bug`, `chore` (refactor/infra/tooling), `spike`, `documentation`
- Review: `review:closely` or `review:diff` (from the ROADMAP tag)
- Area: `area:frontend`, `area:engine`, `area:backend`, `area:worker`, `area:infra`
- Phase: `phase:N` (create it if missing, see step 4)
- `needs:design` (see 2.5)

Show the user every draft in chat (title, labels, body), plus a one-line dependency graph, e.g. `#A 4a → #B 4b, #C 4c`. Then list open questions. If an open question changes the scope, ask it with AskUserQuestion before finalizing. Wait for approval or edits.

## 4. Create (after approval only)

Write each body to the session scratchpad, then:

```bash
gh label create "phase:N" --color BFD4F2 --description "ROADMAP phase N" 2>/dev/null || true
gh issue create --title "<Na: title>" --body-file <scratchpad>/issue-Na.md --label "enhancement,review:diff,area:backend,phase:N"
```

Title format: `<sub-step>: <imperative summary>` for ROADMAP work (`4a: Add pytest suite and ruff config`); just the summary for ad-hoc issues.

Link dependencies with the REST API. It takes the blocker's / child's **database id**, not its number:

```bash
id=$(gh api repos/{owner}/{repo}/issues/<blocker#> --jq .id)
gh api -X POST repos/{owner}/{repo}/issues/<blocked#>/dependencies/blocked_by -F issue_id=$id
# parent/child (e.g. a phase tracking issue with sub-step children):
cid=$(gh api repos/{owner}/{repo}/issues/<child#> --jq .id)
gh api -X POST repos/{owner}/{repo}/issues/<parent#>/sub_issues -F sub_issue_id=$cid
```

If a link call fails, keep the `Blocked by: #N` line in the body (it's always there anyway) and report the failure. Don't retry in a loop.

**Save each created issue** to `.claude-output/<issue#>-<slug>/issue.md`. `<slug>` is the short kebab-case slug `/work` will use for the branch (`<type>/<issue#>-<slug>`), so the folders match; see [`.claude-output/README.md`](../../../.claude-output/README.md). File contents:

```markdown
# Issue: #<n> <title>

<URL> · Labels: <labels> · Blocked by: #… / none · Parent: #… / none

<the body exactly as created>
```

The folder is gitignored (local only), so it doesn't matter which branch you're on. If a body is edited later (a refinement or a scope change), update its `issue.md` too.

Only create a parent "Phase N" tracking issue if the user asks for one. Usually the `phase:N` label is enough.

If the drafts proposed new sub-step letters or found ROADMAP text that is stale, add an AC to the first issue: `- [ ] ROADMAP §6 updated: <what>`.

## 5. Report

List each created issue: `#N <title>`, URL, labels, links. End with the suggested next command: `/work <first unblocked issue#>`.
