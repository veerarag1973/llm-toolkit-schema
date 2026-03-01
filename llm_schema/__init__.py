"""llm-schema — Shared Event Schema for the LLM Developer Toolkit.

This package provides the foundational event contract used by every tool in
the LLM Developer Toolkit.  It is OpenTelemetry-compatible, versioned, and
designed for enterprise-grade observability.

Quick start
-----------
::

    from llm_schema import Event, EventType, Tags

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

    from llm_schema import Event, EventType
    from llm_schema.redact import Redactable, RedactionPolicy, Sensitivity

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

    from llm_schema.models import EventModel
    model = EventModel.from_event(event)
    print(model.model_json_schema())

HMAC signing & audit chain (v0.3+)
-----------------------------------
::

    from llm_schema.signing import sign, verify, verify_chain, AuditStream

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

* :class:`~llm_schema.event.Event`
* :class:`~llm_schema.event.Tags`
* :class:`~llm_schema.types.EventType`
* :data:`~llm_schema.event.SCHEMA_VERSION`
* :func:`~llm_schema.ulid.generate`
* :func:`~llm_schema.ulid.validate`
* :func:`~llm_schema.ulid.extract_timestamp_ms`
* :func:`~llm_schema.types.is_registered`
* :func:`~llm_schema.types.namespace_of`
* :func:`~llm_schema.types.validate_custom`
* :func:`~llm_schema.types.get_by_value`
* :class:`~llm_schema.exceptions.LLMSchemaError`
* :class:`~llm_schema.exceptions.SchemaValidationError`
* :class:`~llm_schema.exceptions.ULIDError`
* :class:`~llm_schema.exceptions.SerializationError`
* :class:`~llm_schema.exceptions.DeserializationError`
* :class:`~llm_schema.exceptions.EventTypeError`
* :class:`~llm_schema.exceptions.SigningError`
* :class:`~llm_schema.exceptions.VerificationError`
* :class:`~llm_schema.redact.Sensitivity`
* :class:`~llm_schema.redact.Redactable`
* :class:`~llm_schema.redact.RedactionPolicy`
* :class:`~llm_schema.redact.RedactionResult`
* :class:`~llm_schema.redact.PIINotRedactedError`
* :func:`~llm_schema.redact.contains_pii`
* :func:`~llm_schema.redact.assert_redacted`
* :func:`~llm_schema.signing.sign`
* :func:`~llm_schema.signing.verify`
* :func:`~llm_schema.signing.verify_chain`
* :func:`~llm_schema.signing.assert_verified`
* :class:`~llm_schema.signing.ChainVerificationResult`
* :class:`~llm_schema.signing.AuditStream`

Version history
---------------
v0.1 — Core ``Event``, ``EventType``, ULID, JSON serialisation, validation.
        Zero external dependencies.
v0.2 — PII redaction framework (``Redactable``, ``RedactionPolicy``,
        ``Sensitivity``).  Pydantic v2 model layer (``llm_schema.models``).
v0.3 — HMAC-SHA256 signing (``sign``, ``verify``), tamper-evident audit chain
        (``verify_chain``, ``AuditStream``), key rotation, gap detection.
"""

from llm_schema.event import SCHEMA_VERSION, Event, Tags
from llm_schema.exceptions import (
    DeserializationError,
    EventTypeError,
    LLMSchemaError,
    SchemaValidationError,
    SerializationError,
    SigningError,
    ULIDError,
    VerificationError,
)
from llm_schema.redact import (
    PIINotRedactedError,
    PII_TYPES,
    Redactable,
    RedactionPolicy,
    RedactionResult,
    Sensitivity,
    assert_redacted,
    contains_pii,
)
from llm_schema.signing import (
    AuditStream,
    ChainVerificationResult,
    assert_verified,
    sign,
    verify,
    verify_chain,
)
from llm_schema.types import (
    EventType,
    get_by_value,
    is_registered,
    namespace_of,
    validate_custom,
)
from llm_schema.ulid import extract_timestamp_ms
from llm_schema.ulid import generate as generate_ulid
from llm_schema.ulid import validate as validate_ulid

__version__: str = "0.3.0"
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
    # Exceptions
    "LLMSchemaError",
    "SchemaValidationError",
    "ULIDError",
    "SerializationError",
    "DeserializationError",
    "EventTypeError",
    "SigningError",
    "VerificationError",
    # Metadata
    "__version__",
]
