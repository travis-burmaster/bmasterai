# BMasterAI — Native OTLP Export

Send all bmasterai agent traces and metrics to any OpenTelemetry-compatible backend.

## Supported backends

| Backend | Transport | Notes |
|---|---|---|
| **Grafana Tempo** | gRPC or HTTP | Pairs with Grafana dashboards |
| **Jaeger** | gRPC | Open source distributed tracing |
| **Honeycomb** | HTTP | SaaS, needs API key header |
| **Datadog** | gRPC/HTTP | Via Datadog Agent OTLP ingestion |
| **New Relic** | HTTP | Needs license key header |
| **Prometheus** | HTTP | Via OTLP bridge receiver |
| **Local collector** | gRPC | `otel-collector` → any backend |

## Install

```bash
# gRPC (default, recommended)
pip install "bmasterai[otlp]"

# HTTP/protobuf (Honeycomb, New Relic, some SaaS)
pip install "bmasterai[otlp-http]"
```

## Usage

```python
from bmasterai import configure_otlp, get_monitor, configure_logging

# 1. Configure OTLP first (before any monitor calls)
configure_otlp(
    endpoint="http://localhost:4317",   # your collector endpoint
    service_name="my-ai-agent",
)

# 2. Use bmasterai normally — OTLP export happens automatically
configure_logging()
monitor = get_monitor()
monitor.start_monitoring()

monitor.track_agent_start("researcher")
monitor.track_llm_call("researcher", "claude-3-5-sonnet", tokens_used=1200, duration_ms=1840)
monitor.track_task_duration("researcher", "web_search", 620)
monitor.track_agent_stop("researcher")
```

## What gets exported

### Traces (spans)
| Span | Trigger | Attributes |
|---|---|---|
| `agent.<agent_id>` | `track_agent_start` / `track_agent_stop` | `bmasterai.agent_id`, `bmasterai.runtime_seconds` |
| `llm.call` | `track_llm_call` | `bmasterai.model`, `bmasterai.tokens_used`, `bmasterai.duration_ms`, `bmasterai.reasoning_steps` |
| `task.<task_name>` | `track_task_duration` | `bmasterai.agent_id`, `bmasterai.task_name`, `bmasterai.duration_ms` |

### Metrics
| Metric | Type | Labels |
|---|---|---|
| `bmasterai.llm.tokens_used` | Counter | `agent_id`, `model` |
| `bmasterai.llm.call_duration` | Histogram | `agent_id`, `model` |
| `bmasterai.task.duration` | Histogram | `agent_id`, `task_name` |
| `bmasterai.agent.errors` | Counter | `agent_id`, `error_type` |
| `bmasterai.custom.metric` | Counter | `metric_name` + any custom labels |

## Examples

### Local Jaeger (docker)
```bash
docker run -d --name jaeger \
  -p 4317:4317 -p 16686:16686 \
  jaegertracing/all-in-one:latest
```
```python
configure_otlp(endpoint="http://localhost:4317", service_name="my-agent")
```
Open http://localhost:16686 to see traces.

### Grafana Cloud
```python
configure_otlp(
    endpoint="https://otlp-gateway-prod-us-central-0.grafana.net/otlp",
    use_http=True,
    headers={
        "Authorization": "Basic <base64(instanceID:apikey)>",
    },
    service_name="my-agent",
    insecure=False,
)
```

### Honeycomb
```python
configure_otlp(
    endpoint="https://api.honeycomb.io",
    use_http=True,
    headers={"x-honeycomb-team": "YOUR_API_KEY"},
    service_name="my-agent",
)
```

### Datadog
```python
configure_otlp(
    endpoint="http://localhost:4317",  # Datadog Agent running locally
    service_name="my-agent",
)
```

## Run the example
```bash
pip install "bmasterai[otlp]"
python agent_with_otlp.py
```
