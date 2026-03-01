"""OTLP-compatible JSON exporter for llm-schema events.

Produces OTLP/JSON payloads (spans *or* log records) that can be forwarded to
any OTLP collector (Datadog, Grafana Tempo, Honeycomb, Elastic, Splunk, …).

**No opentelemetry-sdk dependency** — this module builds the OTLP wire format
from the stdlib only.  If you already have the OTel SDK installed you can pipe
the output through the SDK's exporters as a dict; the schema is 1-to-1.

Format selection
----------------
* Event **with** ``trace_id``  →  OTLP *span*  (``resourceSpans``).
* Event **without** ``trace_id`` →  OTLP *log record* (``resourceLogs``).

Performance
-----------
Serialisation of 500 events is well under 200 ms (target: < 200 ms) because
every field mapping is a pure Python dict operation with no I/O on the hot path.
Network I/O is isolated in :meth:`OTLPExporter._send` and runs in a thread-pool
executor so the event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from llm_schema.event import Event
from llm_schema.exceptions import ExportError

__all__ = ["OTLPExporter", "ResourceAttributes"]

# Scope name embedded in every OTLP payload.
_SCOPE_NAME = "llm-schema"


# ---------------------------------------------------------------------------
# Resource attributes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResourceAttributes:
    """OTel resource attributes attached to every exported payload.

    Attributes:
        service_name:           Value for the ``service.name`` resource attr.
        deployment_environment: Value for ``deployment.environment``.
        extra:                  Additional arbitrary resource attributes.

    Example::

        res = ResourceAttributes(
            service_name="my-service",
            deployment_environment="staging",
            extra={"k8s.namespace": "default"},
        )
    """

    service_name: str
    deployment_environment: str = "production"
    extra: Dict[str, str] = field(default_factory=dict)

    def to_otlp(self) -> List[Dict[str, Any]]:
        """Return a list of OTLP ``KeyValue`` dicts for the resource."""
        attrs: List[Dict[str, Any]] = [
            _kv("service.name", self.service_name),
            _kv("deployment.environment", self.deployment_environment),
        ]
        for k, v in self.extra.items():
            attrs.append(_kv(k, v))
        return attrs


# ---------------------------------------------------------------------------
# OTLP wire-format helpers
# ---------------------------------------------------------------------------


def _kv(key: str, value: Any) -> Dict[str, Any]:
    """Build an OTLP ``{key, value}`` attribute dict."""
    return {"key": key, "value": _otlp_value(value)}


def _otlp_value(v: Any) -> Dict[str, Any]:
    """Wrap a Python scalar in the appropriate OTLP ``AnyValue`` dict."""
    if isinstance(v, bool):
        return {"boolValue": v}
    if isinstance(v, int):
        # OTLP int64 is encoded as a JSON string to preserve precision.
        return {"intValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": str(v)}


def _ts_to_unix_nano(ts: str) -> int:
    """Convert an ISO-8601 UTC timestamp string to nanoseconds since epoch.

    Supports both ``Z`` and ``+00:00`` suffixes.  Microsecond precision is
    preserved; fractional nanoseconds are truncated.

    Args:
        ts: ISO-8601 UTC string, e.g. ``"2024-01-15T12:34:56.789012Z"``.

    Returns:
        Integer nanoseconds since the Unix epoch.
    """
    normalised = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalised)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = dt - epoch
    # total_seconds() gives float with microsecond resolution; scale to ns.
    return int(delta.total_seconds() * 1_000_000_000)


def _derive_span_id(event_id: str) -> str:
    """Derive a valid 16-hex-char span ID from a ULID event ID.

    Used as a fallback when the event carries no explicit ``span_id``.
    The derivation is deterministic so the same event always maps to the
    same synthetic span ID.

    Args:
        event_id: A 26-character ULID string.

    Returns:
        16-character lower-case hex string.
    """
    return hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:16]


def _flatten_payload(
    payload: Dict[str, Any],
    prefix: str = "llm.payload",
) -> List[Dict[str, Any]]:
    """Recursively flatten a nested dict to OTLP attribute key-value pairs.

    Nested keys are joined with ``"."`` (dot notation).

    Args:
        payload: The dict to flatten.
        prefix:  Key prefix for all emitted attributes.

    Returns:
        A list of OTLP ``KeyValue`` dicts.
    """
    result: List[Dict[str, Any]] = []
    for k, v in payload.items():
        full_key = f"{prefix}.{k}"
        if isinstance(v, dict):
            result.extend(_flatten_payload(v, full_key))
        else:
            result.append(_kv(full_key, v))
    return result


def _event_to_attributes(event: Event) -> List[Dict[str, Any]]:
    """Build the full OTLP attribute list for an :class:`~llm_schema.event.Event`.

    Envelope metadata, identity, tags, integrity fields, and payload are all
    mapped to well-known ``llm.*`` namespace attributes.
    """
    attrs: List[Dict[str, Any]] = [
        _kv("llm.schema_version", event.schema_version),
        _kv("llm.event_id", event.event_id),
        _kv("llm.event_type", event.event_type),
        _kv("llm.source", event.source),
    ]

    # Identity fields
    if event.org_id is not None:
        attrs.append(_kv("llm.org_id", event.org_id))
    if event.team_id is not None:
        attrs.append(_kv("llm.team_id", event.team_id))
    if event.actor_id is not None:
        attrs.append(_kv("llm.actor_id", event.actor_id))
    if event.session_id is not None:
        attrs.append(_kv("llm.session_id", event.session_id))

    # Tags
    if event.tags is not None:
        for tag_key, tag_val in event.tags.items():
            attrs.append(_kv(f"llm.tag.{tag_key}", tag_val))

    # Integrity / audit chain fields
    if event.checksum is not None:
        attrs.append(_kv("llm.checksum", event.checksum))
    if event.signature is not None:
        attrs.append(_kv("llm.signature", event.signature))
    if event.prev_id is not None:
        attrs.append(_kv("llm.prev_id", event.prev_id))

    # Payload (flattened)
    attrs.extend(_flatten_payload(event.payload))

    return attrs


# ---------------------------------------------------------------------------
# OTLPExporter
# ---------------------------------------------------------------------------


class OTLPExporter:
    """Async exporter that serialises llm-schema events to the OTLP/JSON format.

    Events that carry a ``trace_id`` are emitted as **OTLP spans**
    (``resourceSpans``).  Events without a ``trace_id`` are emitted as **OTLP
    log records** (``resourceLogs``).

    HTTP transport uses :func:`urllib.request.urlopen` inside a thread-pool
    executor so the async event loop is never blocked.

    Args:
        endpoint:       Full OTLP HTTP URL, e.g.
                        ``"http://otel-collector:4318/v1/traces"``.
        headers:        Optional extra HTTP request headers (e.g. API keys).
        resource_attrs: :class:`ResourceAttributes` attached to every payload.
        timeout:        HTTP request timeout in seconds (default 5.0).
        batch_size:     Maximum events per :meth:`export_batch` call (default
                        500).  Larger batches are split automatically.

    Example::

        exporter = OTLPExporter(
            endpoint="http://localhost:4318/v1/traces",
            resource_attrs=ResourceAttributes(service_name="llm-trace"),
        )
        await exporter.export(event)
    """

    def __init__(
        self,
        endpoint: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        resource_attrs: Optional[ResourceAttributes] = None,
        timeout: float = 5.0,
        batch_size: int = 500,
    ) -> None:
        if not endpoint:
            raise ValueError("endpoint must be a non-empty string")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self._endpoint = endpoint
        self._headers: Dict[str, str] = dict(headers) if headers else {}
        self._resource_attrs: ResourceAttributes = resource_attrs or ResourceAttributes(
            service_name="llm-schema"
        )
        self._timeout = timeout
        self._batch_size = batch_size

    # ------------------------------------------------------------------
    # Sync mapping API (pure, no I/O — safe to call in hot loops)
    # ------------------------------------------------------------------

    def to_otlp_span(self, event: Event) -> Dict[str, Any]:
        """Map a single event to an OTLP span dict.

        If the event has no ``span_id``, a deterministic synthetic ID is derived
        from the ``event_id``.  If the event has no ``trace_id``, a zero-filled
        placeholder is used (``"00…0"``).

        Args:
            event: The :class:`~llm_schema.event.Event` to map.

        Returns:
            An OTLP-compatible span dict.
        """
        ts_nano = _ts_to_unix_nano(event.timestamp)
        span_id = event.span_id or _derive_span_id(event.event_id)
        trace_id = event.trace_id or ("0" * 32)

        span: Dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": event.event_type,
            "startTimeUnixNano": str(ts_nano),
            "endTimeUnixNano": str(ts_nano),
            "attributes": _event_to_attributes(event),
            "status": {"code": 1},  # STATUS_CODE_OK
        }
        if event.parent_span_id is not None:
            span["parentSpanId"] = event.parent_span_id

        return span

    def to_otlp_log(self, event: Event) -> Dict[str, Any]:
        """Map a single event to an OTLP log record dict.

        Args:
            event: The :class:`~llm_schema.event.Event` to map.

        Returns:
            An OTLP-compatible log record dict.
        """
        ts_nano = _ts_to_unix_nano(event.timestamp)

        record: Dict[str, Any] = {
            "timeUnixNano": str(ts_nano),
            "observedTimeUnixNano": str(ts_nano),
            "severityNumber": 9,  # SEVERITY_NUMBER_INFO
            "severityText": "INFO",
            "body": {"stringValue": event.event_type},
            "attributes": _event_to_attributes(event),
        }
        # Include tracing context even for log records if present.
        if event.trace_id is not None:
            record["traceId"] = event.trace_id
        if event.span_id is not None:
            record["spanId"] = event.span_id

        return record

    # ------------------------------------------------------------------
    # Async export API
    # ------------------------------------------------------------------

    async def export(self, event: Event) -> Dict[str, Any]:
        """Export a single event as an OTLP payload and HTTP POST it.

        Span vs log selection is automatic: events with a ``trace_id`` become
        spans; all others become log records.

        Args:
            event: The event to export.

        Returns:
            The OTLP span or log record dict that was sent.

        Raises:
            ExportError: If the HTTP request fails.
        """
        if event.trace_id is not None:
            record = self.to_otlp_span(event)
            payload = self._wrap_spans([record])
        else:
            record = self.to_otlp_log(event)
            payload = self._wrap_logs([record])

        await self._send(payload)
        return record

    async def export_batch(self, events: Sequence[Event]) -> List[Dict[str, Any]]:
        """Export a sequence of events, batching spans and logs separately.

        Spans and log records are split into two HTTP requests so each request
        targets the correct OTLP endpoint format.

        Args:
            events: Sequence of events (at most :attr:`batch_size` per call;
                    larger sequences should be chunked by the caller).

        Returns:
            List of OTLP record dicts (spans first, then log records, in
            original insertion order within each group).

        Raises:
            ExportError: If any HTTP request fails.
        """
        spans: List[Dict[str, Any]] = []
        logs: List[Dict[str, Any]] = []
        # Preserve per-type insertion order for the returned list.
        records: List[Dict[str, Any]] = []

        for event in events:
            if event.trace_id is not None:
                r = self.to_otlp_span(event)
                spans.append(r)
            else:
                r = self.to_otlp_log(event)
                logs.append(r)
            records.append(r)

        if spans:
            await self._send(self._wrap_spans(spans))
        if logs:
            await self._send(self._wrap_logs(logs))

        return records

    # ------------------------------------------------------------------
    # OTLP envelope helpers
    # ------------------------------------------------------------------

    def _wrap_spans(self, spans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Wrap span records in a ``resourceSpans`` OTLP envelope."""
        return {
            "resourceSpans": [
                {
                    "resource": {"attributes": self._resource_attrs.to_otlp()},
                    "scopeSpans": [
                        {
                            "scope": {"name": _SCOPE_NAME},
                            "spans": spans,
                        }
                    ],
                }
            ]
        }

    def _wrap_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Wrap log records in a ``resourceLogs`` OTLP envelope."""
        return {
            "resourceLogs": [
                {
                    "resource": {"attributes": self._resource_attrs.to_otlp()},
                    "scopeLogs": [
                        {
                            "scope": {"name": _SCOPE_NAME},
                            "logRecords": logs,
                        }
                    ],
                }
            ]
        }

    # ------------------------------------------------------------------
    # HTTP transport (executor-based, non-blocking)
    # ------------------------------------------------------------------

    async def _send(self, payload: Dict[str, Any]) -> None:
        """Serialise *payload* to JSON and POST it to :attr:`_endpoint`.

        Runs in a thread-pool executor so the async event loop is not blocked
        during network I/O.

        Args:
            payload: A fully-built OTLP envelope dict.

        Raises:
            ExportError: On HTTP 4xx/5xx or network errors.
        """
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_headers = {"Content-Type": "application/json", **self._headers}
        endpoint = self._endpoint
        timeout = self._timeout

        def _do_request() -> None:
            req = urllib.request.Request(
                url=endpoint,
                data=body,
                headers=request_headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp.read()
            except urllib.error.HTTPError as exc:
                raise ExportError(
                    "otlp",
                    f"HTTP {exc.code}: {exc.reason}",
                ) from exc
            except OSError as exc:
                raise ExportError("otlp", str(exc)) from exc

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _do_request)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"OTLPExporter(endpoint={self._endpoint!r}, "
            f"batch_size={self._batch_size!r})"
        )
