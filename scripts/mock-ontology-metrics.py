#!/usr/bin/env python3
"""Small dependency-free Prometheus endpoint for the Ontology demo dashboard."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import math
import time

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


HTTPServer(("0.0.0.0", 9465), Handler).serve_forever()
