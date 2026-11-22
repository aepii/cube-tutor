// One-time bootstrap, run by the subscription owner from Azure Cloud Shell
// (see infra/README.md). Creates what the per-environment template can't:
//   - the $5 budget (first), filtered to CubeTutor's resource groups
//   - the three resource groups
//   - the shared Postgres server with one database per environment
//   - one deploy identity per GitHub environment (user-assigned managed identity
//     + federated credential) and its RBAC on its own resource group
// The subscription is shared with another project: nothing here touches other
// resource groups or subscription-wide settings except the RG-filtered budget.
targetScope = 'subscription'

@description('Region for the resource groups and the CubeTutor resources.')
param location string = deployment().location

@description('Region for the Postgres server only. Student subscriptions sometimes refuse Postgres in a region; fall back to northcentralus, then westus3.')
param postgresLocation string = location

@description('GitHub repository (owner/name) whose workflows may log in as the deploy identities.')
param githubRepo string = 'aepii/cube-tutor'

@description('Create the Cost Management budget. Turn off only if the subscription type does not support budgets.')
param enableBudget bool = true

@description('Monthly budget in the billing currency.')
param budgetAmount int = 5

@description('First day of the budget period (yyyy-MM-01). Defaults to this month; on a re-run in a later month pass the existing start date (see README).')
param budgetStartDate string = '${utcNow('yyyy-MM')}-01'

@description('Who gets the budget alert emails.')
@minLength(1)
param budgetContactEmails array

@description('Postgres administrator login name.')
param postgresAdminLogin string = 'cubetutoradmin'

@description('Postgres administrator password. Typed in at deploy time; never stored in git.')
@secure()
param postgresAdminPassword string

var tags = { app: 'cubetutor' }
var rgNames = {
  shared: 'rg-cubetutor-shared'
  dev: 'rg-cubetutor-dev'
  prod: 'rg-cubetutor-prod'
}

// ---- Budget (created before anything else) ---------------------------------

resource budget 'Microsoft.Consumption/budgets@2026-06-01' = if (enableBudget) {
  name: 'budget-cubetutor'
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: budgetStartDate
    }
    // The subscription is shared: only count CubeTutor's resource groups.
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: [rgNames.shared, rgNames.dev, rgNames.prod]
      }
    }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: budgetContactEmails
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: budgetContactEmails
      }
    }
  }
}

// ---- Resource groups ---------------------------------------------------------

resource rgShared 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: rgNames.shared
  location: location
  tags: tags
  dependsOn: [budget]
}

resource rgDev 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: rgNames.dev
  location: location
  tags: union(tags, { env: 'dev' })
  dependsOn: [budget]
}

resource rgProd 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: rgNames.prod
  location: location
  tags: union(tags, { env: 'prod' })
  dependsOn: [budget]
}

// ---- Shared Postgres -----------------------------------------------------------

module postgres 'modules/bootstrap/postgres.bicep' = {
  name: 'postgres'
  scope: rgShared
  params: {
    location: postgresLocation
    // Server names are global DNS names, hence the suffix.
    serverName: 'psql-cubetutor-${take(uniqueString(subscription().id, rgNames.shared), 6)}'
    adminLogin: postgresAdminLogin
    adminPassword: postgresAdminPassword
    databaseNames: ['cubetutor_dev', 'cubetutor_prod']
    tags: tags
  }
}

// ---- Deploy identities (in the shared RG, so an env's Contributor can't touch them)

module deployIdDev 'modules/bootstrap/deployIdentity.bicep' = {
  name: 'deploy-identity-dev'
  scope: rgShared
  params: {
    location: location
    name: 'id-cubetutor-deploy-dev'
    tags: union(tags, { env: 'dev' })
    federatedCredentials: [
      // deploy.yml jobs running in the `dev` GitHub environment (master only).
      { name: 'github-env-dev', subject: 'repo:${githubRepo}:environment:dev' }
      // infra-whatif.yml on pull requests (fork PRs get no OIDC token).
      { name: 'github-pull-request', subject: 'repo:${githubRepo}:pull_request' }
    ]
  }
}

module deployIdProd 'modules/bootstrap/deployIdentity.bicep' = {
  name: 'deploy-identity-prod'
  scope: rgShared
  params: {
    location: location
    name: 'id-cubetutor-deploy-prod'
    tags: union(tags, { env: 'prod' })
    federatedCredentials: [
      // deploy.yml jobs running in the `production` GitHub environment (v* tags, approved).
      { name: 'github-env-production', subject: 'repo:${githubRepo}:environment:production' }
    ]
  }
}

// ---- RBAC: each deploy identity on its own resource group only ----------------

module rolesDev 'modules/bootstrap/rgRoles.bicep' = {
  name: 'deploy-roles-dev'
  scope: rgDev
  params: {
    principalId: deployIdDev.outputs.principalId
  }
}

module rolesProd 'modules/bootstrap/rgRoles.bicep' = {
  name: 'deploy-roles-prod'
  scope: rgProd
  params: {
    principalId: deployIdProd.outputs.principalId
  }
}

// ---- Values for the GitHub variables (none of them are secrets) ---------------

output tenantId string = tenant().tenantId
output subscriptionId string = subscription().subscriptionId
output devClientId string = deployIdDev.outputs.clientId
output prodClientId string = deployIdProd.outputs.clientId
output postgresHost string = postgres.outputs.fqdn
