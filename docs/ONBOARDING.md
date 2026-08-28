# 新项目接入指南

平台只暴露一个遥测入口，应用统一发送 OTLP：gRPC `4317` 或 HTTP `4318`。生产环境建议将入口放在内网负载均衡后，并启用 TLS/鉴权。

## 1. 必填资源属性

每个服务至少设置以下属性，平台才能按项目、环境和版本聚合：

| 属性 | 示例 | 说明 |
|---|---|---|
| `service.name` | `media-transcoder` | 稳定、唯一的服务名 |
| `service.namespace` | `media` | 业务域，如 `cicd`、`media` |
| `service.version` | `1.8.2` | 构建版本或 Git SHA |
| `deployment.environment.name` | `prod` | `dev`、`staging`、`prod` |
| `team` | `video-platform` | 责任团队 |

通用环境变量：

```bash
OTEL_SERVICE_NAME=media-transcoder
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel.example.internal:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_RESOURCE_ATTRIBUTES=service.namespace=media,service.version=${GIT_SHA},deployment.environment.name=prod,team=video-platform
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1
OTEL_METRIC_EXPORT_INTERVAL=15000
```

容器与 Collector 同一 Compose 网络时，入口使用 `http://otel-collector:4317`；Kubernetes 中使用 Collector Service DNS。

## 2. 零代码自动探针

### Java

```bash
java -javaagent:/opt/opentelemetry-javaagent.jar -jar app.jar
```

### Node.js

```bash
NODE_OPTIONS="--require @opentelemetry/auto-instrumentations-node/register" node server.js
```

### Python

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
opentelemetry-instrument python app.py
```

### .NET

安装 `OpenTelemetry.AutoInstrumentation` 后，通过启动脚本注入：

```bash
. /otel-dotnet-auto/instrument.sh
dotnet MyService.dll
```

### Go

Go 建议使用官方 OTel SDK，在入口、中间件、数据库和消息消费处显式埋点。务必将请求 `context.Context` 传递到下游。

## 3. 日志关联

应用日志必须为 JSON，至少包含 `timestamp`、`severity`、`message`、`service.name`。使用 OTel Logging SDK 时，日志会自动携带当前 `trace_id` 和 `span_id`；原有 Filebeat 日志可发送至 Logstash `5044`，但需要在应用 formatter 中注入这两个字段。

## 4. 业务指标约定

名称使用小写 snake_case，单位放在后缀，标签只使用低基数字段，禁止把用户 ID、任务 ID、URL 原文作为标签。

CICD 看板约定：

- `cicd_pipeline_runs_total{project,pipeline,status,branch}`
- `cicd_pipeline_duration_seconds`（Histogram）
- `cicd_deployments_total{project,environment,status}`

Media 看板约定：

- `media_jobs_total{job_type,status}`
- `media_processing_duration_seconds{job_type}`（Histogram）
- `media_queue_depth{queue}`（Gauge）
- `media_input_bytes_total`、`media_output_bytes_total`

## 5. CICD 接入模板

在部署变量中注入提交版本：

```yaml
env:
  OTEL_SERVICE_NAME: ${{ github.event.repository.name }}
  OTEL_EXPORTER_OTLP_ENDPOINT: https://otel.example.internal:4317
  OTEL_RESOURCE_ATTRIBUTES: service.namespace=cicd,service.version=${{ github.sha }},deployment.environment.name=prod,team=platform
```

流水线结束时由任务本身通过 OTel SDK 上报 `cicd_pipeline_runs_total` 和 duration histogram；不要从 GitHub/GitLab 的高基数任务 ID 派生 label。

## 6. 接入验收

1. Grafana Explore 中按 `service.name` 搜到 trace。
2. trace 详情能跳转到相同 `trace_id` 的日志。
3. Prometheus 查询 `otelcol_receiver_accepted_*` 持续增长。
4. 业务指标存在且无高基数标签。
5. 模拟错误后能在日志和 trace 中看到一致错误，并验证告警路由。

