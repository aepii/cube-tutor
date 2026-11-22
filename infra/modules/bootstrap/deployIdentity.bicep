// A deploy identity for one GitHub environment: a user-assigned managed identity
// (not an app registration, which school directories usually block) that GitHub
// Actions logs in as through OIDC. No secret exists anywhere: Entra ID trusts a
// GitHub-issued token whose `sub` matches one of the federated credentials.
param location string
param name string
param tags object

@description('[{ name, subject }]. Subjects are environment-scoped (repo:<owner>/<repo>:environment:<env>), so GitHub environment rules decide who gets a token.')
param federatedCredentials array

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: name
  location: location
  tags: tags
}

// Serial: an identity rejects concurrent federated-credential writes.
@batchSize(1)
resource credentials 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = [
  for fc in federatedCredentials: {
    parent: identity
    name: fc.name
    properties: {
      issuer: 'https://token.actions.githubusercontent.com'
      subject: fc.subject
      audiences: ['api://AzureADTokenExchange']
    }
  }
]

output principalId string = identity.properties.principalId
output clientId string = identity.properties.clientId
