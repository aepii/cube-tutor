# Azure infrastructure

What runs on Azure, how it gets there, and who may change it. Bicep is in [`infra/`](../infra/) (runbook: [`infra/README.md`](../infra/README.md)). Why Container Apps + Bicep + managed-identity OIDC: [ADR 0007](decisions/0007-azure-container-apps-bicep.md). Pipeline: [ci-cd.md](ci-cd.md).

Status (23a): the platform exists in `dev` and `prod`, but nothing of ours runs on it yet. The `api` Container App serves a public placeholder image until 23b.

## Two templates, two runners

| Template | Scope | Creates | Runs as | When |
|---|---|---|---|---|
| `infra/bootstrap.bicep` | subscription | budget, 3 resource groups, shared Postgres + 2 databases, 2 deploy identities + federated credentials + their RBAC | the subscription **Owner**, from Cloud Shell | once (re-runs are no-ops) |
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
| `Microsoft.App/containerApps` | `ca-cubetutor-api-<env>` | external HTTPS ingress, 0–2 replicas, 0.25 vCPU / 0.5 GiB |
| `Microsoft.Web/staticSites` | `swa-cubetutor-<env>` | Free plan, empty until 23c |

Azure may add a Smart Detection action group / alert rule for App Insights on its own; those aren't from the template.

**Naming:** `<type>-cubetutor-<env>` using the [Azure abbreviations](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations). Storage, Key Vault and Postgres names are global DNS names, so they end in a `uniqueString` suffix. The suffix is stable per resource group (or subscription), so re-deploys keep the same names. Every resource is tagged `app=cubetutor`, `env=<env>`.

## Identities and RBAC

No secret is stored anywhere. GitHub Actions asks GitHub for an OIDC token, and Entra ID exchanges it for an Azure token. It does so only if the token's `sub` matches a **federated credential** on the identity.

| Identity | Federated credential subjects | Roles | Scope |
|---|---|---|---|
| `id-cubetutor-deploy-dev` | `repo:aepii/cube-tutor:environment:dev`, `repo:aepii/cube-tutor:pull_request` | Contributor; RBAC Administrator **(conditional)** | `rg-cubetutor-dev` |
| `id-cubetutor-deploy-prod` | `repo:aepii/cube-tutor:environment:production` | Contributor; RBAC Administrator **(conditional)** | `rg-cubetutor-prod` |
| `id-cubetutor-api-<env>` | — | Key Vault Secrets User | that env's Key Vault |
| | | Storage Blob Data Contributor | that env's storage account |

- **Environment-scoped subjects.** A token for `environment:dev` exists only in a job running in the `dev` GitHub environment, which only `master` may use. A `production` token requires a `v*` tag **and** the owner's approval. So the GitHub environment rules ([ci-cd.md](ci-cd.md#environments)) are what guard Azure.
- **The `pull_request` subject (dev only)** lets `infra-whatif.yml` log in on PRs, which can't use the `dev` environment. The trade-off: anyone who can push a branch to this repo can act as the dev deployer. In this solo repo that's the owner, who can already merge to `master`. Fork PRs get no OIDC token from GitHub, so they can't use it. Prod has no such credential.
- **Conditional RBAC Administrator.** Contributor can't create role assignments, but `main.bicep` has to grant the `api` identity its two roles. RBAC Administrator does that, limited by an ABAC condition (`infra/modules/bootstrap/rgRoles.bicep`): it may create or delete assignments only for **Key Vault Secrets User** and **Storage Blob Data Contributor**, and only to **service principals** (managed identities). So the deploy identity can't make anything Owner, give itself more rights, or grant a user anything. When the template needs a new role, add its ID to that list and re-run the bootstrap.
- **Deploy identities live in the shared group**, so Contributor on its own environment's group can't delete or re-point the identity it logs in with. Nothing is granted at subscription scope. A deploy identity can't see the other environment or the other project in this subscription.
- **Same image, own identity:** the `api` identity is separate from the deploy identity. The running app can read secrets and blobs, but can't change infrastructure.

## How it's deployed

- `deploy.yml` (dev on every merge to `master`, production on an approved release):
  1. Checks out the commit being deployed. For a release that's the tagged commit, so infra and image match.
  2. Logs in with `azure/login` (OIDC).
  3. Runs `az deployment group create -g rg-cubetutor-<env> --parameters infra/<env>.bicepparam`. Incremental mode: re-runs converge, and nothing outside the template is deleted.
- `infra-whatif.yml` runs on PRs touching `infra/**`. It previews the same deployment against **dev** and keeps one PR comment up to date. It can't preview prod, because the dev identity has no access there. Prod differs from dev only in names and the parameter file.
- `main.bicep`'s `apiImage` parameter defaults to the placeholder (`mcr.microsoft.com/k8se/quickstart`). From 23b, `deploy.yml` passes the image digest, so a re-run of Bicep never rolls the app back to the placeholder.

## Cost guardrails

Target: ≈$0–2/month in year one (ROADMAP §3.12).

- **Budget** `budget-cubetutor`: $5/month, filtered to the three `rg-cubetutor-*` resource groups (the subscription is shared), email at **80% actual** and **100% forecast**. It's created first in the bootstrap. On *Azure for Students* the $100 credit already has a hard spending limit, so the budget is an early warning that credit is burning, not protection from a bill.
- `api` min replicas **0**: an idle app costs nothing and stays within the monthly free grant.
- Log Analytics **daily cap 0.15 GB** (≈ the 5 GB/month free allowance) and 30-day retention.
- Postgres B1ms + 32 GB storage: free for 12 months. Then ≈$12–15/month, or move to Neon or Supabase.
- No Azure Container Registry: images come from GHCR, which is free.

## Known limits (demo choices)

- **Postgres is reachable from any Azure IP** (the 0.0.0.0 "allow Azure services" rule). Any tenant's Azure resources can reach the port, so the password is the only barrier. The production answer is a VNet-integrated Container Apps environment plus private access for Postgres. That costs money, so it isn't planned.
- Key Vault and storage also have public network access, with authentication through Entra ID only.
- Key Vault purge protection is off, so teardown and re-create work. Turn it on for real data. It can't be turned off again.
