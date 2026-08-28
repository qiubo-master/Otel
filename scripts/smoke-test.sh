#!/bin/sh
set -eu

endpoint=${OTEL_HTTP_ENDPOINT:-http://localhost:4318}
trace_id=5b8efff798038103d269b633813fc60c
span_id=eee19b7ec3c1b174
now_ns=$(($(date +%s) * 1000000000))
end_ns=$((now_ns + 100000000))

curl -fsS -X POST "$endpoint/v1/traces" -H 'Content-Type: application/json' -d "{
  \"resourceSpans\":[{\"resource\":{\"attributes\":[
    {\"key\":\"service.name\",\"value\":{\"stringValue\":\"smoke-test\"}},
    {\"key\":\"service.namespace\",\"value\":{\"stringValue\":\"platform\"}},
    {\"key\":\"deployment.environment.name\",\"value\":{\"stringValue\":\"local\"}}
  ]},\"scopeSpans\":[{\"scope\":{\"name\":\"smoke\"},\"spans\":[{
    \"traceId\":\"$trace_id\",\"spanId\":\"$span_id\",\"name\":\"otel-platform-smoke\",\"kind\":2,
    \"startTimeUnixNano\":\"$now_ns\",\"endTimeUnixNano\":\"$end_ns\",\"status\":{\"code\":1}
  }]}]}]}" >/dev/null

curl -fsS -X POST "$endpoint/v1/logs" -H 'Content-Type: application/json' -d "{
  \"resourceLogs\":[{\"resource\":{\"attributes\":[{\"key\":\"service.name\",\"value\":{\"stringValue\":\"smoke-test\"}}]},
  \"scopeLogs\":[{\"scope\":{\"name\":\"smoke\"},\"logRecords\":[{
    \"timeUnixNano\":\"$now_ns\",\"severityNumber\":9,\"severityText\":\"INFO\",\"body\":{\"stringValue\":\"OTel platform smoke test\"},
    \"traceId\":\"$trace_id\",\"spanId\":\"$span_id\"
  }]}]}]}" >/dev/null

curl -fsS http://localhost:13133/ >/dev/null
echo "Smoke trace and correlated log were accepted. Trace ID: $trace_id"

