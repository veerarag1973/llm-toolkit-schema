"""llm_schema.namespaces.trace — Span-level payload types (FROZEN v1).

These classes model ``llm.trace.*`` events and are deliberately kept stable;
downstream tools (cost recorder, eval kit, agent board, evalkit) depend on
the exact field layout.  **Do not add, remove, or rename fields without a
major-version bump.**

Classes
-------
TokenUsage
    Prompt/completion/total token counts for a single inference call.
ModelInfo
    Metadata about the model that produced a span.
ToolCall
    Captures one external tool invocation made within a span.
SpanCompletedPayload
    Root payload for ``llm.trace.span.completed`` events.  FROZEN v1.

All classes are ``dataclass(frozen=True)`` and provide ``to_dict()`` /
``from_dict()`` for serialisation into ``Event.payload``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TokenUsage:
    """Token counts for one LLM inference call.

    Parameters
    ----------
    prompt_tokens:
        Number of tokens in the input prompt.
    completion_tokens:
        Number of tokens in the model's output.
    total_tokens:
        Sum of prompt + completion tokens as reported by the provider.
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"TokenUsage.{name} must be a non-negative int, got {value!r}")
        if self.total_tokens < self.prompt_tokens + self.completion_tokens:
            raise ValueError(
                "TokenUsage.total_tokens must be >= prompt_tokens + completion_tokens"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsage":
        """Reconstruct a :class:`TokenUsage` from a plain dict."""
        return cls(
            prompt_tokens=int(data["prompt_tokens"]),
            completion_tokens=int(data["completion_tokens"]),
            total_tokens=int(data["total_tokens"]),
        )


@dataclass(frozen=True)
class ModelInfo:
    """Metadata about the model involved in a span.

    Parameters
    ----------
    name:
        Short model identifier, e.g. ``"gpt-4o"``.
    provider:
        Provider name, e.g. ``"openai"``, ``"anthropic"``.
    version:
        Optional version string, e.g. ``"2024-05-13"``.
    """

    name: str
    provider: str
    version: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("ModelInfo.name must be a non-empty string")
        if not self.provider or not isinstance(self.provider, str):
            raise ValueError("ModelInfo.provider must be a non-empty string")
        if self.version is not None and not isinstance(self.version, str):
            raise ValueError("ModelInfo.version must be a string or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {"name": self.name, "provider": self.provider}
        if self.version is not None:
            result["version"] = self.version
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Reconstruct a :class:`ModelInfo` from a plain dict."""
        return cls(
            name=str(data["name"]),
            provider=str(data["provider"]),
            version=data.get("version"),
        )


@dataclass(frozen=True)
class ToolCall:
    """Captures a single tool invocation made during a span.

    Parameters
    ----------
    tool_name:
        Name of the tool that was called, e.g. ``"web_search"``.
    tool_input:
        Input passed to the tool (arbitrary dict).
    tool_output:
        Output returned by the tool.  ``None`` if not captured.
    duration_ms:
        Wall-clock duration of the tool call in milliseconds.
    status:
        Outcome: ``"completed"``, ``"error"``, or ``"timeout"``.
    """

    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    status: str = "completed"

    # Allowed status values.
    _VALID_STATUSES: frozenset = field(
        default=frozenset({"completed", "error", "timeout"}), init=False, repr=False, compare=False
    )

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.tool_name or not isinstance(self.tool_name, str):
            raise ValueError("ToolCall.tool_name must be a non-empty string")
        if not isinstance(self.tool_input, dict):
            raise ValueError("ToolCall.tool_input must be a dict")
        if self.tool_output is not None and not isinstance(self.tool_output, dict):
            raise ValueError("ToolCall.tool_output must be a dict or None")
        if self.duration_ms is not None and (
            not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0
        ):
            raise ValueError("ToolCall.duration_ms must be a non-negative number or None")
        if self.status not in frozenset({"completed", "error", "timeout"}):
            raise ValueError(
                f"ToolCall.status must be one of completed/error/timeout, got {self.status!r}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "tool_name": self.tool_name,
            "tool_input": dict(self.tool_input),
            "status": self.status,
        }
        if self.tool_output is not None:
            result["tool_output"] = dict(self.tool_output)
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        """Reconstruct a :class:`ToolCall` from a plain dict."""
        return cls(
            tool_name=str(data["tool_name"]),
            tool_input=dict(data["tool_input"]),
            tool_output=dict(data["tool_output"]) if data.get("tool_output") is not None else None,
            duration_ms=data.get("duration_ms"),
            status=str(data.get("status", "completed")),
        )


# ---------------------------------------------------------------------------
# SpanCompletedPayload — FROZEN v1
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpanCompletedPayload:
    """Payload for ``llm.trace.span.completed`` events.

    .. warning::

        **FROZEN v1** — the field layout of this class is contractually
        stable.  Downstream tools (cost recorder, eval kit, agent board,
        evalkit) rely on exact field names and types.  Any change requires
        a major-version bump of *llm-schema*.

    Parameters
    ----------
    span_name:
        Human-readable name for the span, e.g. ``"run_agent"``.
    status:
        Outcome: ``"ok"``, ``"error"``, or ``"timeout"``.
    duration_ms:
        Wall-clock time for the entire span in milliseconds.
    model:
        Optional :class:`ModelInfo` describing the model used.
    token_usage:
        Optional :class:`TokenUsage` reported by the provider.
    tool_calls:
        Ordered list of :class:`ToolCall` instances made during the span.
    error:
        Short error message if ``status != "ok"``.
    cost_usd:
        Estimated cost in US dollars, if known.
    """

    span_name: str
    status: str
    duration_ms: float
    model: Optional[ModelInfo] = None
    token_usage: Optional[TokenUsage] = None
    tool_calls: Optional[List[ToolCall]] = None
    error: Optional[str] = None
    cost_usd: Optional[float] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.span_name or not isinstance(self.span_name, str):
            raise ValueError("SpanCompletedPayload.span_name must be a non-empty string")
        if self.status not in frozenset({"ok", "error", "timeout"}):
            raise ValueError(
                f"SpanCompletedPayload.status must be ok/error/timeout, got {self.status!r}"
            )
        if not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0:
            raise ValueError("SpanCompletedPayload.duration_ms must be a non-negative number")
        if self.model is not None and not isinstance(self.model, ModelInfo):
            raise TypeError("SpanCompletedPayload.model must be a ModelInfo instance or None")
        if self.token_usage is not None and not isinstance(self.token_usage, TokenUsage):
            raise TypeError(
                "SpanCompletedPayload.token_usage must be a TokenUsage instance or None"
            )
        if self.tool_calls is not None:
            if not isinstance(self.tool_calls, list):
                raise TypeError("SpanCompletedPayload.tool_calls must be a list or None")
            for tc in self.tool_calls:
                if not isinstance(tc, ToolCall):
                    raise TypeError("Each tool_calls entry must be a ToolCall instance")
        if self.cost_usd is not None and (
            not isinstance(self.cost_usd, (int, float)) or self.cost_usd < 0
        ):
            raise ValueError("SpanCompletedPayload.cost_usd must be a non-negative number or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "span_name": self.span_name,
            "status": self.status,
            "duration_ms": self.duration_ms,
        }
        if self.model is not None:
            result["model"] = self.model.to_dict()
        if self.token_usage is not None:
            result["token_usage"] = self.token_usage.to_dict()
        if self.tool_calls is not None:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.error is not None:
            result["error"] = self.error
        if self.cost_usd is not None:
            result["cost_usd"] = self.cost_usd
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpanCompletedPayload":
        """Reconstruct a :class:`SpanCompletedPayload` from a plain dict."""
        model = ModelInfo.from_dict(data["model"]) if data.get("model") else None
        token_usage = (
            TokenUsage.from_dict(data["token_usage"]) if data.get("token_usage") else None
        )
        tool_calls = (
            [ToolCall.from_dict(tc) for tc in data["tool_calls"]]
            if data.get("tool_calls") is not None
            else None
        )
        return cls(
            span_name=str(data["span_name"]),
            status=str(data["status"]),
            duration_ms=float(data["duration_ms"]),
            model=model,
            token_usage=token_usage,
            tool_calls=tool_calls,
            error=data.get("error"),
            cost_usd=data.get("cost_usd"),
        )


__all__: list[str] = [
    "TokenUsage",
    "ModelInfo",
    "ToolCall",
    "SpanCompletedPayload",
]
