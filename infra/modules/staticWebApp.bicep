// Static Web App (Free plan) for the Expo web build. deploy.yml uploads the
// build to the production environment with the app's deployment token (read
// with az, never stored); web-preview.yml adds one preview environment per PR
// (Free allows 3) and deletes it when the PR closes. See docs/ci-cd.md.
param location string
param name string
param tags object

resource site 'Microsoft.Web/staticSites@2025-03-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

output defaultHostname string = site.properties.defaultHostname
output name string = site.name
