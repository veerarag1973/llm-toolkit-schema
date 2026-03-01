"""llm_schema.namespaces.redact — Namespace PII redaction payload types.

.. note::

    This module lives at ``llm_schema.namespaces.redact`` and is completely
    separate from ``llm_schema.redact``, which provides the core
    :class:`~llm_schema.redact.Redactable` / :class:`~llm_schema.redact.RedactionPolicy`
    framework.

Classes
-------
PIIDetectedPayload
    ``llm.redact.pii.detected`` — PII was found in a field.
PIIRedactedPayload
    ``llm.redact.pii.redacted`` — PII was successfully redacted.
ScanCompletedPayload
    ``llm.redact.scan.completed`` — a full redaction scan finished.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PIIDetectedPayload:
    """Payload for ``llm.redact.pii.detected``.

    Parameters
    ----------
    field_path:
        Dot-notation path to the field containing PII, e.g. ``"payload.author"``.
    pii_types:
        List of PII categories found, e.g. ``["email", "phone_number"]``.
    confidence:
        Detection confidence in ``[0.0, 1.0]``.
    redacted:
        Whether the detected PII has already been redacted (``False`` if
        only detected, not yet actioned).
    """

    field_path: str
    pii_types: List[str]
    confidence: float
    redacted: bool = False

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.field_path or not isinstance(self.field_path, str):
            raise ValueError("PIIDetectedPayload.field_path must be a non-empty string")
        if not isinstance(self.pii_types, list) or not self.pii_types:
            raise ValueError("PIIDetectedPayload.pii_types must be a non-empty list")
        for pt in self.pii_types:
            if not isinstance(pt, str):
                raise TypeError("Each pii_type must be a string")
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"PIIDetectedPayload.confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        if not isinstance(self.redacted, bool):
            raise TypeError("PIIDetectedPayload.redacted must be a bool")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "field_path": self.field_path,
            "pii_types": list(self.pii_types),
            "confidence": self.confidence,
            "redacted": self.redacted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PIIDetectedPayload":
        """Reconstruct a :class:`PIIDetectedPayload` from a plain dict."""
        return cls(
            field_path=str(data["field_path"]),
            pii_types=list(data["pii_types"]),
            confidence=float(data["confidence"]),
            redacted=bool(data.get("redacted", False)),
        )


@dataclass(frozen=True)
class PIIRedactedPayload:
    """Payload for ``llm.redact.pii.redacted``.

    Parameters
    ----------
    field_path:
        Dot-notation path to the redacted field.
    pii_types:
        List of PII categories that were redacted.
    method:
        Redaction method applied: ``"mask"``, ``"hash"``, ``"drop"``,
        ``"replace"``, etc.
    redacted_by:
        Optional identifier of the policy or actor that performed the
        redaction.
    """

    field_path: str
    pii_types: List[str]
    method: str
    redacted_by: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.field_path or not isinstance(self.field_path, str):
            raise ValueError("PIIRedactedPayload.field_path must be a non-empty string")
        if not isinstance(self.pii_types, list) or not self.pii_types:
            raise ValueError("PIIRedactedPayload.pii_types must be a non-empty list")
        for pt in self.pii_types:
            if not isinstance(pt, str):
                raise TypeError("Each pii_type must be a string")
        if not self.method or not isinstance(self.method, str):
            raise ValueError("PIIRedactedPayload.method must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "field_path": self.field_path,
            "pii_types": list(self.pii_types),
            "method": self.method,
        }
        if self.redacted_by is not None:
            result["redacted_by"] = self.redacted_by
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PIIRedactedPayload":
        """Reconstruct a :class:`PIIRedactedPayload` from a plain dict."""
        return cls(
            field_path=str(data["field_path"]),
            pii_types=list(data["pii_types"]),
            method=str(data["method"]),
            redacted_by=data.get("redacted_by"),
        )


@dataclass(frozen=True)
class ScanCompletedPayload:
    """Payload for ``llm.redact.scan.completed``.

    Parameters
    ----------
    scanned_fields:
        Number of fields that were inspected during the scan.
    pii_detected_count:
        Number of fields where PII was detected.
    pii_redacted_count:
        Number of fields where PII was redacted.
    duration_ms:
        Optional wall-clock time for the scan in milliseconds.
    policy_id:
        Optional identifier of the redaction policy applied.
    """

    scanned_fields: int
    pii_detected_count: int
    pii_redacted_count: int
    duration_ms: Optional[float] = None
    policy_id: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("scanned_fields", "pii_detected_count", "pii_redacted_count"):
            value = getattr(self, attr)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"ScanCompletedPayload.{attr} must be a non-negative int")
        if self.pii_redacted_count > self.pii_detected_count:
            raise ValueError(
                "ScanCompletedPayload.pii_redacted_count cannot exceed pii_detected_count"
            )
        if self.pii_detected_count > self.scanned_fields:
            raise ValueError(
                "ScanCompletedPayload.pii_detected_count cannot exceed scanned_fields"
            )
        if self.duration_ms is not None and (
            not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0
        ):
            raise ValueError("ScanCompletedPayload.duration_ms must be a non-negative number or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "scanned_fields": self.scanned_fields,
            "pii_detected_count": self.pii_detected_count,
            "pii_redacted_count": self.pii_redacted_count,
        }
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        if self.policy_id is not None:
            result["policy_id"] = self.policy_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanCompletedPayload":
        """Reconstruct a :class:`ScanCompletedPayload` from a plain dict."""
        return cls(
            scanned_fields=int(data["scanned_fields"]),
            pii_detected_count=int(data["pii_detected_count"]),
            pii_redacted_count=int(data["pii_redacted_count"]),
            duration_ms=data.get("duration_ms"),
            policy_id=data.get("policy_id"),
        )


__all__: list[str] = [
    "PIIDetectedPayload",
    "PIIRedactedPayload",
    "ScanCompletedPayload",
]
