// Static Web App (Free plan) for the Expo web build. Created empty: 23c deploys
// the build with the app's deployment token and turns on PR previews.
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
