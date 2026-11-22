// Log Analytics workspace (Container Apps logs) + workspace-based App Insights.
param location string
param workspaceName string
param appInsightsName string
@description('Daily ingestion cap in GB, as a string (Bicep has no decimals).')
param dailyQuotaGb string
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2026-03-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: json(dailyQuotaGb)
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    IngestionMode: 'LogAnalytics'
  }
}

output workspaceName string = workspace.name
output appInsightsName string = appInsights.name
// Not a secret (Microsoft: it only identifies where to send telemetry), so it's
// passed to the api as a plain env var. Not a main.bicep output.
output connectionString string = appInsights.properties.ConnectionString
