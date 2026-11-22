// Container Apps environment (workload-profiles type, Consumption profile only:
// pay per use, nothing reserved) + the `api` app. min 0 replicas: it scales to
// zero when idle, which keeps it inside the monthly free grant (ROADMAP §3.12).
param location string
param environmentName string
param appName string
param workspaceName string
param identityId string
param image string
param targetPort int
param tags object

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
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
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
        }
      ]
      scale: {
        minReplicas: 0 // never keep one warm: that burns the free grant
        maxReplicas: 2
      }
    }
  }
}

output url string = 'https://${api.properties.configuration.ingress.fqdn}'
