# Azure infrastructure

What runs on Azure, how it gets there, and who may change it. Bicep is in [`infra/`](../infra/) (runbook: [`infra/README.md`](../infra/README.md)). Why Container Apps + Bicep + managed-identity OIDC: [ADR 0007](decisions/0007-azure-container-apps-bicep.md). Pipeline: [ci-cd.md](ci-cd.md).

Status (23b): the backend image runs on Container Apps in `dev` (every merge to `master`) and `prod` (every approved release). Each deploy runs migrations as a Container Apps Job first, and the app reads its secrets from Key Vault. The Static Web App is still empty until 23c.

## Two templates, two runners

| Template | Scope | Creates | Runs as | When |
|---|---|---|---|---|
| `infra/bootstrap.bicep` | subscription | budget, 3 resource groups, shared Postgres + 2 databases, 2 deploy identities + federated credentials + their RBAC, the owner's Key Vault Secrets Officer | the subscription **Owner**, from Cloud Shell | once (re-runs are no-ops) |
| `infra/main.bicep` + `{dev,prod}.bicepparam` | one resource group | everything per environment (below) | that environment's **deploy identity**, via GitHub OIDC | every `deploy.yml` run |

Why the split: the deploy identities can't create themselves, and limiting each identity to its own resource group means it can't create the budget, the resource groups, or the shared server either. Those are created once by a human who has Owner.

## Resource map

`centralus` for everything (the subscription's allowed regions: `westus3`, `centralus`, `canadacentral`, `northcentralus`, `belgiumcentral`). Postgres can be moved alone with the bootstrap's `postgresLocation` parameter if a student subscription refuses it there. Static Web Apps Free is offered in `centralus`; check that again if the region ever changes.

**`rg-cubetutor-shared`** (bootstrap)

| Resource | Name | Notes |
|---|---|---|
| Postgres Flexible Server | `psql-cubetutor-<6 chars>` | B1ms Burstable, Postgres 18, 32 GB, no HA / geo-backup; password auth; public access + "allow Azure services" rule |
| Postgres databases | `cubetutor_dev`, `cubetutor_prod` | one server for both: only one B1ms is free |
| Managed identity | `id-cubetutor-deploy-dev` | GitHub deploys to dev + PR what-if |
| Managed identity | `id-cubetutor-deploy-prod` | GitHub deploys to production |

**Subscription:** budget `budget-cubetutor` (see Cost guardrails).

**`rg-cubetutor-<env>`** (`main.bicep`; `az resource list -g rg-cubetutor-dev -o table` should list exactly these)

| Type | Name | Notes |
|---|---|---|
| `Microsoft.ManagedIdentity/userAssignedIdentities` | `id-cubetutor-api-<env>` | the `api` app's identity |
| `Microsoft.OperationalInsights/workspaces` | `log-cubetutor-<env>` | Container Apps logs; 30-day retention, 0.15 GB/day cap |
| `Microsoft.Insights/components` | `appi-cubetutor-<env>` | workspace-based App Insights (used from 23c) |
| `Microsoft.KeyVault/vaults` | `kv-cubetutor-<env>-<6 chars>` | RBAC mode, soft delete 7 days, purge protection off |
| `Microsoft.Storage/storageAccounts` | `stcubetutor<env><8 chars>` | Standard LRS, no public blob access, shared keys off, TLS 1.2 |
| `Microsoft.App/managedEnvironments` | `cae-cubetutor-<env>` | workload-profiles environment, Consumption profile only |
| `Microsoft.App/containerApps` | `ca-cubetutor-api-<env>` | the backend image by digest on port 8000, external HTTPS ingress, 0–2 replicas (HTTP scale rule, 10 concurrent requests each), 0.25 vCPU / 0.5 GiB, probes on `/health/*` |
| `Microsoft.App/jobs` | `caj-cubetutor-migrate-<env>` | manual trigger, `alembic upgrade head && python -m seed.seed_algorithms`, 10-minute replica timeout, no retries |
| `Microsoft.Web/staticSites` | `swa-cubetutor-<env>` | Free plan, empty until 23c |

Azure may add a Smart Detection action group / alert rule for App Insights on its own; those aren't from the template.

**Naming:** `<type>-cubetutor-<env>` using the [Azure abbreviations](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations). Storage, Key Vault and Postgres names are global DNS names, so they end in a `uniqueString` suffix. The suffix is stable per resource group (or subscription), so re-deploys keep the same names. Every resource is tagged `app=cubetutor`, `env=<env>`.

## Identities and RBAC

No secret is stored anywhere. GitHub Actions asks GitHub for an OIDC token, and Entra ID exchanges it for an Azure token. It does so only if the token's `sub` matches a **federated credential** on the identity.

| Identity | Federated credential subjects | Roles | Scope |
|---|---|---|---|
| `id-cubetutor-deploy-dev` | `repo:aepii/cube-tutor:environment:dev`, `repo:aepii/cube-tutor:pull_request` | Contributor; RBAC Administrator **(conditional)** | `rg-cubetutor-dev` |
| `id-cubetutor-deploy-prod` | `repo:aepii/cube-tutor:environment:production` | Contributor; RBAC Administrator **(conditional)** | `rg-cubetutor-prod` |
| `id-cubetutor-api-<env>` (the `api` app **and** the migration job) | — | Key Vault Secrets User | that env's Key Vault |
| | | Storage Blob Data Contributor | that env's storage account |
| you (the user who ran the bootstrap) | — | Key Vault Secrets Officer | `rg-cubetutor-dev`, `rg-cubetutor-prod` |

- **Environment-scoped subjects.** A token for `environment:dev` exists only in a job running in the `dev` GitHub environment, which only `master` may use. A `production` token requires a `v*` tag **and** the owner's approval. So the GitHub environment rules ([ci-cd.md](ci-cd.md#environments)) are what guard Azure.
- **The `pull_request` subject (dev only)** lets `infra-whatif.yml` log in on PRs, which can't use the `dev` environment. The trade-off: anyone who can push a branch to this repo can act as the dev deployer. In this solo repo that's the owner, who can already merge to `master`. Fork PRs get no OIDC token from GitHub, so they can't use it. Prod has no such credential.
- **Conditional RBAC Administrator.** Contributor can't create role assignments, but `main.bicep` has to grant the `api` identity its two roles. RBAC Administrator does that, limited by an ABAC condition (`infra/modules/bootstrap/rgRoles.bicep`): it may create or delete assignments only for **Key Vault Secrets User** and **Storage Blob Data Contributor**, and only to **service principals** (managed identities). So the deploy identity can't make anything Owner, give itself more rights, or grant a user anything. When the template needs a new role, add its ID to that list and re-run the bootstrap.
- **Deploy identities live in the shared group**, so Contributor on its own environment's group can't delete or re-point the identity it logs in with. Nothing is granted at subscription scope. A deploy identity can't see the other environment or the other project in this subscription.
- **Same image, own identity:** the `api` identity is separate from the deploy identity. The running app can read secrets and blobs, but can't change infrastructure. The migration job runs as the `api` identity too, so it needed no new role through the deploy identity's condition.
- **Your Key Vault Secrets Officer.** Owner can't read or write secrets in an RBAC-mode vault, so the bootstrap gives the person running it (`ownerPrincipalId`) Secrets Officer on the two environment groups. The deploy identity can't remove it: its condition only covers service-principal assignments. Nothing in a workflow can write secrets.

## Secrets

| Key Vault secret | Container Apps secret | Env var | Value |
|---|---|---|---|
| `database-url` | `database-url` | `DATABASE_URL` | `postgresql://cubetutor_<env>_app:<pw>@<server>:5432/cubetutor_<env>?sslmode=require` |
| `secret-key` | `secret-key` | `SECRET_KEY` | `openssl rand -hex 32` |

- **Set once by the owner** in Cloud Shell ([runbook step 6](../infra/README.md#6-create-the-app-database-users-and-secrets-once-per-environment)), along with rotation. No workflow generates or rotates them: the deploy identity has no data-plane access to the vault.
- **Key Vault references:** the `api` app and the migration job declare each secret as `{ keyVaultUrl: <vault>/secrets/<name>, identity: <api identity> }`. Container Apps fetches it as that identity. The value is never in Bicep, the deployment history or `az containerapp show`. The URLs carry no version, so a new value is picked up within ~30 minutes, or on a revision restart.
- **A missing secret fails the deploy** at the first Bicep step, before anything changes.
- `CORS_ORIGINS` is a plain env var: `https://<Static Web App default hostname>`. PR preview origins come in 23c.
- **One database role per environment.** `cubetutor_<env>_app` owns only `cubetutor_<env>`. `CONNECT` is revoked from `PUBLIC` on both databases, so the dev role can't connect to the prod database. The admin login isn't in any app config. Postgres requires TLS (`sslmode=require`).

## How it's deployed

- `deploy.yml` (dev on every merge to `master`, production on an approved release). It checks out the commit being deployed (for a release, the tagged commit, so infra and image match) and logs in with `azure/login` (OIDC). Then, in order; a failed step stops the run:
  1. **Bicep, pass 1:** `az deployment group create -g rg-cubetutor-<env> --parameters infra/<env>.bicepparam` with `migrateImage=<new digest>` and `apiImage=<the image api runs now>`. The job moves to the new image; `api` doesn't change. Incremental mode: re-runs converge, and nothing outside the template is deleted.
  2. **Migrate:** [`infra/scripts/run-migration.sh`](../infra/scripts/run-migration.sh) starts one job execution and polls it (15-minute limit). If it fails, the script prints the execution's console logs from Log Analytics and exits 1. `api` still runs the old revision.
  3. **Bicep, pass 2:** the same deployment with `apiImage=<new digest>`. Container Apps creates a new revision and moves traffic once it's ready (Single revision mode).
  4. **Smoke test:** waits until the latest revision runs the new digest and is the latest ready one, then `GET /health/ready` returns 200. It backs off for up to ~3 minutes to cover a cold start.
- **Why the running image in pass 1:** `apiImage` defaults to the placeholder. Without reading it, every deploy would briefly roll `api` back. On a fresh environment (no app yet) the placeholder is used, which listens on port 80 and has no probes (`main.bicep` switches both on `apiImage`).
- `infra-whatif.yml` runs on PRs touching `infra/**`. It previews the same deployment against **dev** and keeps one PR comment up to date. It can't preview prod, because the dev identity has no access there. Prod differs from dev only in names and the parameter file.
- `infra-whatif.yml` also passes the image dev runs now as `apiImage`, so the preview shows only real changes.

### Probes and scaling

| Probe | Path | Settings | Why |
|---|---|---|---|
| Startup | `/health/live` | every 3 s, 40 failures (~2 min) | cold start from 0 replicas |
| Liveness | `/health/live` | every 30 s, 3 failures | restart a hung process |
| Readiness | `/health/ready` | every 10 s, 3 s timeout, 3 failures | a database outage takes replicas out of rotation instead of serving 500s |

Scale: min 0, max 2, HTTP rule at 10 concurrent requests per replica. After a few idle minutes `api` has 0 replicas, and the next request cold-starts one.

### The migration rule (expand → deploy → contract)

The old `api` revision keeps serving while the migration job runs on the new image, and for a moment after. So **every migration must work with the code that's running before it**:

1. **Expand:** add tables, nullable columns, or columns with defaults; backfill data. The old code ignores them.
2. **Deploy** the code that uses them.
3. **Contract** in a later deploy: drop or rename what the old code needed, once no running revision uses it.

Never rename or drop a column in the same deploy as the code change. The seed runs in the job on every deploy, so it has to stay idempotent. See also [`backend/CLAUDE.md`](../backend/CLAUDE.md#changing-the-schema).

## Cost guardrails

Target: ≈$0–2/month in year one (ROADMAP §3.12).

- **Budget** `budget-cubetutor`: $5/month, filtered to the three `rg-cubetutor-*` resource groups (the subscription is shared), email at **80% actual** and **100% forecast**. It's created first in the bootstrap. On *Azure for Students* the $100 credit already has a hard spending limit, so the budget is an early warning that credit is burning, not protection from a bill.
- `api` min replicas **0**: an idle app costs nothing and stays within the monthly free grant. The migration job only bills while it runs (seconds per deploy).
- Log Analytics **daily cap 0.15 GB** (≈ the 5 GB/month free allowance) and 30-day retention.
- Postgres B1ms + 32 GB storage: free for 12 months. Then ≈$12–15/month, or move to Neon or Supabase.
- No Azure Container Registry: images come from GHCR, which is free.

## Known limits (demo choices)

- **Postgres is reachable from any Azure IP** (the 0.0.0.0 "allow Azure services" rule). Any tenant's Azure resources can reach the port, so the password is the only barrier. The production answer is a VNet-integrated Container Apps environment plus private access for Postgres. That costs money, so it isn't planned.
- Key Vault and storage also have public network access, with authentication through Entra ID only.
- Key Vault purge protection is off, so teardown and re-create work. Turn it on for real data. It can't be turned off again.
