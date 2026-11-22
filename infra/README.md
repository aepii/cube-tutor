# infra/

Bicep for CubeTutor on Azure. What it builds and why: [`docs/infra.md`](../docs/infra.md) and [ADR 0007](../docs/decisions/0007-azure-container-apps-bicep.md).

| File | Scope | Run by |
|---|---|---|
| `bootstrap.bicep` + `modules/bootstrap/` | subscription | **you, once**, from Azure Cloud Shell (this runbook) |
| `main.bicep` + `modules/*.bicep`, `dev.bicepparam`, `prod.bicepparam` | resource group | `deploy.yml` on every deploy; `infra-whatif.yml` previews it on PRs |
| `bicepconfig.json`, `lint.sh` | — | the `infra` CI job: `BICEP=<path to bicep> bash infra/lint.sh` (any warning fails) |

## Bootstrap runbook (Cloud Shell, Bash)

Everything runs in [Azure Cloud Shell](https://shell.azure.com) (Bash). It already has `az`, `git`, `jq` and `gh`, so you need no local tools.

### 1. Prerequisites

- **Owner** on the subscription (role assignments need it).
- The subscription's allowed-regions policy must include `centralus` (resources). For Postgres it must include `centralus` or a fallback: `northcentralus`, then `westus3`.
- Pick the right subscription. It's shared with another project:
  ```bash
  az account list -o table
  az account set --subscription "<subscription name or id>"
  ```

### 2. Register the resource providers

A subscription can only create a resource type once its provider is registered. Registering is idempotent; already-registered providers are no-ops.

```bash
providers="Microsoft.App Microsoft.DBforPostgreSQL Microsoft.Web Microsoft.KeyVault Microsoft.OperationalInsights Microsoft.Insights Microsoft.Storage Microsoft.ManagedIdentity Microsoft.Consumption"
for p in $providers; do az provider register --namespace "$p"; done
for p in $providers; do
  until [ "$(az provider show --namespace "$p" --query registrationState -o tsv)" = "Registered" ]; do sleep 10; done
  echo "$p: Registered"
done
```

### 3. Deploy the bootstrap

Get the files:
- **After the PR is merged:** `git clone https://github.com/aepii/cube-tutor.git && cd cube-tutor`
- **Before (testing the branch):** zip `infra/` locally, upload it in Cloud Shell (*Manage files → Upload*), then run `mkdir -p cube-tutor && cd cube-tutor && unzip ~/infra.zip`.

```bash
# Password: 8–128 chars, 3 of upper/lower/digit/symbol. Typed, never stored in git or history.
read -rsp 'Postgres admin password: ' PGPW; echo
# Re-runs must keep the budget's original start date.
START=$(az consumption budget show --budget-name budget-cubetutor --query timePeriod.startDate -o tsv 2>/dev/null)

az deployment sub create \
  --name cubetutor-bootstrap \
  --location centralus \
  --template-file infra/bootstrap.bicep \
  --parameters budgetContactEmails='["you@example.com"]' \
               postgresAdminPassword="$PGPW" \
               ${START:+budgetStartDate=$START}
```

- Postgres fails with *"location is restricted"*: add `postgresLocation=northcentralus` (then `westus3`) to `--parameters` and run it again.
- Budgets not supported on the subscription: add `enableBudget=false`.
- Takes ~10 minutes (most of it is Postgres).

Keep the password somewhere safe (a password manager). 23b stores the connection string in Key Vault.

### 4. Set the GitHub variables

These are IDs, not credentials, so they're **variables**, not secrets. The bootstrap outputs them:

```bash
O=$(az deployment sub show --name cubetutor-bootstrap --query properties.outputs -o json)
echo "$O" | jq 'map_values(.value)'
```

| Variable | Where | Value |
|---|---|---|
| `AZURE_TENANT_ID` | repository | `tenantId` output |
| `AZURE_SUBSCRIPTION_ID` | repository | `subscriptionId` output |
| `AZURE_WHATIF_CLIENT_ID` | repository | `devClientId` output (infra-whatif runs as the dev identity) |
| `AZURE_CLIENT_ID` | environment `dev` | `devClientId` output |
| `AZURE_CLIENT_ID` | environment `production` | `prodClientId` output |

With `gh` (run `gh auth login` first):

```bash
R=aepii/cube-tutor
v() { jq -r ".$1.value" <<<"$O"; }
gh variable set AZURE_TENANT_ID        -R "$R" -b "$(v tenantId)"
gh variable set AZURE_SUBSCRIPTION_ID  -R "$R" -b "$(v subscriptionId)"
gh variable set AZURE_WHATIF_CLIENT_ID -R "$R" -b "$(v devClientId)"
gh variable set AZURE_CLIENT_ID        -R "$R" -e dev        -b "$(v devClientId)"
gh variable set AZURE_CLIENT_ID        -R "$R" -e production -b "$(v prodClientId)"
```

Or in GitHub: *Settings → Secrets and variables → Actions → Variables* for the repository ones, and *Settings → Environments → dev / production → Environment variables* for the others.

### 5. Check it worked

```bash
# Re-running changes nothing. Use the same password (what-if can't compare secure values).
START=$(az consumption budget show --budget-name budget-cubetutor --query timePeriod.startDate -o tsv)
az deployment sub what-if --location centralus --template-file infra/bootstrap.bicep \
  --parameters budgetContactEmails='["you@example.com"]' postgresAdminPassword="$PGPW" budgetStartDate="$START"

az group list --query "[?starts_with(name, 'rg-cubetutor')].name" -o tsv              # 3 groups
# `az consumption` uses an old API that doesn't return `filter`; read the budget with the current one.
az rest --method get --url "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/providers/Microsoft.Consumption/budgets/budget-cubetutor?api-version=2026-06-01"   --query "properties.{amount:amount, filter:filter, notifications:notifications}"
PG=$(az postgres flexible-server list -g rg-cubetutor-shared --query "[0].name" -o tsv)
az postgres flexible-server db list -g rg-cubetutor-shared -s "$PG" --query "[].name" -o tsv   # includes cubetutor_dev, cubetutor_prod
for e in dev prod; do
  az identity federated-credential list -g rg-cubetutor-shared --identity-name "id-cubetutor-deploy-$e" --query "[].subject" -o tsv
  pid=$(az identity show -g rg-cubetutor-shared -n "id-cubetutor-deploy-$e" --query principalId -o tsv)
  az role assignment list --assignee "$pid" --all --query "[].{role:roleDefinitionName, scope:scope, condition:condition!=null}" -o table
done
```

Expected:
- What-if shows no Create or Delete. These *Modify* / *Unsupported* lines are known what-if noise, not drift:
  - budget `- endDate` (Azure's default 10-year end date; the template doesn't set one)
  - Postgres `dataEncryption`, `replica`, `replicationRole`, `storage.iops/tier/type` (server-populated)
  - identity `isolationScope` (an Azure default)
  - 4 role assignments as *Unsupported* (their names depend on a principal ID that only exists during deployment; the role table below checks them)
- Each deploy identity has two assignments, both on its **own** resource group: Contributor (`condition: False`) and Role Based Access Control Administrator (`condition: True`).
- The budget also appears in the portal under *Cost Management → Budgets* with the 3-resource-group filter.

### 6. Tear it all down

```bash
for rg in rg-cubetutor-dev rg-cubetutor-prod rg-cubetutor-shared; do az group delete --name "$rg" --yes; done
# Key Vault soft delete keeps the names reserved for 7 days; purge to reuse them now.
for kv in $(az keyvault list-deleted --query "[?starts_with(name, 'kv-cubetutor')].name" -o tsv); do az keyvault purge --name "$kv"; done
az consumption budget delete --budget-name budget-cubetutor
az deployment sub delete --name cubetutor-bootstrap
# Optional: remove the GitHub variables
for v in AZURE_TENANT_ID AZURE_SUBSCRIPTION_ID AZURE_WHATIF_CLIENT_ID; do gh variable delete "$v" -R aepii/cube-tutor; done
for e in dev production; do gh variable delete AZURE_CLIENT_ID -R aepii/cube-tutor -e "$e"; done
```

Deleting the resource groups also removes the role assignments scoped to them. Deleting `rg-cubetutor-shared` removes the deploy identities and their federated credentials.
