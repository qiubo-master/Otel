#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root_dir"

required_files="
docker-compose.yml
config/otel-collector.yaml
config/prometheus/prometheus.yml
config/prometheus/rules/platform-alerts.yml
config/tempo.yaml
config/grafana/provisioning/datasources/datasources.yml
config/grafana/provisioning/dashboards/dashboards.yml
config/grafana/dashboards/platform-overview.json
config/grafana/dashboards/cicd-overview.json
config/grafana/dashboards/media-overview.json
"

for file in $required_files; do
  test -s "$file" || { echo "missing or empty: $file" >&2; exit 1; }
done

for dashboard in config/grafana/dashboards/*.json; do
  python3 -m json.tool "$dashboard" >/dev/null
done

echo "Static validation passed."

