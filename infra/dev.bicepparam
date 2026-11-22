// rg-cubetutor-dev (location: centralus, from the resource group). Deployed by deploy.yml.
using 'main.bicep'

param environmentName = 'dev'

// PR preview sites (web-preview.yml) call the dev API; prod keeps its exact origin.
param allowPreviewOrigins = true
