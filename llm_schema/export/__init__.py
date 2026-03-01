"""Export backends for llm-schema events.

All exporters are **opt-in** — importing this package does not open any network
connections or file handles.  Instantiate an exporter explicitly to activate it.

Available exporters
-------------------
* :class:`~llm_schema.export.otlp.OTLPExporter` — OTLP-compatible JSON/HTTP.
* :class:`~llm_schema.export.webhook.WebhookExporter` — HTTP with HMAC-SHA256
  request signing.
* :class:`~llm_schema.export.jsonl.JSONLExporter` — newline-delimited JSON for
  local development and audit trails.

All exporters are async by default; every ``export`` / ``export_batch`` method
is a coroutine.

Usage example::

    from llm_schema.export import JSONLExporter

    async with JSONLExporter("events.jsonl") as exporter:
        await exporter.export(event)
"""

from __future__ import annotations

from llm_schema.export.jsonl import JSONLExporter
from llm_schema.export.otlp import OTLPExporter, ResourceAttributes
from llm_schema.export.webhook import WebhookExporter

__all__ = [
    "OTLPExporter",
    "ResourceAttributes",
    "WebhookExporter",
    "JSONLExporter",
]
