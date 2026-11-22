// Key Vault in RBAC mode (no access policies). 23b puts SECRET_KEY and
// DATABASE_URL here; the api identity reads them as Key Vault Secrets User.
param location string
param name string
param apiPrincipalId string
param tags object

var keyVaultSecretsUser = '4633458b-17de-408a-b874-0445c86b69e6'

resource vault 'Microsoft.KeyVault/vaults@2026-05-15' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    accessPolicies: []
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    // Purge protection is irreversible once on, and it would block teardown +
    // re-create with the same name for the retention period. A demo doesn't need it.
    enablePurgeProtection: null
    publicNetworkAccess: 'Enabled' // no VNet in this project (cost); see ADR 0007
  }
}

resource secretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, apiPrincipalId, keyVaultSecretsUser)
  scope: vault
  properties: {
    principalId: apiPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUser)
  }
}

output name string = vault.name
