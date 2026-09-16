#!/usr/bin/env python3
"""Small dependency-free Prometheus endpoint for the Ontology demo dashboard."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import random
import secrets
import threading
import time
from urllib.request import Request, urlopen

STARTED_AT = time.time()


def metric_payload() -> str:
    elapsed = max(time.time() - STARTED_AT, 1)
    wave = math.sin(elapsed / 45)
    request_rate = 11 + 3 * wave
    request_total = int(18000 + elapsed * request_rate)
    error_total = int(72 + elapsed * (0.08 + 0.03 * max(wave, 0)))
    decision_total = int(12500 + elapsed * 8.4)
    lines = [
        '# HELP ontology_build_info Ontology service build information.',
        '# TYPE ontology_build_info gauge',
        'ontology_build_info{service_name="ontology",version="1.0.0",environment="demo"} 1',
        '# HELP ontology_http_requests_total HTTP requests handled by Ontology.',
        '# TYPE ontology_http_requests_total counter',
        f'ontology_http_requests_total{{service_name="ontology",route="/api/search",status="200"}} {int(request_total * 0.52)}',
        f'ontology_http_requests_total{{service_name="ontology",route="/api/entities",status="200"}} {int(request_total * 0.28)}',
        f'ontology_http_requests_total{{service_name="ontology",route="/api/decision",status="200"}} {int(request_total * 0.20)}',
        f'ontology_http_requests_total{{service_name="ontology",route="/api/search",status="500"}} {error_total}',
        '# HELP ontology_http_request_duration_seconds Ontology HTTP request duration.',
        '# TYPE ontology_http_request_duration_seconds histogram',
    ]
    latency_factor = 1 + 0.15 * wave
    buckets = [(0.05, 0.34), (0.1, 0.67), (0.25, 0.91), (0.5, 0.98), (1.0, 0.997)]
    for bound, fraction in buckets:
        lines.append(f'ontology_http_request_duration_seconds_bucket{{service_name="ontology",le="{bound}"}} {int(request_total * min(fraction / latency_factor, 0.999))}')
    lines.extend([
        f'ontology_http_request_duration_seconds_bucket{{service_name="ontology",le="+Inf"}} {request_total}',
        f'ontology_http_request_duration_seconds_sum{{service_name="ontology"}} {request_total * (0.118 + 0.012 * wave):.3f}',
        f'ontology_http_request_duration_seconds_count{{service_name="ontology"}} {request_total}',
        '# HELP ontology_entities_total Current entities by ontology type.',
        '# TYPE ontology_entities_total gauge',
        f'ontology_entities_total{{service_name="ontology",entity_type="vehicle"}} {4280 + int(elapsed / 20)}',
        f'ontology_entities_total{{service_name="ontology",entity_type="part"}} {13640 + int(elapsed / 8)}',
        f'ontology_entities_total{{service_name="ontology",entity_type="service"}} {860 + int(elapsed / 60)}',
        f'ontology_entities_total{{service_name="ontology",entity_type="intent"}} {324 + int(elapsed / 120)}',
        '# HELP ontology_rules_total Current rules grouped by lifecycle state.',
        '# TYPE ontology_rules_total gauge',
        'ontology_rules_total{service_name="ontology",state="active"} 286',
        'ontology_rules_total{service_name="ontology",state="draft"} 31',
        'ontology_rules_total{service_name="ontology",state="disabled"} 12',
        '# HELP ontology_decisions_total Decisions produced by the rule engine.',
        '# TYPE ontology_decisions_total counter',
        f'ontology_decisions_total{{service_name="ontology",result="matched"}} {int(decision_total * 0.83)}',
        f'ontology_decisions_total{{service_name="ontology",result="fallback"}} {int(decision_total * 0.14)}',
        f'ontology_decisions_total{{service_name="ontology",result="rejected"}} {int(decision_total * 0.03)}',
        '# HELP ontology_answer_accuracy_ratio Human-evaluated answer accuracy.',
        '# TYPE ontology_answer_accuracy_ratio gauge',
        f'ontology_answer_accuracy_ratio{{service_name="ontology",dataset="golden-set"}} {0.925 + 0.012 * math.sin(elapsed / 90):.4f}',
        '# HELP ontology_recall_ratio Entity and rule retrieval recall.',
        '# TYPE ontology_recall_ratio gauge',
        f'ontology_recall_ratio{{service_name="ontology",dataset="golden-set"}} {0.887 + 0.018 * math.sin(elapsed / 75):.4f}',
        '# HELP ontology_groundedness_ratio Answers supported by retrieved evidence.',
        '# TYPE ontology_groundedness_ratio gauge',
        f'ontology_groundedness_ratio{{service_name="ontology"}} {0.944 + 0.009 * math.sin(elapsed / 110):.4f}',
        '# HELP ontology_hallucination_ratio Unsupported answer ratio.',
        '# TYPE ontology_hallucination_ratio gauge',
        f'ontology_hallucination_ratio{{service_name="ontology"}} {0.026 + 0.006 * (1 + math.sin(elapsed / 80)):.4f}',
        '# HELP ontology_safety_events_total Detected and blocked safety events.',
        '# TYPE ontology_safety_events_total counter',
        f'ontology_safety_events_total{{service_name="ontology",category="prompt_injection",severity="high"}} {int(18 + elapsed / 95)}',
        f'ontology_safety_events_total{{service_name="ontology",category="pii_exposure",severity="critical"}} {int(4 + elapsed / 330)}',
        f'ontology_safety_events_total{{service_name="ontology",category="unsafe_advice",severity="medium"}} {int(29 + elapsed / 75)}',
        f'ontology_safety_events_total{{service_name="ontology",category="policy_bypass",severity="high"}} {int(12 + elapsed / 140)}',
        '# HELP ontology_guardrail_block_ratio Fraction of requests blocked by guardrails.',
        '# TYPE ontology_guardrail_block_ratio gauge',
        f'ontology_guardrail_block_ratio{{service_name="ontology"}} {0.006 + 0.002 * (1 + math.sin(elapsed / 55)):.4f}',
        '# HELP ontology_cache_hit_ratio Cache hit ratio from zero to one.',
        '# TYPE ontology_cache_hit_ratio gauge',
        f'ontology_cache_hit_ratio{{service_name="ontology"}} {0.91 + 0.025 * math.sin(elapsed / 70):.4f}',
        '# HELP ontology_sync_lag_seconds Delay of the latest source synchronization.',
        '# TYPE ontology_sync_lag_seconds gauge',
        f'ontology_sync_lag_seconds{{service_name="ontology",source="catalog"}} {18 + 7 * (1 + wave):.2f}',
        f'ontology_sync_lag_seconds{{service_name="ontology",source="workorder"}} {31 + 11 * (1 + math.sin(elapsed / 60)):.2f}',
        '# HELP ontology_dependency_up Whether an Ontology dependency is healthy.',
        '# TYPE ontology_dependency_up gauge',
        'ontology_dependency_up{service_name="ontology",dependency="postgresql"} 1',
        'ontology_dependency_up{service_name="ontology",dependency="redis"} 1',
        'ontology_dependency_up{service_name="ontology",dependency="vector-store"} 1',
        'ontology_dependency_up{service_name="ontology",dependency="gfm"} 1',
    ])
    return "\n".join(lines) + "\n"


def post_otlp(path: str, payload: dict) -> None:
    request = Request(
        f"http://otel-collector:4318/v1/{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3):
        pass


def emit_telemetry() -> None:
    routes = ["POST /api/search", "GET /api/entities", "POST /api/decision"]
    while True:
        started = time.time_ns()
        duration_ms = random.choice([42, 58, 74, 96, 130, 210, 380])
        trace_id = secrets.token_hex(16)
        span_id = secrets.token_hex(8)
        route = random.choice(routes)
        unsafe = random.random() < 0.08
        status_code = 2 if unsafe else 1
        attributes = [
            {"key": "http.route", "value": {"stringValue": route.split(" ", 1)[1]}},
            {"key": "http.request.method", "value": {"stringValue": route.split(" ", 1)[0]}},
            {"key": "ontology.intent", "value": {"stringValue": random.choice(["part_search", "fault_diagnosis", "service_recommendation"])}},
            {"key": "ontology.grounded", "value": {"boolValue": not unsafe}},
        ]
        resource = {"attributes": [
            {"key": "service.name", "value": {"stringValue": "ontology"}},
            {"key": "service.namespace", "value": {"stringValue": "automotive"}},
            {"key": "deployment.environment.name", "value": {"stringValue": "demo"}},
        ]}
        trace = {"resourceSpans": [{"resource": resource, "scopeSpans": [{"scope": {"name": "ontology.demo"}, "spans": [{
            "traceId": trace_id, "spanId": span_id, "name": route, "kind": 2,
            "startTimeUnixNano": str(started), "endTimeUnixNano": str(started + duration_ms * 1_000_000),
            "attributes": attributes, "status": {"code": status_code, "message": "guardrail blocked request" if unsafe else ""},
        }]}]}]}
        message = "Guardrail blocked possible prompt injection" if unsafe else f"Ontology request completed in {duration_ms}ms"
        logs = {"resourceLogs": [{"resource": resource, "scopeLogs": [{"scope": {"name": "ontology.demo"}, "logRecords": [{
            "timeUnixNano": str(started + duration_ms * 1_000_000), "severityNumber": 17 if unsafe else 9,
            "severityText": "ERROR" if unsafe else "INFO", "body": {"stringValue": message},
            "traceId": trace_id, "spanId": span_id,
            "attributes": [{"key": "event.domain", "value": {"stringValue": "ontology"}}, {"key": "demo.data", "value": {"boolValue": True}}],
        }]}]}]}
        try:
            post_otlp("traces", trace)
            post_otlp("logs", logs)
        except Exception:
            pass
        time.sleep(3)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/metrics", "/health"):
            self.send_error(404)
            return
        body = ("ok\n" if self.path == "/health" else metric_payload()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


threading.Thread(target=emit_telemetry, daemon=True).start()
HTTPServer(("0.0.0.0", 9465), Handler).serve_forever()
