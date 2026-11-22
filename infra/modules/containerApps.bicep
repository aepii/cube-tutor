// Container Apps environment (workload-profiles type, Consumption profile only:
// pay per use, nothing reserved) + the `api` app. min 0 replicas: it scales to
// zero when idle, which keeps it inside the monthly free grant (ROADMAP §3.12).
param location string
param environmentName string
param appName string
param workspaceName string
param identityId string
param image string

@description('False only for the public placeholder image: it listens on 80 and has no /health endpoints.')
param isBackendImage bool

@description('Key Vault URI (https://<name>.vault.azure.net/) holding database-url and secret-key.')
param keyVaultUri string

@description('CORS_ORIGINS for the API (comma-separated).')
param corsOrigins string

param tags object

var port = isBackendImage ? 8000 : 80

// Key Vault references: Container Apps fetches the secret as the api identity
// (Key Vault Secrets User on the vault). Versionless URLs: a new secret version
// is picked up within ~30 minutes, or immediately on a revision restart.
var secrets = [
  {
    name: 'database-url'
    keyVaultUrl: '${keyVaultUri}secrets/database-url'
    identity: identityId
  }
  {
    name: 'secret-key'
    keyVaultUrl: '${keyVaultUri}secrets/secret-key'
    identity: identityId
  }
]

// Startup gives a cold start ~2 minutes; liveness restarts a hung process;
// readiness (which pings the database) takes a replica out of rotation during a
// database outage instead of letting it serve 500s.
var probes = [
  {
    type: 'Startup'
    httpGet: { path: '/health/live', port: port }
    periodSeconds: 3
    timeoutSeconds: 2
    failureThreshold: 40
  }
  {
    type: 'Liveness'
    httpGet: { path: '/health/live', port: port }
    periodSeconds: 30
    timeoutSeconds: 3
    failureThreshold: 3
  }
  {
    type: 'Readiness'
    httpGet: { path: '/health/ready', port: port }
    periodSeconds: 10
    timeoutSeconds: 3
    failureThreshold: 3
  }
]

resource workspace 'Microsoft.OperationalInsights/workspaces@2026-03-01' existing = {
  name: workspaceName
}

resource env 'Microsoft.App/managedEnvironments@2026-07-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: workspace.properties.customerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

resource api 'Microsoft.App/containerApps@2026-07-01' = {
  name: appName
  location: location
  tags: union(tags, { component: 'api' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    environmentId: env.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: port
        transport: 'auto'
        allowInsecure: false
      }
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: 'api'
          image: image
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
            { name: 'CORS_ORIGINS', value: corsOrigins }
          ]
          probes: isBackendImage ? probes : []
        }
      ]
      scale: {
        minReplicas: 0 // never keep one warm: that burns the free grant
        maxReplicas: 2
        rules: [
          {
            // Add a replica per 10 concurrent requests; with min 0, the first
            // request after idle cold-starts one.
            name: 'http'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

output environmentId string = env.id
output appName string = api.name
output url string = 'https://${api.properties.configuration.ingress.fqdn}'
