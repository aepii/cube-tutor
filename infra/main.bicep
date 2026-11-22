// Per-environment platform, deployed into rg-cubetutor-<env> by deploy.yml on
// every deploy (and previewed by infra-whatif.yml on PRs). Runs as that
// environment's deploy identity: Contributor on this resource group, plus a
// limited RBAC Administrator that may only hand out the two roles below.
// The shared Postgres server, the budget and the deploy identities live in
// bootstrap.bicep. See docs/infra.md.

@description('Short environment name used in resource names.')
@allowed(['dev', 'prod'])
param environmentName string

param location string = resourceGroup().location

@description('Image for the api app. A public placeholder until 23b passes the backend image digest.')
param apiImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Port the api image listens on (80 for the placeholder).')
param apiTargetPort int = 80

@description('Log Analytics daily ingestion cap in GB; a cost guardrail (5 GB/month is free).')
param logDailyQuotaGb string = '0.15'

var tags = {
  app: 'cubetutor'
  env: environmentName
}
// Storage and Key Vault names are global and short; this suffix is stable per RG.
var suffix = uniqueString(resourceGroup().id)

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: 'id-cubetutor-api-${environmentName}'
  location: location
  tags: tags
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    workspaceName: 'log-cubetutor-${environmentName}'
    appInsightsName: 'appi-cubetutor-${environmentName}'
    dailyQuotaGb: logDailyQuotaGb
    tags: tags
  }
}

module keyVault 'modules/keyVault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    name: 'kv-cubetutor-${environmentName}-${take(suffix, 6)}'
    apiPrincipalId: apiIdentity.properties.principalId
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    name: 'stcubetutor${environmentName}${take(suffix, 8)}'
    apiPrincipalId: apiIdentity.properties.principalId
    tags: tags
  }
}

module containerApps 'modules/containerApps.bicep' = {
  name: 'containerapps'
  params: {
    location: location
    environmentName: 'cae-cubetutor-${environmentName}'
    appName: 'ca-cubetutor-api-${environmentName}'
    workspaceName: monitoring.outputs.workspaceName
    identityId: apiIdentity.id
    image: apiImage
    targetPort: apiTargetPort
    tags: tags
  }
}

module staticWebApp 'modules/staticWebApp.bicep' = {
  name: 'staticwebapp'
  params: {
    location: location
    name: 'swa-cubetutor-${environmentName}'
    tags: tags
  }
}

output apiUrl string = containerApps.outputs.url
output apiIdentityClientId string = apiIdentity.properties.clientId
output keyVaultName string = keyVault.outputs.name
output storageAccountName string = storage.outputs.name
output staticWebAppHost string = staticWebApp.outputs.defaultHostname
output appInsightsName string = monitoring.outputs.appInsightsName
