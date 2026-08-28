# 生产化清单

当前 Compose 方案适合开发、演示和单机中小规模部署。正式生产需完成：

- 将 Elasticsearch、Tempo、Prometheus 改为多副本或托管服务，并把本地卷改为云盘/对象存储。
- 在 OTLP 入口前配置内网 LB、TLS、mTLS 或 API Key；不要直接暴露 `4317/4318` 到公网。
- Elasticsearch 开启安全功能和账号权限；Grafana 接入 SSO，并按团队配置 Folder 权限。
- 按容量调整 Collector 的 `memory_limiter`、batch、队列与副本数；Collector 建议 gateway 与 agent 分层。
- 为 Elasticsearch 配置 ILM，为 Prometheus/Tempo 配置实际保留期和对象存储生命周期。
- 增加 Alertmanager 或 Grafana Alerting 联系点，将告警路由到值班系统。
- 备份 Grafana 配置、Dashboard JSON 与索引模板；定期执行恢复演练。
- 对敏感属性使用 Collector `attributes`/`redaction` processor 脱敏，禁止采集 Token、密码和完整请求体。

粗略容量估算需要以压测为准：trace 存储量约为 `请求量 × 采样率 × 每条 trace 平均字节数 × 保留时间`；日志通常是最大成本项，应先控制日志等级和字段体积。

