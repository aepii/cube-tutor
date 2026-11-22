# 0007: Azure Container Apps, Bicep, and GitHub OIDC through managed identities

**Status:** accepted (23a, issue #29). Builds on [ADR 0006](0006-trunk-based-release-tags.md) (environments, promote by digest).

**Evidence:** ROADMAP §3.9 (stated: service choices), §3.11 (environments, OIDC), §3.12 (cost); `infra/`, `.github/workflows/deploy.yml`, `infra-whatif.yml`.

## Context
- CubeTutor needs a `dev` and a `production` deployment of one FastAPI container, a web build, Postgres, secrets, blob storage and telemetry, at roughly zero cost while it has no users.
- The target is an *Azure for Students* subscription that **another project also uses**. Its constraints:
  - an allowed-regions policy
  - a $100 credit with a hard limit
  - a school Entra directory, where creating app registrations is usually blocked
- It's a portfolio project. The choices should be what teams use, and easy to explain.
- No Azure secret should be stored in GitHub.

## Decision
- **Compute: Azure Container Apps** (Consumption profile). One `api` app per environment, scale 0..N, the same image as local Docker.
- **Infrastructure as code: Bicep.** There are two templates:
  - a subscription-scope **bootstrap**, run once by the Owner from Cloud Shell: budget, resource groups, shared Postgres, deploy identities and RBAC
  - a resource-group template that `deploy.yml` applies on **every** deploy, so drift is corrected each time
- **Identity for CI: user-assigned managed identities with GitHub federated credentials**, one per environment. The subjects are environment-scoped (`repo:aepii/cube-tutor:environment:dev` / `:production`). GitHub stores only IDs, as variables.
- **Least privilege for the deploy identities:**
  - Contributor on their own resource group only.
  - Role Based Access Control Administrator **with a condition**: it may only assign the two data-plane roles the template uses, and only to service principals.
- **Data:** one shared Postgres Flexible Server (B1ms, free for 12 months) with a database per environment. Password auth and public access with the "allow Azure services" rule.

## Alternatives
- **App Service (Web App for Containers).** Rejected: the cheapest always-on plan costs money, and its free tier doesn't run containers or scale to zero. Container Apps also gives KEDA scaling for the Service Bus worker (Phase 24) and Jobs for migrations and cron (23b, Phase 18).
- **AKS.** Rejected: there's a cluster to run and pay for, which is far more than one API needs. Container Apps runs on Kubernetes and KEDA without exposing them.
- **Terraform.** Rejected: it needs remote state storage, locking and a provider for every API change. Bicep has no state (Azure is the state), supports new API versions on day one, and has `what-if` built in. Terraform is the better fit for multi-cloud; this project is Azure-only.
- **App-registration (service principal) OIDC.** Rejected: school directories usually block app registrations. An app registration is also a directory-level object, while a user-assigned identity is a normal Azure resource. You can create, inspect and delete it with the resource group, so it's easier to tear down cleanly. The OIDC flow is the same.
- **A client secret in GitHub.** Rejected: secrets expire and leak, and must be rotated. Federated credentials have nothing to steal.
- **Owner or User Access Administrator for the deploy identity.** Rejected: either one lets it grant itself anything. The conditional RBAC Administrator gives it exactly the role assignments the template needs.
- **One subscription-scope deployment from CI.** Rejected: the identity would need subscription rights, which is unacceptable in a subscription shared with another project.
- **Private networking (VNet-integrated environment, private Postgres).** Deferred: it's the production answer, but it costs money. Without it, any Azure IP can reach Postgres, so the password is the only barrier. Acceptable for a demo with no real data.

## Consequences
- Merging to `master` keeps dev's infrastructure in line with `infra/` automatically. A release does the same for prod, from the tagged commit.
- The bootstrap is the one manual step. A new role for the template means editing the condition's role list and re-running the bootstrap.
- PR previews (`infra-whatif.yml`) log in as the dev identity through an extra `pull_request` federated credential. Anyone who can push a branch can act as the dev deployer, which here is only the owner. Prod can't be previewed.
- One Postgres server serves both environments. A real team would give prod its own server.
- Container Apps scales to zero, so the first request after idling has a cold start of a few seconds.
