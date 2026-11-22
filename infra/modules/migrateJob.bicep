// Migration job: a manually triggered Container Apps Job that runs
// `alembic upgrade head` and the (idempotent) seed from the backend image.
// deploy.yml starts it with the NEW image and waits for it to succeed before the
// api moves to that image, so a failed migration never shifts traffic.
// Runs as the api identity (Key Vault Secrets User), with the same secrets.
param location string
param name string
param environmentId string
param identityId string
param image string

@description('Key Vault URI (https://<name>.vault.azure.net/) holding database-url and secret-key.')
param keyVaultUri string

param tags object

resource job 'Microsoft.App/jobs@2026-07-01' = {
  name: name
  location: location
  tags: union(tags, { component: 'migrate' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    environmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 600 // seconds; a stuck migration fails instead of hanging the deploy
      replicaRetryLimit: 0 // a failed migration is not retried: someone has to read why
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      secrets: [
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
    }
    template: {
      containers: [
        {
          name: 'migrate'
          image: image
          // Same command as the Compose `migrate` service.
          command: ['sh', '-c', 'alembic upgrade head && python -m seed.seed_algorithms']
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            { name: 'DATABASE_URL', secretRef: 'database-url' }
            // Settings requires it; the seed doesn't use it.
            { name: 'SECRET_KEY', secretRef: 'secret-key' }
          ]
        }
      ]
    }
  }
}

output name string = job.name
