"""Namespaced event type registry for llm-schema.

All event types follow the pattern::

    llm.<tool-namespace>.<entity>.<action>

Each tool in the LLM Developer Toolkit owns its namespace exclusively.  No
tool may emit events in another tool's namespace.  Third-party tools must use
the ``x.*`` private prefix.

Namespace ownership
-------------------

============================  ==============  ================================
Namespace                     Tool            Purpose
============================  ==============  ================================
``llm.diff.*``                llm-diff        Prompt/output diff comparisons
``llm.prompt.*``              promptlock      Prompt version lifecycle + audit
``llm.template.*``            promptblock     Template rendering and validation
``llm.trace.*``               llm-trace       Span tracing (central event type)
``llm.cost.*``                llm-cost        Token cost recording + budgets
``llm.eval.*``                evalkit         Evaluation scenarios + regression
``llm.guard.*``               promptguard     Input/output safety guards
``llm.redact.*``              llm-redact      PII detection and redaction
``llm.fence.*``               llm-fence       Output-format validation + retry
``llm.cache.*``               llm-cache       Semantic cache hit/miss events
============================  ==============  ================================

Design
------
:class:`EventType` is a ``str`` subclass so that values can be compared with
plain strings, used as dict keys, and serialised without conversion, while
still providing the autocomplete and type-safety of an enum.

:func:`is_registered` and :func:`namespace_of` provide runtime introspection.
:func:`validate_custom` allows third-party tools to validate their ``x.*``
types at runtime.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Final, Optional

from llm_schema.exceptions import EventTypeError

__all__ = [
    "EventType",
    "is_registered",
    "namespace_of",
    "validate_custom",
    "EVENT_TYPE_PATTERN",
]

# ---------------------------------------------------------------------------
# Validation pattern for ALL event type strings (registered + custom)
# ---------------------------------------------------------------------------
# Pattern accepts 3-part (llm.ns.action) or 4-part (llm.ns.entity.action) types.
EVENT_TYPE_PATTERN: Final[str] = (
    r"^(?:llm\.[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_.]*){1,2}"
    r"|x\.[a-z][a-z0-9._]*)$"
)
_EVENT_TYPE_RE: Final[re.Pattern[str]] = re.compile(EVENT_TYPE_PATTERN)

# Namespaces reserved by the llm-toolkit registry.
_RESERVED_NAMESPACES: Final[frozenset[str]] = frozenset(
    [
        "llm.audit",
        "llm.cache",
        "llm.cost",
        "llm.diff",
        "llm.eval",
        "llm.fence",
        "llm.guard",
        "llm.prompt",
        "llm.redact",
        "llm.template",
        "llm.trace",
    ]
)


class EventType(str, Enum):
    """Exhaustive registry of all first-party llm-toolkit event types.

    Values are the canonical string representations used in serialised events.

    Each member also carries:

    * :attr:`namespace` — the ``llm.<tool>`` prefix.
    * :attr:`tool` — the owning tool name.
    * :attr:`description` — a one-line description for documentation/tooling.

    Example::

        event_type = EventType.TRACE_SPAN_COMPLETED
        assert event_type == "llm.trace.span.completed"
        assert event_type.namespace == "llm.trace"
        assert event_type.tool == "llm-trace"
    """

    def __new__(cls, value: str, tool: str = "", description: str = "") -> "EventType":  # noqa: ANN001
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, value: str, tool: str = "", description: str = "") -> None:  # noqa: ANN001
        self._tool = tool
        self._description = description

    # Explicit overrides required for Python 3.12+ where Enum's __eq__ no
    # longer delegates to the mixed-in data-type's __eq__.
    def __str__(self) -> str:  # type: ignore[override]
        """Return the canonical string value (e.g. 'llm.trace.span.completed')."""
        return self.value  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        """Compare equal to strings that match this event type's value."""
        if isinstance(other, str):
            return str.__eq__(self, other)
        return NotImplemented

    def __hash__(self) -> int:
        """Hash consistently with string representation."""
        return str.__hash__(self)

    # ------------------------------------------------------------------
    # llm.diff.*  — llm-diff
    # ------------------------------------------------------------------
    DIFF_COMPARISON_STARTED = (
        "llm.diff.comparison.started",
        "llm-diff",
        "A diff comparison has been initiated.",
    )
    DIFF_COMPARISON_COMPLETED = (
        "llm.diff.comparison.completed",
        "llm-diff",
        "A diff comparison finished successfully.",
    )
    DIFF_REPORT_EXPORTED = (
        "llm.diff.report.exported",
        "llm-diff",
        "A diff report has been exported to a file or sink.",
    )

    # ------------------------------------------------------------------
    # llm.prompt.*  — promptlock
    # ------------------------------------------------------------------
    PROMPT_SAVED = (
        "llm.prompt.saved",
        "promptlock",
        "A prompt version was saved to the registry.",
    )
    PROMPT_PROMOTED = (
        "llm.prompt.promoted",
        "promptlock",
        "A prompt version was promoted to a higher environment.",
    )
    PROMPT_ROLLED_BACK = (
        "llm.prompt.rolled_back",
        "promptlock",
        "A prompt was rolled back to a previous version.",
    )
    PROMPT_APPROVED = (
        "llm.prompt.approved",
        "promptlock",
        "A prompt version approval was recorded.",
    )
    PROMPT_REJECTED = (
        "llm.prompt.rejected",
        "promptlock",
        "A prompt version was rejected in the review workflow.",
    )

    # ------------------------------------------------------------------
    # llm.template.*  — promptblock
    # ------------------------------------------------------------------
    TEMPLATE_RENDERED = (
        "llm.template.rendered",
        "promptblock",
        "A prompt template was rendered with variable substitution.",
    )
    TEMPLATE_VARIABLE_MISSING = (
        "llm.template.variable.missing",
        "promptblock",
        "A required template variable was absent at render time.",
    )
    TEMPLATE_VALIDATION_FAILED = (
        "llm.template.validation.failed",
        "promptblock",
        "Template post-render validation did not pass.",
    )

    # ------------------------------------------------------------------
    # llm.trace.*  — llm-trace  (central event type — payload is frozen v1)
    # ------------------------------------------------------------------
    TRACE_SPAN_STARTED = (
        "llm.trace.span.started",
        "llm-trace",
        "A tracing span was opened.",
    )
    TRACE_SPAN_COMPLETED = (
        "llm.trace.span.completed",
        "llm-trace",
        "A tracing span completed. Primary event consumed by cost/eval/board.",
    )
    TRACE_TOOL_CALL_STARTED = (
        "llm.trace.tool_call.started",
        "llm-trace",
        "A tool call within a span was initiated.",
    )
    TRACE_TOOL_CALL_COMPLETED = (
        "llm.trace.tool_call.completed",
        "llm-trace",
        "A tool call within a span completed.",
    )

    # ------------------------------------------------------------------
    # llm.cost.*  — llm-cost
    # ------------------------------------------------------------------
    COST_RECORDED = (
        "llm.cost.recorded",
        "llm-cost",
        "Token usage cost was recorded for a span.",
    )
    COST_BUDGET_THRESHOLD_REACHED = (
        "llm.cost.budget.threshold_reached",
        "llm-cost",
        "Cost crossed a configured warning threshold.",
    )
    COST_BUDGET_EXCEEDED = (
        "llm.cost.budget.exceeded",
        "llm-cost",
        "Cost exceeded the hard budget limit.",
    )

    # ------------------------------------------------------------------
    # llm.eval.*  — evalkit
    # ------------------------------------------------------------------
    EVAL_SCENARIO_STARTED = (
        "llm.eval.scenario.started",
        "evalkit",
        "An evaluation scenario run has started.",
    )
    EVAL_SCENARIO_COMPLETED = (
        "llm.eval.scenario.completed",
        "evalkit",
        "An evaluation scenario run has finished.",
    )
    EVAL_REGRESSION_FAILED = (
        "llm.eval.regression.failed",
        "evalkit",
        "An evaluation run detected a quality regression versus baseline.",
    )

    # ------------------------------------------------------------------
    # llm.guard.*  — promptguard
    # ------------------------------------------------------------------
    GUARD_INPUT_SCANNED = (
        "llm.guard.input.scanned",
        "promptguard",
        "An input was scanned by the guard policy.",
    )
    GUARD_INPUT_BLOCKED = (
        "llm.guard.input.blocked",
        "promptguard",
        "An input was blocked by the guard policy.",
    )
    GUARD_OUTPUT_FLAGGED = (
        "llm.guard.output.flagged",
        "promptguard",
        "A model output was flagged by the guard policy.",
    )

    # ------------------------------------------------------------------
    # llm.redact.*  — llm-redact
    # ------------------------------------------------------------------
    REDACT_PII_DETECTED = (
        "llm.redact.pii.detected",
        "llm-redact",
        "PII was detected in a field.",
    )
    REDACT_PII_REDACTED = (
        "llm.redact.pii.redacted",
        "llm-redact",
        "A field was successfully redacted.",
    )
    REDACT_SCAN_COMPLETED = (
        "llm.redact.scan.completed",
        "llm-redact",
        "A PII scan of an event completed.",
    )

    # ------------------------------------------------------------------
    # llm.fence.*  — llm-fence
    # ------------------------------------------------------------------
    FENCE_VALIDATION_PASSED = (
        "llm.fence.validation.passed",
        "llm-fence",
        "Output-format validation passed.",
    )
    FENCE_VALIDATION_FAILED = (
        "llm.fence.validation.failed",
        "llm-fence",
        "Output-format validation failed.",
    )
    FENCE_RETRY_TRIGGERED = (
        "llm.fence.retry.triggered",
        "llm-fence",
        "A retry was triggered following a fence validation failure.",
    )

    # ------------------------------------------------------------------
    # llm.audit.*  — llm-schema (audit chain / signing infrastructure)
    # ------------------------------------------------------------------
    AUDIT_CHAIN_STARTED = (
        "llm.audit.chain.started",
        "llm-schema",
        "A new tamper-evident audit chain was initialised.",
    )
    AUDIT_KEY_ROTATED = (
        "llm.audit.key.rotated",
        "llm-schema",
        "The HMAC signing key was rotated; subsequent events use the new key.",
    )

    # ------------------------------------------------------------------
    # llm.cache.*  — llm-cache
    # ------------------------------------------------------------------
    CACHE_HIT = (
        "llm.cache.hit",
        "llm-cache",
        "A semantic cache returned a cached result.",
    )
    CACHE_MISS = (
        "llm.cache.miss",
        "llm-cache",
        "A semantic cache lookup returned no result.",
    )
    CACHE_EVICTED = (
        "llm.cache.evicted",
        "llm-cache",
        "A cache entry was evicted.",
    )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str:
        """Return the ``llm.<tool>`` namespace prefix.

        Example::

            EventType.TRACE_SPAN_COMPLETED.namespace  # "llm.trace"
        """
        parts = self.value.split(".")
        return f"{parts[0]}.{parts[1]}"

    @property
    def tool(self) -> str:
        """Return the name of the tool that owns this event type."""
        return self._tool

    @property
    def description(self) -> str:
        """Return a one-line description of the event type."""
        return self._description


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_REGISTERED: Final[frozenset[str]] = frozenset(et.value for et in EventType)


def is_registered(event_type: str) -> bool:
    """Return ``True`` if *event_type* is a first-party registered type.

    Args:
        event_type: The event type string to check.

    Returns:
        ``True`` for any value that is a member of :class:`EventType`.
    """
    return event_type in _REGISTERED


def namespace_of(event_type: str) -> str:
    """Extract the ``llm.<tool>`` namespace prefix from *event_type*.

    Works for both registered and syntactically valid custom (``x.*``) types.

    Args:
        event_type: A syntactically valid event type string.

    Returns:
        The namespace prefix, e.g. ``"llm.trace"`` or ``"x.mycompany"``.

    Raises:
        EventTypeError: If *event_type* does not match the expected pattern.

    Example::

        namespace_of("llm.trace.span.completed")    # "llm.trace"
        namespace_of("x.myco.inference.completed") # "x.myco"
    """
    if not _EVENT_TYPE_RE.match(event_type):
        raise EventTypeError(
            event_type,
            f"does not match required pattern {EVENT_TYPE_PATTERN!r}",
        )
    parts = event_type.split(".")
    return f"{parts[0]}.{parts[1]}"


def validate_custom(event_type: str) -> None:
    """Validate a custom (third-party) event type string.

    Third-party tools **must** use the ``x.`` prefix.  Attempting to use a
    reserved ``llm.*`` namespace that is not in the first-party registry raises
    an error.

    Args:
        event_type: The custom event type string to validate.

    Raises:
        EventTypeError: If the string is malformed, uses a reserved namespace
            without being in the first-party registry, or uses the bare
            ``x.*`` prefix without a company qualifier.

    Example::

        validate_custom("x.mycompany.inference.completed")  # OK
        validate_custom("llm.trace.span.completed")         # raises — reserved
    """
    if not _EVENT_TYPE_RE.match(event_type):
        raise EventTypeError(
            event_type,
            f"does not match the required pattern {EVENT_TYPE_PATTERN!r}. "
            "Custom types must use the 'x.<company>.<entity>.<action>' prefix.",
        )

    ns = namespace_of(event_type)

    if ns in _RESERVED_NAMESPACES and not is_registered(event_type):
        raise EventTypeError(
            event_type,
            f"namespace '{ns}' is reserved by the llm-toolkit registry. "
            "Use the 'x.' prefix for custom event types.",
        )

    if event_type.startswith("x.") and event_type.count(".") < 2:  # noqa: PLR2004
        raise EventTypeError(
            event_type,
            "custom types must include a company qualifier: 'x.<company>.<…>'",
        )


def get_by_value(value: str) -> Optional[EventType]:
    """Return the :class:`EventType` matching *value*, or ``None``.

    Args:
        value: The event type string, e.g. ``"llm.trace.span.completed"``.

    Returns:
        The matching :class:`EventType` member, or ``None`` if not found.

    Example::

        et = get_by_value("llm.trace.span.completed")
        assert et is EventType.TRACE_SPAN_COMPLETED
    """
    try:
        return EventType(value)
    except ValueError:
        return None
