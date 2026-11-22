#!/usr/bin/env bash
# Start one execution of the migration job and wait for it to finish.
#   run-migration.sh <resource group> <job name> [extra `az containerapp job start` args...]
# Exit 0 when the execution succeeds. Otherwise print its logs (from Log
# Analytics) and exit 1. Used by deploy.yml between the two Bicep passes, so
# the api only moves to the new image after this succeeds. The extra args are
# for rehearsing a failure from Cloud Shell (infra/README.md), e.g.
#   bash infra/scripts/run-migration.sh rg-cubetutor-dev caj-cubetutor-migrate-dev \
#     --command sh --args -c 'echo failing on purpose; exit 1'
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: $0 <resource group> <job name> [az containerapp job start args...]" >&2
  exit 2
fi
rg="$1"
job="$2"
shift 2

TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-900}"   # the job's replica timeout is 600 s; leave room to schedule it
LOG_WAIT_SECONDS="${LOG_WAIT_SECONDS:-300}" # Log Analytics ingestion can lag by several minutes

execution=$(az containerapp job start --name "$job" --resource-group "$rg" "$@" --query name --output tsv)
if [ -z "$execution" ]; then
  echo "::error::az containerapp job start returned no execution name" >&2
  exit 1
fi
echo "Started $job execution $execution"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  echo "execution=$execution" >> "$GITHUB_OUTPUT"
fi

status=""
deadline=$((SECONDS + TIMEOUT_SECONDS))
while :; do
  status=$(az containerapp job execution show --name "$job" --resource-group "$rg" \
    --job-execution-name "$execution" --query properties.status --output tsv)
  echo "$(date -u +%H:%M:%S) $execution: $status"
  case "$status" in
    Succeeded) echo "Migration job succeeded."; exit 0 ;;
    Failed | Stopped | Degraded) break ;;
  esac
  if [ "$SECONDS" -ge "$deadline" ]; then
    status="timed out after ${TIMEOUT_SECONDS}s (last status: $status)"
    break
  fi
  sleep 10
done

echo "::error::Migration job execution $execution: $status. The api was not changed."

# The replica is gone by now, so `az containerapp job logs show` can't stream
# it. Its console output is in the environment's Log Analytics workspace.
envId=$(az containerapp job show --name "$job" --resource-group "$rg" --query properties.environmentId --output tsv)
workspace=$(az containerapp env show --ids "$envId" \
  --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId --output tsv)
# One line, so the fallback below prints a command that can be pasted as is.
query="ContainerAppConsoleLogs_CL | where ContainerJobName_s == '$job' and ContainerGroupName_s startswith '$execution' | project TimeGenerated, Log_s | order by TimeGenerated asc"

echo "Waiting up to ${LOG_WAIT_SECONDS}s for the execution's logs to reach Log Analytics..."
errfile=$(mktemp)
trap 'rm -f "$errfile"' EXIT
deadline=$((SECONDS + LOG_WAIT_SECONDS))
logs=""
query_failed=0
while :; do
  # Keep the query's stderr: an error (extension, auth, KQL) must not look like
  # "the logs haven't arrived yet". Retry anyway, since some errors are transient.
  if logs=$(az monitor log-analytics query --workspace "$workspace" --analytics-query "$query"       --timespan PT2H --query "[].Log_s" --output tsv 2>"$errfile"); then
    query_failed=0
  else
    query_failed=1
    logs=""
  fi
  if [ -n "$logs" ] || [ "$SECONDS" -ge "$deadline" ]; then
    break
  fi
  sleep 15
done

if [ -n "$logs" ]; then
  echo "----- $execution logs -----"
  printf '%s
' "$logs"
  echo "----- end of logs -----"
else
  if [ "$query_failed" -eq 1 ]; then
    echo "::warning::The Log Analytics query failed, so the logs couldn't be read:"
    cat "$errfile"
  else
    echo "No logs arrived within ${LOG_WAIT_SECONDS}s."
  fi
  echo "Read them later with:"
  echo "az monitor log-analytics query --workspace $workspace --timespan PT2H --query \"[].Log_s\" --output tsv \\"
  echo "  --analytics-query \"$query\""
fi
exit 1
