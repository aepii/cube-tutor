#!/usr/bin/env bash
# Build and lint every Bicep and .bicepparam file under infra/. Any diagnostic
# (linter warning, compiler warning, or error) fails, so warnings can't pile up.
# Used by the `infra` job in ci.yml; run it locally the same way:
#   BICEP=/path/to/bicep bash infra/lint.sh      (default: `bicep` on PATH)
set -euo pipefail

BICEP="${BICEP:-bicep}"
cd "$(dirname "$0")"

mapfile -t files < <(find . -name '*.bicep' -o -name '*.bicepparam' | sort)
total=0
for f in "${files[@]}"; do
  # lint compiles too (modules included) and reports every diagnostic as SARIF.
  sarif=$("$BICEP" lint "$f" --diagnostics-format sarif)
  count=$(jq '[.runs[].results[]] | length' <<<"$sarif")
  if [ "$count" -gt 0 ]; then
    echo "FAIL $f ($count)"
    jq -r '.runs[].results[] | "  \(.locations[0].physicalLocation.artifactLocation.uri | sub(".*/infra/"; "infra/")):\(.locations[0].physicalLocation.region.startLine) \(.level // "warning") \(.ruleId): \(.message.text)"' <<<"$sarif"
    total=$((total + count))
  else
    echo "ok   $f"
  fi
done

if [ "$total" -gt 0 ]; then
  echo "::error::$total Bicep diagnostic(s); warnings count as errors"
  exit 1
fi
