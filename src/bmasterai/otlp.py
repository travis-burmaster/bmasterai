"""
BMasterAI — Native OTLP (OpenTelemetry Protocol) Export Layer

Wraps bmasterai agent events into OTel traces and metrics, then exports via OTLP
to any compatible backend: Grafana Tempo, Jaeger, Honeycomb, Datadog, New Relic,
Prometheus (via OTLP bridge), or a local collector.

Usage:
    from bmasterai.otlp import configure_otlp

    # gRPC (default OTLP)
    configure_otlp(endpoint="http://localhost:4317")

    # HTTP/protobuf
    configure_otlp(endpoint="http://localhost:4318", use_http=True)

    # With auth headers (Honeycomb, Grafana Cloud, etc.)
    configure_otlp(
        endpoint="https://api.honeycomb.io",
        headers={"x-honeycomb-team": "YOUR_API_KEY"},
        service_name="my-ai-agent",
    )

After configure_otlp() is called, all bmasterai monitor calls automatically emit spans:
    - agent_start / agent_stop  → root span per agent lifecycle
    - track_llm_call            → child span with token/latency attributes
    - track_task_duration       → child span per task
    - track_error               → span event with error details
    - record_custom_metric      → OTel counter/histogram via metrics API

Requires:
    pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
    # or for HTTP:
    pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# ── Availability check ─────────────────────────────────────────────────────────

try:
    from opentelemetry import trace, metrics as otel_metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False

_otlp_configured = False
_tracer: Optional[Any] = None
_meter: Optional[Any] = None

# Active spans keyed by agent_id for lifecycle tracking
_agent_spans: Dict[str, Any] = {}

# Metric instruments (created once)
_instruments: Dict[str, Any] = {}


def is_available() -> bool:
    """Return True if opentelemetry-sdk is installed."""
    return _OTEL_AVAILABLE


def configure_otlp(
    endpoint: str = "http://localhost:4317",
    service_name: str = "bmasterai",
    service_version: str = "0.2.3",
    use_http: bool = False,
    headers: Optional[Dict[str, str]] = None,
    export_interval_ms: int = 5000,
    insecure: bool = True,
) -> bool:
    """
    Configure native OTLP export for all bmasterai monitor calls.

    Parameters
    ----------
    endpoint : str
        OTLP collector endpoint.
        gRPC default: ``http://localhost:4317``
        HTTP default: ``http://localhost:4318``
    service_name : str
        ``service.name`` resource attribute sent with every span/metric.
    service_version : str
        ``service.version`` resource attribute.
    use_http : bool
        Use HTTP/protobuf transport instead of gRPC.
        Requires ``opentelemetry-exporter-otlp-proto-http``.
    headers : dict, optional
        Extra headers for authenticated SaaS backends (Honeycomb, Grafana Cloud, etc.).
    export_interval_ms : int
        How often to flush metrics (milliseconds). Default 5 000.
    insecure : bool
        Allow plaintext gRPC (no TLS). Set False for production TLS endpoints.

    Returns
    -------
    bool
        True if configuration succeeded, False if opentelemetry-sdk is missing.
    """
    global _otlp_configured, _tracer, _meter, _instruments

    if not _OTEL_AVAILABLE:
        logger.warning(
            "opentelemetry-sdk not installed. "
            "Run: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
        )
        return False

    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: service_version,
        "bmasterai.version": service_version,
    })

    # ── Tracer provider ────────────────────────────────────────────────────────
    if use_http:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        except ImportError:
            logger.error(
                "HTTP exporter not available. "
                "Run: pip install opentelemetry-exporter-otlp-proto-http"
            )
            return False
        span_exporter = OTLPSpanExporter(
            endpoint=f"{endpoint.rstrip('/')}/v1/traces",
            headers=headers or {},
        )
    else:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        except ImportError:
            logger.error(
                "gRPC exporter not available. "
                "Run: pip install opentelemetry-exporter-otlp-proto-grpc"
            )
            return False
        span_exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers or {},
            insecure=insecure,
        )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer("bmasterai", service_version)

    # ── Meter provider ─────────────────────────────────────────────────────────
    try:
        if use_http:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            metric_exporter = OTLPMetricExporter(
                endpoint=f"{endpoint.rstrip('/')}/v1/metrics",
                headers=headers or {},
            )
        else:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
            metric_exporter = OTLPMetricExporter(
                endpoint=endpoint,
                headers=headers or {},
                insecure=insecure,
            )

        reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=export_interval_ms,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        otel_metrics.set_meter_provider(meter_provider)
        _meter = otel_metrics.get_meter("bmasterai", service_version)

        # Pre-create instruments
        _instruments["llm_tokens"] = _meter.create_counter(
            "bmasterai.llm.tokens_used",
            unit="tokens",
            description="Total LLM tokens consumed per agent/model",
        )
        _instruments["llm_duration"] = _meter.create_histogram(
            "bmasterai.llm.call_duration",
            unit="ms",
            description="LLM call latency in milliseconds",
        )
        _instruments["task_duration"] = _meter.create_histogram(
            "bmasterai.task.duration",
            unit="ms",
            description="Agent task execution duration in milliseconds",
        )
        _instruments["agent_errors"] = _meter.create_counter(
            "bmasterai.agent.errors",
            unit="1",
            description="Total agent errors by type",
        )
        _instruments["custom_counter"] = _meter.create_counter(
            "bmasterai.custom.metric",
            description="Custom metrics emitted via record_custom_metric",
        )
    except Exception as exc:
        logger.warning("Metrics OTLP setup failed (traces still active): %s", exc)
        _meter = None

    _otlp_configured = True
    logger.info("BMasterAI OTLP configured → %s (transport=%s)", endpoint, "http" if use_http else "grpc")
    return True


# ── Instrumentation hooks (called by AgentMonitor) ────────────────────────────

def on_agent_start(agent_id: str, attributes: Optional[Dict[str, Any]] = None):
    """Open a root span for an agent lifecycle. Called by AgentMonitor.track_agent_start."""
    if not _otlp_configured or _tracer is None:
        return
    span = _tracer.start_span(
        f"agent.{agent_id}",
        attributes={
            "bmasterai.agent_id": agent_id,
            **(attributes or {}),
        },
    )
    _agent_spans[agent_id] = span


def on_agent_stop(agent_id: str, runtime_seconds: Optional[float] = None):
    """Close the root span for an agent. Called by AgentMonitor.track_agent_stop."""
    if not _otlp_configured:
        return
    span = _agent_spans.pop(agent_id, None)
    if span is not None:
        if runtime_seconds is not None:
            span.set_attribute("bmasterai.runtime_seconds", runtime_seconds)
        span.end()


def on_llm_call(
    agent_id: str,
    model: str,
    tokens_used: int,
    duration_ms: float,
    reasoning_steps: Optional[int] = None,
    thinking_depth: Optional[int] = None,
):
    """Emit a child span + metrics for an LLM call."""
    if not _otlp_configured:
        return

    attrs = {
        "bmasterai.agent_id": agent_id,
        "bmasterai.model": model,
        "bmasterai.tokens_used": tokens_used,
        "bmasterai.duration_ms": duration_ms,
    }
    if reasoning_steps is not None:
        attrs["bmasterai.reasoning_steps"] = reasoning_steps
    if thinking_depth is not None:
        attrs["bmasterai.thinking_depth"] = thinking_depth

    if _tracer:
        parent_span = _agent_spans.get(agent_id)
        ctx = trace.set_span_in_context(parent_span) if parent_span else None
        with _tracer.start_as_current_span("llm.call", context=ctx, attributes=attrs):
            pass  # span closes immediately — duration captured as attribute

    if _meter and _instruments:
        label = {"agent_id": agent_id, "model": model}
        _instruments["llm_tokens"].add(tokens_used, label)
        _instruments["llm_duration"].record(duration_ms, label)


def on_task_duration(agent_id: str, task_name: str, duration_ms: float):
    """Emit a child span + histogram for a task."""
    if not _otlp_configured:
        return

    attrs = {
        "bmasterai.agent_id": agent_id,
        "bmasterai.task_name": task_name,
        "bmasterai.duration_ms": duration_ms,
    }

    if _tracer:
        parent_span = _agent_spans.get(agent_id)
        ctx = trace.set_span_in_context(parent_span) if parent_span else None
        with _tracer.start_as_current_span(f"task.{task_name}", context=ctx, attributes=attrs):
            pass

    if _meter and _instruments:
        _instruments["task_duration"].record(
            duration_ms, {"agent_id": agent_id, "task_name": task_name}
        )


def on_error(agent_id: str, error_type: str):
    """Increment error counter and add event to active agent span."""
    if not _otlp_configured:
        return

    if _meter and _instruments:
        _instruments["agent_errors"].add(1, {"agent_id": agent_id, "error_type": error_type})

    span = _agent_spans.get(agent_id)
    if span:
        span.add_event("error", {"bmasterai.error_type": error_type})


def on_custom_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Forward a custom metric to OTel as a counter increment."""
    if not _otlp_configured or _meter is None or not _instruments:
        return
    try:
        _instruments["custom_counter"].add(value, {**(labels or {}), "metric_name": name})
    except Exception:
        pass
