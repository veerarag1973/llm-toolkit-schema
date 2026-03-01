"""llm_schema.namespaces.fence — Output fence / structured-output payload types.

Classes
-------
ValidationPassedPayload
    ``llm.fence.validation.passed`` — rendered output passed fence validation.
FenceValidationFailedPayload
    ``llm.fence.validation.failed`` — rendered output failed fence validation.
RetryTriggeredPayload
    ``llm.fence.retry.triggered`` — a fence failure triggered a retry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ValidationPassedPayload:
    """Payload for ``llm.fence.validation.passed``.

    Parameters
    ----------
    validator_id:
        Unique identifier for the fence/validator, e.g. ``"json-schema:v2"``.
    format_type:
        Expected output format: ``"json"``, ``"yaml"``, ``"xml"``, ``"custom"``, etc.
    attempt:
        Which attempt succeeded (1-based; 1 = first try).
    duration_ms:
        Optional validation duration in milliseconds.
    """

    validator_id: str
    format_type: str
    attempt: int = 1
    duration_ms: Optional[float] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.validator_id or not isinstance(self.validator_id, str):
            raise ValueError("ValidationPassedPayload.validator_id must be a non-empty string")
        if not self.format_type or not isinstance(self.format_type, str):
            raise ValueError("ValidationPassedPayload.format_type must be a non-empty string")
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError("ValidationPassedPayload.attempt must be a positive int")
        if self.duration_ms is not None and (
            not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0
        ):
            raise ValueError(
                "ValidationPassedPayload.duration_ms must be a non-negative number or None"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "validator_id": self.validator_id,
            "format_type": self.format_type,
            "attempt": self.attempt,
        }
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationPassedPayload":
        """Reconstruct a :class:`ValidationPassedPayload` from a plain dict."""
        return cls(
            validator_id=str(data["validator_id"]),
            format_type=str(data["format_type"]),
            attempt=int(data.get("attempt", 1)),
            duration_ms=data.get("duration_ms"),
        )


@dataclass(frozen=True)
class FenceValidationFailedPayload:
    """Payload for ``llm.fence.validation.failed``.

    This event is raised when *rendered LLM output* fails to conform to the
    expected structure, as opposed to
    :class:`~llm_schema.namespaces.template.TemplateValidationFailedPayload`
    which covers validation of the template definition itself.

    Parameters
    ----------
    validator_id:
        Unique identifier for the fence/validator.
    format_type:
        Expected output format.
    errors:
        Ordered list of human-readable validation error messages.
    attempt:
        Which attempt failed (1-based).
    retryable:
        Whether another generation attempt may succeed.
    """

    validator_id: str
    format_type: str
    errors: List[str]
    attempt: int = 1
    retryable: bool = True

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.validator_id or not isinstance(self.validator_id, str):
            raise ValueError(
                "FenceValidationFailedPayload.validator_id must be a non-empty string"
            )
        if not self.format_type or not isinstance(self.format_type, str):
            raise ValueError(
                "FenceValidationFailedPayload.format_type must be a non-empty string"
            )
        if not isinstance(self.errors, list) or not self.errors:
            raise ValueError("FenceValidationFailedPayload.errors must be a non-empty list")
        for err in self.errors:
            if not isinstance(err, str):
                raise TypeError("Each error must be a string")
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError("FenceValidationFailedPayload.attempt must be a positive int")
        if not isinstance(self.retryable, bool):
            raise TypeError("FenceValidationFailedPayload.retryable must be a bool")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "validator_id": self.validator_id,
            "format_type": self.format_type,
            "errors": list(self.errors),
            "attempt": self.attempt,
            "retryable": self.retryable,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FenceValidationFailedPayload":
        """Reconstruct a :class:`FenceValidationFailedPayload` from a plain dict."""
        return cls(
            validator_id=str(data["validator_id"]),
            format_type=str(data["format_type"]),
            errors=list(data["errors"]),
            attempt=int(data.get("attempt", 1)),
            retryable=bool(data.get("retryable", True)),
        )


@dataclass(frozen=True)
class RetryTriggeredPayload:
    """Payload for ``llm.fence.retry.triggered``.

    Parameters
    ----------
    validator_id:
        Unique identifier for the fence/validator that triggered the retry.
    attempt:
        The attempt number that is *about to start* (1-based;
        ``attempt=2`` means the first retry).
    max_attempts:
        Configured maximum number of attempts.
    previous_error:
        Optional summary of the error from the previous attempt.
    strategy:
        Retry strategy: ``"regenerate"``, ``"repair"``, ``"fallback"``.
    """

    validator_id: str
    attempt: int
    max_attempts: int
    previous_error: Optional[str] = None
    strategy: str = "regenerate"

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.validator_id or not isinstance(self.validator_id, str):
            raise ValueError("RetryTriggeredPayload.validator_id must be a non-empty string")
        if not isinstance(self.attempt, int) or self.attempt < 1:
            raise ValueError("RetryTriggeredPayload.attempt must be a positive int")
        if not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            raise ValueError("RetryTriggeredPayload.max_attempts must be a positive int")
        if self.attempt > self.max_attempts:
            raise ValueError(
                f"RetryTriggeredPayload.attempt ({self.attempt}) cannot exceed "
                f"max_attempts ({self.max_attempts})"
            )
        if self.strategy not in frozenset({"regenerate", "repair", "fallback"}):
            raise ValueError(
                f"RetryTriggeredPayload.strategy must be regenerate/repair/fallback, "
                f"got {self.strategy!r}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "validator_id": self.validator_id,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "strategy": self.strategy,
        }
        if self.previous_error is not None:
            result["previous_error"] = self.previous_error
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetryTriggeredPayload":
        """Reconstruct a :class:`RetryTriggeredPayload` from a plain dict."""
        return cls(
            validator_id=str(data["validator_id"]),
            attempt=int(data["attempt"]),
            max_attempts=int(data["max_attempts"]),
            previous_error=data.get("previous_error"),
            strategy=str(data.get("strategy", "regenerate")),
        )


__all__: list[str] = [
    "ValidationPassedPayload",
    "FenceValidationFailedPayload",
    "RetryTriggeredPayload",
]
