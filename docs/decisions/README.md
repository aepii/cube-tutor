# Architecture decision records

Short records of significant choices, written **after the fact** from evidence in the code, git history and [`ROADMAP.md`](../../ROADMAP.md). Each one has Context, Decision, Alternatives and Consequences.

**Inferred** marks rationale that isn't stated anywhere in the repo and was reconstructed from the code. Treat it as a hypothesis, not a record.

| # | Decision | Evidence |
|---|---|---|
| [0001](0001-expo-single-codebase.md) | Expo + react-native-web for one web/mobile codebase | Project goal stated in `CLAUDE.md`; created with `create-expo-app` |
| [0002](0002-zustand-state.md) | Zustand for client state | Commit `915c94a` replaced an `AuthProvider` context; rationale not stated |
| [0003](0003-sticker-model-engine.md) | Sticker-model cube engine instead of face arrays / cubies | ROADMAP §3.1, §3.2 (stated) |
| [0004](0004-celery-redis-worker.md) | Celery + Redis for background work (**superseded** by [0008](0008-service-bus-jobs.md); removed in #39) | Commit `bf3d73c`; ROADMAP §5, §3.10 (stated) |
| [0005](0005-one-python-package-uv.md) | One Python package + image for API and worker (three commands), managed by uv | Issue #18; ROADMAP §4.1 #6, §4.2, §3.11 (stated) |
| [0006](0006-trunk-based-release-tags.md) | Trunk-based branching + release tags; build the image once, promote by digest | Issues #26, #27; ROADMAP §3.11 (stated) |
| [0007](0007-azure-container-apps-bicep.md) | Azure Container Apps + Bicep; GitHub OIDC through user-assigned managed identities with conditional RBAC | Issue #29; ROADMAP §3.9, §3.11, §3.12 (stated) |
| [0008](0008-service-bus-jobs.md) | Background jobs: a `Job` table + a direct Azure Service Bus consumer behind a `JobQueue` interface (supersedes 0004) | Issues #54, #55; ROADMAP §3.10 (stated) |
