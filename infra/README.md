# infra/

Bicep for CubeTutor on Azure. What it builds and why: [`docs/infra.md`](../docs/infra.md) and [ADR 0007](../docs/decisions/0007-azure-container-apps-bicep.md).

| File | Scope | Run by |
|---|---|---|
| `bootstrap.bicep` + `modules/bootstrap/` | subscription | **you, once**, from Azure Cloud Shell (this runbook) |
| `main.bicep` + `modules/*.bicep`, `dev.bicepparam`, `prod.bicepparam` | resource group | `deploy.yml` on every deploy; `infra-whatif.yml` previews it on PRs |
| `scripts/run-migration.sh` | — | `deploy.yml` (start the migration job, wait, print its logs if it fails); you, to rehearse a failure (step 7) |
| `bicepconfig.json`, `lint.sh` | — | the `infra` CI job: `BICEP=<path to bicep> bash infra/lint.sh` (any warning fails) |

## Bootstrap runbook (Cloud Shell, Bash)

Everything runs in [Azure Cloud Shell](https://shell.azure.com) (Bash). It already has `az`, `git`, `jq` and `gh`, so you need no local tools.

### 1. Prerequisites

- **Owner** on the subscription (role assignments need it). The bootstrap also gives you **Key Vault Secrets Officer** on `rg-cubetutor-dev` and `rg-cubetutor-prod`: in an RBAC-mode vault, Owner alone can't read or write secrets.
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
# You: gets Key Vault Secrets Officer on the dev and prod resource groups.
ME=$(az ad signed-in-user show --query id -o tsv)

az deployment sub create \
  --name cubetutor-bootstrap \
  --location centralus \
  --template-file infra/bootstrap.bicep \
  --parameters budgetContactEmails='["you@example.com"]' \
               postgresAdminPassword="$PGPW" \
               ownerPrincipalId="$ME" \
               ${START:+budgetStartDate=$START}
```

- Postgres fails with *"location is restricted"*: add `postgresLocation=northcentralus` (then `westus3`) to `--parameters` and run it again.
- Budgets not supported on the subscription: add `enableBudget=false`.
- Takes ~10 minutes (most of it is Postgres).

Keep the password somewhere safe (a password manager). The app doesn't use it: each environment gets its own database user (step 6).

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
ME=$(az ad signed-in-user show --query id -o tsv)
az deployment sub what-if --location centralus --template-file infra/bootstrap.bicep \
  --parameters budgetContactEmails='["you@example.com"]' postgresAdminPassword="$PGPW" ownerPrincipalId="$ME" budgetStartDate="$START"

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
az role assignment list --assignee "$ME" --all --query "[?roleDefinitionName=='Key Vault Secrets Officer'].scope" -o tsv
```

Expected:
- What-if shows no Create or Delete. These *Modify* / *Unsupported* lines are known what-if noise, not drift:
  - budget `- endDate` (Azure's default 10-year end date; the template doesn't set one)
  - Postgres `dataEncryption`, `replica`, `replicationRole`, `storage.iops/tier/type` (server-populated)
  - identity `isolationScope` (an Azure default)
  - 4 role assignments as *Unsupported*: the deploy identities' assignments, whose names depend on a principal ID that only exists during deployment. The role checks below cover them.
  - Your 2 Key Vault Secrets Officer assignments show as *Create* on the first run that adds them, and *Nochange* after that.
- Each deploy identity has two assignments, both on its **own** resource group: Contributor (`condition: False`) and Role Based Access Control Administrator (`condition: True`).
- You have Key Vault Secrets Officer on exactly `rg-cubetutor-dev` and `rg-cubetutor-prod`.
- The budget also appears in the portal under *Cost Management → Budgets* with the 3-resource-group filter.

### 6. Create the app database users and secrets (once per environment)

Do this once per environment. While a secret is missing, `deploy.yml` fails at its first Bicep step: Container Apps resolves Key Vault references when it deploys.

The script needs the environment's Key Vault, and only `main.bicep` creates it (the bootstrap doesn't). On a fresh environment, the first deploy creates the vault and then fails. So the order is:

1. **Deploy once and let it fail.** Dev: merge to `master`. Prod: publish the first release and approve it. The `Deploy` run fails at "1. Bicep" with a missing-secret error on the `api` app. The vault exists by then, because the Key Vault module deploys before Container Apps.
2. **Run the script below** with `E=dev` or `E=prod`. Check the vault exists first: `az keyvault list -g rg-cubetutor-$E -o table`.
3. **Re-run the failed run** (Actions → the run → *Re-run all jobs*). For prod, the re-run needs approval again.

If the environment already has its secrets (for example after its Container Apps environment was recreated), skip this step.

Each environment gets its own Postgres role, which owns only its own database, so the admin login stays out of the app. By default Postgres lets `PUBLIC` connect to every database, so the SQL revokes that on both databases. The dev role can't even connect to `cubetutor_prod`, and the reverse.

```bash
E=dev   # then E=prod
PG=$(az postgres flexible-server list -g rg-cubetutor-shared --query "[0].name" -o tsv)
PGHOST=$(az postgres flexible-server show -g rg-cubetutor-shared -n "$PG" --query fullyQualifiedDomainName -o tsv)
KV=$(az keyvault list -g "rg-cubetutor-$E" --query "[0].name" -o tsv)
read -rsp 'Postgres admin password: ' PGPASSWORD; echo; export PGPASSWORD
# Hex: nothing that needs escaping in a URL.
APP_PW=$(openssl rand -hex 24)

# One quoted line per statement, piped in (no heredoc: a pasted, indented
# terminator leaves the shell waiting). psql fills in :"role", :"db", :'pw'.
#  - the admin isn't a superuser on Azure: it must be a member to hand the role a database
#  - since Postgres 15 the public schema belongs to pg_database_owner, so the owner can create tables
#  - no database is open to PUBLIC; only its owner and the admin connect
printf '%s\n' \
  "CREATE ROLE :\"role\" LOGIN PASSWORD :'pw';" \
  "GRANT :\"role\" TO cubetutoradmin;" \
  "ALTER DATABASE :\"db\" OWNER TO :\"role\";" \
  "REVOKE CONNECT ON DATABASE cubetutor_dev, cubetutor_prod FROM PUBLIC;" \
  "GRANT CONNECT ON DATABASE cubetutor_dev, cubetutor_prod TO cubetutoradmin;" \
| psql "host=$PGHOST port=5432 dbname=postgres user=cubetutoradmin sslmode=require" \
    -v ON_ERROR_STOP=1 -v role="cubetutor_${E}_app" -v db="cubetutor_$E" -v pw="$APP_PW"

az keyvault secret set --vault-name "$KV" --name database-url --output none \
  --value "postgresql://cubetutor_${E}_app:${APP_PW}@${PGHOST}:5432/cubetutor_${E}?sslmode=require"
az keyvault secret set --vault-name "$KV" --name secret-key --output none --value "$(openssl rand -hex 32)"
unset APP_PW
```

- **`psql` can't connect:** Cloud Shell reaches the server through the "allow Azure services" rule. If that doesn't cover it, add your IP with `az postgres flexible-server firewall-rule create -g rg-cubetutor-shared -n "$PG" -r cloudshell --start-ip-address <ip> --end-ip-address <ip>`, and delete the rule afterwards.
- **`Forbidden` from `az keyvault secret set`:** the Secrets Officer role from step 3 can take a few minutes to apply. Wait, then retry.
- **Check the isolation** (AC4): connecting as the dev role to the prod database must fail with *permission denied for database "cubetutor_prod"*. Run it while `E=dev`, before the `unset`, or with the password read back from Key Vault:
  ```bash
  psql "host=$PGHOST dbname=cubetutor_prod user=cubetutor_dev_app sslmode=require password=<dev app password>" -c 'select 1'
  ```

**Rotating a secret.** Each Key Vault reference has no version, so Container Apps reads the latest version of the secret. It picks up a new value within about 30 minutes, or right away after a restart:

```bash
APP=ca-cubetutor-api-$E
restart() { az containerapp revision restart -g "rg-cubetutor-$E" -n "$APP" \
  --revision "$(az containerapp show -g "rg-cubetutor-$E" -n "$APP" --query properties.latestRevisionName -o tsv)"; }

# SECRET_KEY signs the access tokens, so rotating it logs everyone out.
az keyvault secret set --vault-name "$KV" --name secret-key --output none --value "$(openssl rand -hex 32)"
restart

# Database password: the app can't connect between ALTER ROLE and the restart (seconds).
APP_PW=$(openssl rand -hex 24)
printf '%s\n' "ALTER ROLE :\"role\" PASSWORD :'pw';" \
| psql "host=$PGHOST dbname=postgres user=cubetutoradmin sslmode=require" \
    -v ON_ERROR_STOP=1 -v role="cubetutor_${E}_app" -v pw="$APP_PW"
az keyvault secret set --vault-name "$KV" --name database-url --output none \
  --value "postgresql://cubetutor_${E}_app:${APP_PW}@${PGHOST}:5432/cubetutor_${E}?sslmode=require"
restart
unset APP_PW PGPASSWORD
```

The migration job reads the secrets each time it starts, so it needs no restart.

### 7. Rehearse a failed migration (optional)

`deploy.yml` waits for the migration job with [`scripts/run-migration.sh`](scripts/run-migration.sh). Running the script with a command override shows what a failed migration does, without changing the job or the API:

```bash
bash infra/scripts/run-migration.sh rg-cubetutor-dev caj-cubetutor-migrate-dev \
  --command sh --args -c 'echo failing on purpose; exit 1'
echo "exit: $?"   # 1, after printing "failing on purpose" (read from Log Analytics)
az containerapp show -g rg-cubetutor-dev -n ca-cubetutor-api-dev \
  --query "{revision: properties.latestRevisionName, image: properties.template.containers[0].image}"   # unchanged
```

### 8. Tear it all down

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

Deleting the resource groups also removes the role assignments scoped to them (including your Key Vault Secrets Officer). The `cubetutor_<env>_app` Postgres roles go with the server. Deleting `rg-cubetutor-shared` removes the deploy identities and their federated credentials.
