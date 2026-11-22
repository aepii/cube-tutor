# 0006 — Trunk-based branching, release tags, build once and promote by digest

**Status:** accepted (9b, issue #27). Builds on 9a (issue #26: CI, the `master` ruleset).

**Evidence:** ROADMAP §3.11 (stated: branching, environments, workflow table); `.github/workflows/deploy-*.yml`.

## Context
- The app gets a `dev` and a `production` environment on Azure in Phase 23. Before that, the repo needs a way to say *what* goes to each one, and to prove that production runs exactly what was tested.
- This is a solo project, so every extra merge or branch is pure overhead. It's also a portfolio piece, so the flow should be one that teams actually use and that's easy to explain.
- Since 9a, `master` only changes through PRs that pass CI.

## Decision
- **Trunk-based:** short-lived feature branches merge into `master`. There are no long-lived `dev`, `prod` or release branches.
- **`master` = dev.** Every push to `master` builds the backend image **once**, pushes it to GHCR as `:<commit sha>`, and deploys it to `dev` by digest.
- **A release = a tag.** Publishing a GitHub Release `vX.Y.Z` on a `master` commit deploys that commit's existing image to `production`, **by digest**, after the owner approves (GitHub environment protection, limited to `v*` tags). The `:vX.Y.Z` image tag is added to the same digest only after a successful deploy.
- **Rollback = redeploy an earlier release** (re-run its `Deploy production` run).

## Alternatives
- **A long-lived `prod` branch (or `dev` + `prod`, GitFlow).** Rejected:
  - Long-lived branches drift and need merge-backs.
  - Every change would take two PRs.
  - "What's in prod?" becomes a branch diff instead of a tag.
  - If a branch is ever wanted, only `deploy-prod.yml`'s trigger changes.
- **Rebuild the image for each environment.** Rejected: the production image wouldn't be the artifact that ran in dev. Base images, dependency resolution or build tools can change between two builds of the same commit.
- **Promote by tag (`:latest`, `:dev`, `:prod`).** Rejected: tags are mutable, so a push between "tested" and "deployed" changes what ships. Digests are content addresses and can't change.
- **Build on the PR and push from there.** Rejected: the merge commit isn't the PR head commit. Images built for PRs would also fill the registry with code that never shipped.

## Consequences
- Every commit on `master` has an image, so any of them can be released or rolled back to. Old `:<sha>` images pile up in GHCR, and a retention policy will be needed eventually.
- A release can't be cut from a commit that `deploy-dev` never built (for example, from before 9b). `deploy-prod` fails early with a clear message.
- Production deploys need a human approval, and a re-run for rollback needs one too.
- In Phase 23, `deploy.yml` only gains the Azure steps. The triggers, environments and digest handoff stay as they are.
