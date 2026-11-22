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

@description('Image for the api app. deploy.yml passes the running image, then the new digest once the migration job succeeds; infra-whatif.yml passes the running image. Empty = the public placeholder (a fresh environment).')
param apiImage string = ''

@description('Image for the migration job. deploy.yml passes the digest being deployed. Empty = the api image.')
param migrateImage string = ''

// What a fresh environment runs before the first backend rollout. It listens on
// 80 and has no /health endpoints, so it gets no probes.
var placeholderImage = 'mcr.microsoft.com/k8se/quickstart:latest'
var api = empty(apiImage) ? placeholderImage : apiImage
var migrate = empty(migrateImage) ? api : migrateImage

@description('Log Analytics daily ingestion cap in GB; a cost guardrail (5 GB/month is free).')
param logDailyQuotaGb string = '0.15'

@description('Allow the Static Web App PR preview hosts as CORS origins (dev only: previews call the dev API).')
param allowPreviewOrigins bool = false

@description('Fraction of API traces sent to App Insights (0-1), as a string.')
param tracesSampleRatio string = '1.0'

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

// PR previews live at <sub>-<PR#>.<region>.<rest>, where the default hostname
// is <sub>.<rest> (e.g. gentle-sea-0abc12345.2.azurestaticapps.net). The
// default hostname has no region, so that label is [a-z0-9]+; <sub> carries a
// hash unique to this site. Anchored, https only, numeric suffix = PR previews.
var swaHost = staticWebApp.outputs.defaultHostname
var swaSub = split(swaHost, '.')[0]
var swaRest = substring(swaHost, length(swaSub) + 1)
var previewOriginRegex = '^https://${swaSub}-[0-9]+\\.[a-z0-9]+\\.${replace(swaRest, '.', '\\.')}$'

module containerApps 'modules/containerApps.bicep' = {
  name: 'containerapps'
  params: {
    location: location
    environmentName: 'cae-cubetutor-${environmentName}'
    appName: 'ca-cubetutor-api-${environmentName}'
    workspaceName: monitoring.outputs.workspaceName
    identityId: apiIdentity.id
    image: api
    isBackendImage: api != placeholderImage
    keyVaultUri: keyVault.outputs.uri
    corsOrigins: 'https://${staticWebApp.outputs.defaultHostname}'
    corsOriginRegex: allowPreviewOrigins ? previewOriginRegex : ''
    appInsightsConnectionString: monitoring.outputs.connectionString
    tracesSampleRatio: tracesSampleRatio
    tags: tags
  }
}

module migrateJob 'modules/migrateJob.bicep' = {
  name: 'migratejob'
  params: {
    location: location
    name: 'caj-cubetutor-migrate-${environmentName}'
    environmentId: containerApps.outputs.environmentId
    identityId: apiIdentity.id
    image: migrate
    keyVaultUri: keyVault.outputs.uri
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
output apiAppName string = containerApps.outputs.appName
output migrateJobName string = migrateJob.outputs.name
output apiIdentityClientId string = apiIdentity.properties.clientId
output keyVaultName string = keyVault.outputs.name
output storageAccountName string = storage.outputs.name
output staticWebAppName string = staticWebApp.outputs.name
output staticWebAppHost string = staticWebApp.outputs.defaultHostname
output appInsightsName string = monitoring.outputs.appInsightsName
