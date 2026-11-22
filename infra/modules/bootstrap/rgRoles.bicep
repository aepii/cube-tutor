// What a deploy identity may do, scoped to its own environment's resource group:
//   - Contributor: create and update resources (cannot touch role assignments)
//   - Role Based Access Control Administrator, *with a condition*: it may only
//     create or delete assignments of the roles main.bicep hands out, and only to
//     service principals (managed identities). Assigning Owner, Contributor,
//     User Access Administrator, or any role to a user is denied.
// Nothing is assigned at subscription scope, so the identity can't see or change
// the other environment or the other project in this subscription.
param principalId string

var roleIds = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  rbacAdministrator: 'f58310d9-a9f6-439a-9e8d-f62e7b41a168'
  // The only roles main.bicep assigns. Add a role here when the template needs it.
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}
var assignableRoles = '${roleIds.keyVaultSecretsUser}, ${roleIds.storageBlobDataContributor}'

// ABAC condition (version 2.0), the form the portal's "Constrain roles and
// principal types" option generates. Each block reads: "if the action is X,
// the request/resource must match these roles and principal types".
var rbacCondition = '''
(
 (
  !(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})
 )
 OR
 (
  @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {ASSIGNABLE_ROLES}
  AND
  @Request[Microsoft.Authorization/roleAssignments:PrincipalType] ForAnyOfAnyValues:StringEqualsIgnoreCase {'ServicePrincipal'}
 )
)
AND
(
 (
  !(ActionMatches{'Microsoft.Authorization/roleAssignments/delete'})
 )
 OR
 (
  @Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {ASSIGNABLE_ROLES}
  AND
  @Resource[Microsoft.Authorization/roleAssignments:PrincipalType] ForAnyOfAnyValues:StringEqualsIgnoreCase {'ServicePrincipal'}
 )
)
'''

resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleIds.contributor)
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.contributor)
    description: 'CubeTutor deploy identity: manage resources in this resource group'
  }
}

resource rbacAdmin 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleIds.rbacAdministrator)
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleIds.rbacAdministrator)
    description: 'CubeTutor deploy identity: assign only Key Vault Secrets User / Storage Blob Data Contributor to managed identities'
    conditionVersion: '2.0'
    condition: replace(rbacCondition, 'ASSIGNABLE_ROLES', assignableRoles)
  }
}
