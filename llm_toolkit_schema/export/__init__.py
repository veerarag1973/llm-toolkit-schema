"""Export backends for llm-toolkit-schema events.

All exporters are **opt-in** — importing this package does not open any network
connections or file handles.  Instantiate an exporter explicitly to activate it.

Available exporters
-------------------
* :class:`~llm_toolkit_schema.export.otlp.OTLPExporter` — OTLP/JSON HTTP exporter
  (zero dependencies; builds OTLP wire format from stdlib).
* :class:`~llm_toolkit_schema.export.otel_bridge.OTelBridgeExporter` — OpenTelemetry
  SDK bridge that emits real OTel spans via a configured ``TracerProvider``.
  Requires ``pip install "llm-toolkit-schema[otel]"``.
* :class:`~llm_toolkit_schema.export.webhook.WebhookExporter` — HTTP with HMAC-SHA256
  request signing.
* :class:`~llm_toolkit_schema.export.jsonl.JSONLExporter` — newline-delimited JSON for
  local development and audit trails.
* :class:`~llm_toolkit_schema.export.datadog.DatadogExporter` — Datadog APM traces +
  custom metrics via the Datadog Agent.
* :class:`~llm_toolkit_schema.export.grafana.GrafanaLokiExporter` — Grafana Loki push
  exporter for structured log delivery.

W3C TraceContext utilities
--------------------------
* :func:`~llm_toolkit_schema.export.otlp.make_traceparent` — build a ``traceparent``
  header value for outgoing HTTP request propagation.
* :func:`~llm_toolkit_schema.export.otlp.extract_trace_context` — parse a
  ``traceparent`` / ``tracestate`` header dict into trace context fields.

All exporters are async by default; every ``export`` / ``export_batch`` method
is a coroutine.

Usage example::

    from llm_toolkit_schema.export import JSONLExporter

    async with JSONLExporter("events.jsonl") as exporter:
        await exporter.export(event)
"""

from __future__ import annotations

from llm_toolkit_schema.export.datadog import DatadogExporter, DatadogResourceAttributes
from llm_toolkit_schema.export.grafana import GrafanaLokiExporter
from llm_toolkit_schema.export.jsonl import JSONLExporter
from llm_toolkit_schema.export.otlp import OTLPExporter, ResourceAttributes
from llm_toolkit_schema.export.webhook import WebhookExporter

__all__ = [
    "OTLPExporter",
    "ResourceAttributes",
    "WebhookExporter",
    "JSONLExporter",
    "DatadogExporter",
    "DatadogResourceAttributes",
    "GrafanaLokiExporter",
]
