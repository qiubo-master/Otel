# 通用 OpenTelemetry 可观测平台

一套面向全项目的本地/单机可部署观测栈，统一接收 OpenTelemetry trace、metrics、logs，同时提供 Prometheus 指标库、ELK 日志聚合和 Grafana 看板。已预置平台健康、CICD 中台与 Media 三类视图。

[平台操作手册](docs/OPERATIONS.md) · [新项目接入指南](docs/ONBOARDING.md) · [生产化清单](docs/PRODUCTION.md)

## 架构

```text
Applications / CI jobs / Media workers
                 |
          OTLP gRPC / HTTP
                 v
       OpenTelemetry Collector
          /        |         \
     traces      metrics      logs
       v            v           v
     Tempo      Prometheus  Elasticsearch
       \            |           /
        +-------- Grafana ------+
                             Kibana (log ops)

Legacy JSON logs -> Logstash -> Elasticsearch
Host / containers -> node-exporter / cAdvisor -> Prometheus
```

## 快速启动

依赖 Docker Engine 24+ 与 Docker Compose v2，建议至少 4 CPU、8 GB 内存。

```bash
cp .env.example .env
# 修改 .env 中默认密码
docker compose up -d
docker compose ps
./scripts/smoke-test.sh
```

入口与 UI：

| 服务 | 地址 | 用途 |
|---|---|---|
| OTLP gRPC | `localhost:4317` | 推荐应用入口 |
| OTLP HTTP | `http://localhost:4318` | 浏览器/HTTP 入口 |
| Grafana | `http://localhost:3000` | 统一看板、trace、日志 |
| Prometheus | `http://localhost:9090` | PromQL 与告警规则 |
| Kibana | `http://localhost:5601` | ELK 日志检索 |
| Elasticsearch | `http://localhost:9200` | 日志 API |
| Tempo | `http://localhost:3200` | Trace API |
| Collector health | `http://localhost:13133` | 健康检查 |

Grafana 登录账号来自 `.env`。Dashboard 会自动加载到 `OpenTelemetry` 文件夹。

## 数据流与默认保留

- Trace：OTLP → Collector → Tempo，本地默认保留 7 天；Tempo 自动生成 span metrics 和 service graph，并 remote-write 到 Prometheus。
- Metrics：OTLP → Collector Prometheus exporter → Prometheus，默认保留 30 天；同时采集节点、容器和平台自身指标。
- Logs：OTLP → Collector → Elasticsearch 的 `otel-logs*` 索引；传统 JSON 日志可经 TCP/UDP `15000`（可由 `LOGSTASH_TCP_PORT` 修改）或 Beats `5044` 进入 `app-logs-*`。
- Grafana 数据源和 trace-to-metrics、trace-to-logs 跳转均自动 provision。

## 新项目接入

最小配置如下；详细的 Java、Node.js、Python、.NET、Go、CICD 和指标规范见 [接入指南](docs/ONBOARDING.md)。

```bash
export OTEL_SERVICE_NAME=my-service
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-platform:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_RESOURCE_ATTRIBUTES=service.namespace=my-domain,service.version=1.0.0,deployment.environment.name=prod,team=my-team
```

生产部署前请阅读 [生产化清单](docs/PRODUCTION.md)。

## 运维命令

```bash
make init       # 生成 .env
make up         # 启动
make ps         # 查看状态
make logs       # 跟随日志
make validate   # 静态检查 Compose 和 Dashboard
make smoke      # 发送一条关联 trace + log
make down       # 停止
make clean      # 停止并删除数据卷（不可恢复）
```

## 目录

```text
config/otel-collector.yaml             遥测入口、处理和路由
config/prometheus/                     抓取配置与告警规则
config/tempo.yaml                      Trace 存储与指标生成
config/logstash/pipeline.conf          传统日志管道
config/grafana/provisioning/           自动数据源与 Dashboard 装载
config/grafana/dashboards/             Platform / Service / CICD / Media 看板
docs/ONBOARDING.md                     新项目接入规范
docs/PRODUCTION.md                     生产化安全与扩展建议
scripts/                               配置校验和冒烟测试
```

## 安全说明

为了开箱即用，本地 Compose 中 Elasticsearch 安全认证默认关闭，OTLP 入口也未启用 TLS。这些默认值不能直接用于公网或生产环境；生产要求见清单。
