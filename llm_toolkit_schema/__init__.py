"""llm-toolkit-schema — Shared Event Schema for the LLM Developer Toolkit.

This package provides the foundational event contract used by every tool in
the LLM Developer Toolkit.  It is OpenTelemetry-compatible, versioned, and
designed for enterprise-grade observability.

Quick start
-----------
::

    from llm_toolkit_schema import Event, EventType, Tags

    event = Event(
        event_type=EventType.TRACE_SPAN_COMPLETED,
        source="llm-trace@0.3.1",
        payload={"span_name": "run_agent", "status": "ok"},
        tags=Tags(env="production", model="gpt-4o"),
    )
    event.validate()
    print(event.to_json())

PII redaction (v0.2+)
---------------------
::

    from llm_toolkit_schema import Event, EventType
    from llm_toolkit_schema.redact import Redactable, RedactionPolicy, Sensitivity

    policy = RedactionPolicy(min_sensitivity=Sensitivity.PII, redacted_by="policy:corp")
    event = Event(
        event_type=EventType.PROMPT_SAVED,
        source="promptlock@1.0.0",
        payload={"author": Redactable("alice@example.com", Sensitivity.PII, {"email"})},
    )
    result = policy.apply(event)

Pydantic models (optional, requires pydantic>=2.7)
--------------------------------------------------
::

    from llm_toolkit_schema.models import EventModel
    model = EventModel.from_event(event)
    print(model.model_json_schema())

HMAC signing & audit chain (v0.3+)
-----------------------------------
::

    from llm_toolkit_schema.signing import sign, verify, verify_chain, AuditStream

    # Sign individual events
    signed = sign(event, org_secret="my-secret")
    assert verify(signed, org_secret="my-secret")

    # Build a tamper-evident chain
    stream = AuditStream(org_secret="my-secret", source="signing-daemon@1.0.0")
    for evt in events:
        stream.append(evt)
    result = stream.verify()
    assert result.valid

Public API
----------
The following names are the stable, supported public interface.

* :class:`~llm_toolkit_schema.event.Event`
* :class:`~llm_toolkit_schema.event.Tags`
* :class:`~llm_toolkit_schema.types.EventType`
* :data:`~llm_toolkit_schema.event.SCHEMA_VERSION`
* :func:`~llm_toolkit_schema.ulid.generate`
* :func:`~llm_toolkit_schema.ulid.validate`
* :func:`~llm_toolkit_schema.ulid.extract_timestamp_ms`
* :func:`~llm_toolkit_schema.types.is_registered`
* :func:`~llm_toolkit_schema.types.namespace_of`
* :func:`~llm_toolkit_schema.types.validate_custom`
* :func:`~llm_toolkit_schema.types.get_by_value`
* :class:`~llm_toolkit_schema.exceptions.LLMSchemaError`
* :class:`~llm_toolkit_schema.exceptions.SchemaValidationError`
* :class:`~llm_toolkit_schema.exceptions.ULIDError`
* :class:`~llm_toolkit_schema.exceptions.SerializationError`
* :class:`~llm_toolkit_schema.exceptions.DeserializationError`
* :class:`~llm_toolkit_schema.exceptions.EventTypeError`
* :class:`~llm_toolkit_schema.exceptions.SigningError`
* :class:`~llm_toolkit_schema.exceptions.VerificationError`
* :class:`~llm_toolkit_schema.redact.Sensitivity`
* :class:`~llm_toolkit_schema.redact.Redactable`
* :class:`~llm_toolkit_schema.redact.RedactionPolicy`
* :class:`~llm_toolkit_schema.redact.RedactionResult`
* :class:`~llm_toolkit_schema.redact.PIINotRedactedError`
* :func:`~llm_toolkit_schema.redact.contains_pii`
* :func:`~llm_toolkit_schema.redact.assert_redacted`
* :func:`~llm_toolkit_schema.signing.sign`
* :func:`~llm_toolkit_schema.signing.verify`
* :func:`~llm_toolkit_schema.signing.verify_chain`
* :func:`~llm_toolkit_schema.signing.assert_verified`
* :class:`~llm_toolkit_schema.signing.ChainVerificationResult`
* :class:`~llm_toolkit_schema.signing.AuditStream`
* :class:`~llm_toolkit_schema.export.otlp.OTLPExporter`
* :class:`~llm_toolkit_schema.export.otlp.ResourceAttributes`
* :class:`~llm_toolkit_schema.export.webhook.WebhookExporter`
* :class:`~llm_toolkit_schema.export.jsonl.JSONLExporter`
* :class:`~llm_toolkit_schema.stream.EventStream`
* :class:`~llm_toolkit_schema.stream.Exporter`
* :class:`~llm_toolkit_schema.exceptions.ExportError`
* :func:`~llm_toolkit_schema.validate.validate_event`
* Namespace payloads (v0.5): :mod:`llm_toolkit_schema.namespaces` — see sub-module
  docs for :class:`~llm_toolkit_schema.namespaces.trace.SpanCompletedPayload`
  (**FROZEN v1**), :class:`~llm_toolkit_schema.namespaces.cost.CostRecordedPayload`,
  :class:`~llm_toolkit_schema.namespaces.eval_.EvalScenarioPayload`, and all others.
* Runtime enforcement policies (v1.1.1):
  :class:`~llm_toolkit_schema.namespaces.guard.GuardPolicy`,
  :class:`~llm_toolkit_schema.namespaces.fence.FencePolicy`,
  :class:`~llm_toolkit_schema.namespaces.template.TemplatePolicy`
* Streaming generators (v1.1.1):
  :func:`~llm_toolkit_schema.stream.iter_file`,
  :func:`~llm_toolkit_schema.stream.aiter_file`

Version history
---------------
v0.1 — Core ``Event``, ``EventType``, ULID, JSON serialisation, validation.
        Zero external dependencies.
v0.2 — PII redaction framework (``Redactable``, ``RedactionPolicy``,
        ``Sensitivity``).  Pydantic v2 model layer (``llm_toolkit_schema.models``).
v0.3 — HMAC-SHA256 signing (``sign``, ``verify``), tamper-evident audit chain
        (``verify_chain``, ``AuditStream``), key rotation, gap detection.
v0.4 — OTLP/JSON export (``OTLPExporter``), HTTP webhook export
        (``WebhookExporter``), JSONL file export (``JSONLExporter``),
        ``EventStream`` with filtering and routing.
v0.5 — Namespace payload dataclasses for all 10 reserved namespaces
        (``llm_toolkit_schema.namespaces``).  Published JSON Schema
        (``schemas/v1.0/schema.json``).  ``validate_event()`` for schema
        validation with optional ``jsonschema`` backend.
v1.0 — Production-ready GA release.  Compliance toolkit
        (``llm_toolkit_schema.compliance``) with multi-tenant isolation checks,
        audit chain integrity verification, and third-party compatibility
        checker.  Migration scaffold ``llm_toolkit_schema.migrate.v1_to_v2``.
        ``llm-toolkit-schema check-compat`` CLI command.
v1.1 — Enterprise integrations (Phase 7): Datadog APM exporter
        (``DatadogExporter``), Grafana Loki exporter (``GrafanaLokiExporter``),
        Kafka consumer support (``EventStream.from_kafka``), Consumer
        registration API (``llm_toolkit_schema.consumer``), Schema governance
        engine (``llm_toolkit_schema.governance``), Deprecation registry
        (``llm_toolkit_schema.deprecations``).  Ecosystem integrations
        (Phase 8): LangChain and LlamaIndex callback adapters
        (``llm_toolkit_schema.integrations``).  v2 migration roadmap
        (Phase 9, ``v2_migration_roadmap``).
v1.1.1 — Security & correctness patch: ``Event.payload`` now returns a
        read-only ``MappingProxyType``; ``strict_unknown=True`` correctly
        blocks unregistered event types; exception-handling narrowed in
        ``_cli.py`` and ``stream.py``; checksum/signature regex patterns
        aligned to ``signing.py`` (``sha256:`` / ``hmac-sha256:`` prefixes);
        Datadog exporter uses deterministic SHA-256 IDs, ``event.timestamp``
        for span start, and validates ``dd_site`` / ``agent_url``; OTLP
        exporter respects ``batch_size`` chunking; URL scheme validation
        added to all HTTP exporters; ``redact._has_redactable`` uses
        ``Mapping`` ABC.  New runtime enforcement classes: ``GuardPolicy``
        (``llm_toolkit_schema.namespaces.guard``), ``FencePolicy``
        (``llm_toolkit_schema.namespaces.fence``), ``TemplatePolicy``
        (``llm_toolkit_schema.namespaces.template``).  New streaming
        generators ``iter_file()`` / ``aiter_file()`` in
        ``llm_toolkit_schema.stream``.
v1.1.2 — Full OpenTelemetry compliance: ``gen_ai.*`` semantic-convention
        attributes (GenAI semconv 1.27+) emitted by ``to_otlp_span()``;
        ``deployment.environment.name`` used in place of legacy
        ``deployment.environment`` (semconv 1.21+); ``spanKind: CLIENT``
        and ``traceFlags: 1`` (sampled) set on every span; ``endTimeUnixNano``
        computed from ``payload.duration_ms``; ``status.code`` / ``status.message``
        mapped from ``payload.status``.  New W3C TraceContext helpers
        ``make_traceparent()`` and ``extract_trace_context()`` in
        ``llm_toolkit_schema.export.otlp``.  New ``OTelBridgeExporter``
        (``llm_toolkit_schema.export.otel_bridge``) emits events through any
        configured ``TracerProvider`` — requires optional ``[otel]`` extra.
"""

from llm_toolkit_schema.event import SCHEMA_VERSION, Event, Tags
from llm_toolkit_schema.exceptions import (
    DeserializationError,
    EventTypeError,
    ExportError,
    LLMSchemaError,
    SchemaValidationError,
    SerializationError,
    SigningError,
    ULIDError,
    VerificationError,
)
from llm_toolkit_schema.redact import (
    PIINotRedactedError,
    PII_TYPES,
    Redactable,
    RedactionPolicy,
    RedactionResult,
    Sensitivity,
    assert_redacted,
    contains_pii,
)
from llm_toolkit_schema.signing import (
    AuditStream,
    ChainVerificationResult,
    assert_verified,
    sign,
    verify,
    verify_chain,
)
from llm_toolkit_schema.types import (
    EventType,
    get_by_value,
    is_registered,
    namespace_of,
    validate_custom,
)
from llm_toolkit_schema.ulid import extract_timestamp_ms
from llm_toolkit_schema.ulid import generate as generate_ulid
from llm_toolkit_schema.ulid import validate as validate_ulid

from llm_toolkit_schema.export import (
    DatadogExporter,
    DatadogResourceAttributes,
    GrafanaLokiExporter,
    JSONLExporter,
    OTLPExporter,
    ResourceAttributes,
    WebhookExporter,
)
from llm_toolkit_schema.consumer import (
    ConsumerRecord,
    ConsumerRegistry,
    IncompatibleSchemaError,
    assert_compatible,
    get_registry as get_consumer_registry,
    register_consumer,
)
from llm_toolkit_schema.governance import (
    EventGovernancePolicy,
    GovernanceViolationError,
    GovernanceWarning,
    check_event as governance_check_event,
    get_global_policy,
    set_global_policy,
)
from llm_toolkit_schema.deprecations import (
    DeprecationNotice,
    DeprecationRegistry,
    get_deprecation_notice,
    get_registry as get_deprecation_registry,
    list_deprecated,
    mark_deprecated,
    warn_if_deprecated,
)
from llm_toolkit_schema.stream import EventStream, Exporter, iter_file, aiter_file
from llm_toolkit_schema.validate import validate_event
from llm_toolkit_schema.compliance import (
    CompatibilityResult,
    CompatibilityViolation,
    ChainIntegrityResult,
    ChainIntegrityViolation,
    IsolationResult,
    IsolationViolation,
    test_compatibility,
    verify_chain_integrity,
    verify_events_scoped,
    verify_tenant_isolation,
)
from llm_toolkit_schema.migrate import DeprecationRecord, MigrationResult, SunsetPolicy, v1_to_v2, v2_migration_roadmap
from llm_toolkit_schema.namespaces import (
    # cache
    CacheEvictedPayload,
    CacheHitPayload,
    CacheMissPayload,
    # cost
    BudgetThresholdPayload,
    CostRecordedPayload,
    # diff
    DiffComparisonPayload,
    DiffReportPayload,
    # eval
    EvalRegressionPayload,
    EvalScenarioPayload,
    # fence
    FencePolicy,
    FenceValidationFailedPayload,
    RetryTriggeredPayload,
    ValidationPassedPayload,
    # guard
    GuardBlockedPayload,
    GuardFlaggedPayload,
    GuardPolicy,
    # prompt
    PromptApprovedPayload,
    PromptPromotedPayload,
    PromptRolledBackPayload,
    PromptSavedPayload,
    # redact (namespace)
    PIIDetectedPayload,
    PIIRedactedPayload,
    ScanCompletedPayload,
    # template
    TemplatePolicy,
    TemplateRenderedPayload,
    TemplateValidationFailedPayload,
    VariableMissingPayload,
    # trace (FROZEN v1)
    ModelInfo,
    SpanCompletedPayload,
    TokenUsage,
    ToolCall,
)

__version__: str = "1.1.2"
__all__: list[str] = [
    # Core
    "Event",
    "Tags",
    "EventType",
    "SCHEMA_VERSION",
    # ULID
    "generate_ulid",
    "validate_ulid",
    "extract_timestamp_ms",
    # EventType helpers
    "is_registered",
    "namespace_of",
    "validate_custom",
    "get_by_value",
    # PII Redaction (v0.2)
    "Sensitivity",
    "Redactable",
    "RedactionPolicy",
    "RedactionResult",
    "PIINotRedactedError",
    "contains_pii",
    "assert_redacted",
    "PII_TYPES",
    # HMAC Signing & Audit Chain (v0.3)
    "sign",
    "verify",
    "verify_chain",
    "assert_verified",
    "ChainVerificationResult",
    "AuditStream",
    # Export backends (v0.4)
    "OTLPExporter",
    "ResourceAttributes",
    "WebhookExporter",
    "JSONLExporter",
    # Event routing (v0.4)
    "EventStream",
    "Exporter",
    # Exceptions
    "LLMSchemaError",
    "SchemaValidationError",
    "ULIDError",
    "SerializationError",
    "DeserializationError",
    "EventTypeError",
    "SigningError",
    "VerificationError",
    "ExportError",
    # Validation (v0.5)
    "validate_event",
    # Namespace payloads (v0.5) — cache
    "CacheHitPayload",
    "CacheMissPayload",
    "CacheEvictedPayload",
    # Namespace payloads (v0.5) — cost
    "CostRecordedPayload",
    "BudgetThresholdPayload",
    # Namespace payloads (v0.5) — diff
    "DiffComparisonPayload",
    "DiffReportPayload",
    # Namespace payloads (v0.5) — eval
    "EvalScenarioPayload",
    "EvalRegressionPayload",
    # Namespace payloads (v0.5) — fence
    "ValidationPassedPayload",
    "FenceValidationFailedPayload",
    "RetryTriggeredPayload",
    # Namespace payloads (v0.5) — guard
    "GuardBlockedPayload",
    "GuardFlaggedPayload",
    # Namespace payloads (v0.5) — prompt
    "PromptSavedPayload",
    "PromptPromotedPayload",
    "PromptApprovedPayload",
    "PromptRolledBackPayload",
    # Namespace payloads (v0.5) — redact namespace
    "PIIDetectedPayload",
    "PIIRedactedPayload",
    "ScanCompletedPayload",
    # Namespace payloads (v0.5) — template
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
    # Namespace payloads (v0.5) — trace (FROZEN v1)
    "TokenUsage",
    "ModelInfo",
    "ToolCall",
    "SpanCompletedPayload",
    # Compliance toolkit (v1.0)
    "test_compatibility",
    "CompatibilityResult",
    "CompatibilityViolation",
    "verify_chain_integrity",
    "ChainIntegrityResult",
    "ChainIntegrityViolation",
    "verify_tenant_isolation",
    "verify_events_scoped",
    "IsolationResult",
    "IsolationViolation",
    # Migration scaffold & roadmap (v1.0 / Phase 9)
    "MigrationResult",
    "v1_to_v2",
    "DeprecationRecord",
    "SunsetPolicy",
    "v2_migration_roadmap",
    # Export backends — enterprise (v1.1 Phase 7)
    "DatadogExporter",
    "DatadogResourceAttributes",
    "GrafanaLokiExporter",
    # Consumer registration (v1.1 Phase 7)
    "ConsumerRecord",
    "ConsumerRegistry",
    "IncompatibleSchemaError",
    "register_consumer",
    "get_consumer_registry",
    "assert_compatible",
    # Schema governance (v1.1 Phase 7)
    "EventGovernancePolicy",
    "GovernanceViolationError",
    "GovernanceWarning",
    "get_global_policy",
    "set_global_policy",
    "governance_check_event",
    # Deprecation registry (v1.1 Phase 8)
    "DeprecationNotice",
    "DeprecationRegistry",
    "mark_deprecated",
    "get_deprecation_notice",
    "warn_if_deprecated",
    "list_deprecated",
    "get_deprecation_registry",
    # Runtime policy enforcement (v1.1.1)
    "GuardPolicy",
    "FencePolicy",
    "TemplatePolicy",
    # Streaming generators (v1.1.1)
    "iter_file",
    "aiter_file",
    # Metadata
    "__version__",
]
