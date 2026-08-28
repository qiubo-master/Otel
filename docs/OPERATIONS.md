# Otel 平台操作手册

本文面向通过 ForgeOps CICD 中台管理 Otel 平台的运维人员。

## 访问入口

| 功能 | 默认地址 | 用途 |
|---|---|---|
| Grafana | `http://部署服务器:3000` | 统一看板、Trace 与日志关联查询 |
| Prometheus | `http://部署服务器:9090` | PromQL、Targets 与告警规则 |
| Kibana | `http://部署服务器:5601` | Elasticsearch 日志检索 |
| Elasticsearch | `http://部署服务器:9200` | 日志索引 API |
| Tempo | `http://部署服务器:3200` | Trace 查询 API |
| OTLP gRPC | `部署服务器:4317` | 服务端推荐接入地址 |
| OTLP HTTP | `http://部署服务器:4318` | HTTP/浏览器遥测入口 |
| 健康检查 | `http://部署服务器:13133` | Collector 发布验收 |

生产环境应通过内网负载均衡、域名和 TLS 暴露入口，不应直接开放全部端口到公网。

## 从 CICD 中台发布

1. 进入 ForgeOps 的“项目管理”，选择 `Otel 可观测平台`。
2. 在“版本发布”中选择 `main` 分支和目标服务器。
3. 初次部署建议选择 `large` 资源规格。
4. 点击发布，流水线依次执行配置校验、打包、上传、拉取镜像、启动和健康检查。
5. 发布成功后点击项目描述下方的“操作手册”或“访问平台”。

项目 production environment 需要配置：

- `DEPLOY_HOST`：部署服务器地址。
- `DEPLOY_PORT`：SSH 端口。
- `DEPLOY_USER`：SSH 用户。
- `DEPLOY_SSH_KEY`：部署私钥。
- `DEPLOY_HOST_KEY`：目标服务器 `known_hosts` 记录。

## 启动、停止与检查

在服务器当前版本目录执行：

```bash
docker compose up -d
docker compose ps
./scripts/smoke-test.sh
docker compose logs -f --tail=200
```

停止但保留数据：

```bash
docker compose down
```

不要在生产环境执行 `docker compose down -v`，该命令会删除 Prometheus、Tempo、Elasticsearch 和 Grafana 数据卷。

## 发布验收

1. Collector 健康检查返回 `Server available`。
2. Prometheus `/targets` 中所有目标均为 `UP`。
3. Grafana 可以看到 Platform、CICD、Media 三个 Dashboard。
4. 执行冒烟测试后，Tempo 能查到 Trace ID，Elasticsearch `otel-logs` 索引新增日志。
5. Trace 页面可以跳转到相同 Trace ID 的日志。

## 常见故障

### 端口被占用

检查 `3000`、`4317`、`4318`、`5601`、`9090`、`9200`、`13133`、`15000`。传统 Logstash TCP/UDP 入口可通过 `.env` 的 `LOGSTASH_TCP_PORT` 修改。

### Elasticsearch 无法健康

确认服务器至少有 8 GB 可用内存和足够磁盘；检查 `docker compose logs elasticsearch`。生产环境建议将 JVM 和数据卷迁移到专用资源。

### Collector 有导出失败

查看 `otelcol_exporter_send_failed_*` 指标，并分别检查 Tempo、Elasticsearch 和 Prometheus 的网络、磁盘与健康状态。

### 回滚

在 CICD 中台选择 `rollback`。流水线会切换到上一份服务器 release 并重新执行 `docker compose up -d`。数据卷不随应用版本回滚。

## 新项目接入

应用接入所需的资源属性、SDK 和各语言自动探针配置见 [新项目接入指南](ONBOARDING.md)。

