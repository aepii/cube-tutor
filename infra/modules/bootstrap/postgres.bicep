// Shared Postgres Flexible Server (one B1ms is free for 12 months) with one
// database per environment. Public access with the "allow Azure services" rule:
// any Azure IP can reach the port, so the password is the only barrier. The
// production answer is VNet integration + private access (costs money); see ADR 0007.
param location string
param serverName string
param adminLogin string
@secure()
param adminPassword string
param databaseNames array
param tags object

resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2025-08-01' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '18'
    administratorLogin: adminLogin
    administratorLoginPassword: adminPassword
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
    storage: {
      storageSizeGB: 32 // the free-tier allowance
      autoGrow: 'Disabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

// 0.0.0.0–0.0.0.0 is Azure's special "allow public access from any Azure service" rule.
resource allowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2025-08-01' = {
  parent: server
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Serial: the server rejects concurrent database operations.
@batchSize(1)
resource databases 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2025-08-01' = [
  for db in databaseNames: {
    parent: server
    name: db
    properties: {
      charset: 'UTF8'
      collation: 'en_US.utf8'
    }
    dependsOn: [allowAzure]
  }
]

output fqdn string = server.properties.fullyQualifiedDomainName
