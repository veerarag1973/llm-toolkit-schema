"""llm_toolkit_schema.namespaces.prompt — Prompt lifecycle payload types.

Classes
-------
PromptSavedPayload
    ``llm.prompt.saved`` — a prompt version has been persisted.
PromptPromotedPayload
    ``llm.prompt.promoted`` — a prompt was moved between environments.
PromptApprovedPayload
    ``llm.prompt.approved`` — a prompt version received an approval.
PromptRolledBackPayload
    ``llm.prompt.rolled_back`` — a prompt was rolled back to a prior version.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PromptSavedPayload:
    """Payload for ``llm.prompt.saved``.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt (stable across versions).
    version:
        Semantic or monotonic version string, e.g. ``"1.3.0"``.
    environment:
        Target environment: ``"development"``, ``"staging"``, ``"production"``.
    template_hash:
        SHA-256 hex digest of the template body at save time.
    author:
        Optional identifier of the person/service that saved the prompt.
    tags:
        Optional list of string labels attached to this version.
    """

    prompt_id: str
    version: str
    environment: str
    template_hash: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "version", "environment", "template_hash"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptSavedPayload.{attr} must be a non-empty string")
        if self.tags is not None:
            if not isinstance(self.tags, list):
                raise TypeError("PromptSavedPayload.tags must be a list or None")
            for tag in self.tags:
                if not isinstance(tag, str):
                    raise TypeError("Each tag must be a string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "environment": self.environment,
            "template_hash": self.template_hash,
        }
        if self.author is not None:
            result["author"] = self.author
        if self.tags is not None:
            result["tags"] = list(self.tags)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptSavedPayload":
        """Reconstruct a :class:`PromptSavedPayload` from a plain dict."""
        tags_raw = data.get("tags")
        return cls(
            prompt_id=str(data["prompt_id"]),
            version=str(data["version"]),
            environment=str(data["environment"]),
            template_hash=str(data["template_hash"]),
            author=data.get("author"),
            tags=list(tags_raw) if tags_raw is not None else None,
        )


@dataclass(frozen=True)
class PromptPromotedPayload:
    """Payload for ``llm.prompt.promoted``.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt.
    version:
        Version being promoted.
    from_environment:
        Environment the prompt was promoted *from*.
    to_environment:
        Environment the prompt was promoted *to*.
    promoted_by:
        Optional identifier of the user/service that performed the promotion.
    """

    prompt_id: str
    version: str
    from_environment: str
    to_environment: str
    promoted_by: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "version", "from_environment", "to_environment"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptPromotedPayload.{attr} must be a non-empty string")
        if self.from_environment == self.to_environment:
            raise ValueError(
                "PromptPromotedPayload.from_environment and to_environment must differ"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "from_environment": self.from_environment,
            "to_environment": self.to_environment,
        }
        if self.promoted_by is not None:
            result["promoted_by"] = self.promoted_by
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptPromotedPayload":
        """Reconstruct a :class:`PromptPromotedPayload` from a plain dict."""
        return cls(
            prompt_id=str(data["prompt_id"]),
            version=str(data["version"]),
            from_environment=str(data["from_environment"]),
            to_environment=str(data["to_environment"]),
            promoted_by=data.get("promoted_by"),
        )


@dataclass(frozen=True)
class PromptApprovedPayload:
    """Payload for ``llm.prompt.approved``.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt.
    version:
        Version receiving approval.
    approved_by:
        Identifier of the reviewer who approved the prompt.
    approval_note:
        Optional free-text note from the approver.
    """

    prompt_id: str
    version: str
    approved_by: str
    approval_note: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "version", "approved_by"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptApprovedPayload.{attr} must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "approved_by": self.approved_by,
        }
        if self.approval_note is not None:
            result["approval_note"] = self.approval_note
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptApprovedPayload":
        """Reconstruct a :class:`PromptApprovedPayload` from a plain dict."""
        return cls(
            prompt_id=str(data["prompt_id"]),
            version=str(data["version"]),
            approved_by=str(data["approved_by"]),
            approval_note=data.get("approval_note"),
        )


@dataclass(frozen=True)
class PromptRolledBackPayload:
    """Payload for ``llm.prompt.rolled_back``.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt.
    from_version:
        Version that was active before the rollback.
    to_version:
        Version restored by the rollback.
    reason:
        Optional human-readable reason for rolling back.
    rolled_back_by:
        Optional identifier of the user/service that performed the rollback.
    """

    prompt_id: str
    from_version: str
    to_version: str
    reason: Optional[str] = None
    rolled_back_by: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "from_version", "to_version"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptRolledBackPayload.{attr} must be a non-empty string")
        if self.from_version == self.to_version:
            raise ValueError("PromptRolledBackPayload.from_version and to_version must differ")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "prompt_id": self.prompt_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
        }
        if self.reason is not None:
            result["reason"] = self.reason
        if self.rolled_back_by is not None:
            result["rolled_back_by"] = self.rolled_back_by
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptRolledBackPayload":
        """Reconstruct a :class:`PromptRolledBackPayload` from a plain dict."""
        return cls(
            prompt_id=str(data["prompt_id"]),
            from_version=str(data["from_version"]),
            to_version=str(data["to_version"]),
            reason=data.get("reason"),
            rolled_back_by=data.get("rolled_back_by"),
        )


@dataclass(frozen=True)
class PromptRejectedPayload:
    """Payload for ``llm.prompt.rejected``.

    Emitted when a promotion request is rejected in the approval workflow.
    The ``rejection_reason`` is mandatory — it is required for audit compliance
    so that rejection decisions are always traceable.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt.
    version:
        Version that was rejected.
    rejected_by:
        Identifier of the reviewer who rejected the version.
    rejection_reason:
        Mandatory human-readable reason for rejection (audit trail).
    """

    prompt_id: str
    version: str
    rejected_by: str
    rejection_reason: str

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "version", "rejected_by", "rejection_reason"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptRejectedPayload.{attr} must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptRejectedPayload":
        """Reconstruct a :class:`PromptRejectedPayload` from a plain dict."""
        return cls(
            prompt_id=str(data["prompt_id"]),
            version=str(data["version"]),
            rejected_by=str(data["rejected_by"]),
            rejection_reason=str(data["rejection_reason"]),
        )


@dataclass(frozen=True)
class PromptRenderedPayload:
    """Payload for ``llm.prompt.rendered``.

    Emitted by promptlock when a versioned prompt is fetched from the registry
    and rendered with variable substitution (``{{variable_name}}`` syntax)
    before being sent to a model.  Distinct from
    :class:`~llm_toolkit_schema.namespaces.template.TemplateRenderedPayload`,
    which covers the promptblock template engine.

    Parameters
    ----------
    prompt_id:
        Unique identifier for the prompt that was rendered.
    version:
        Version of the prompt that was rendered.
    environment:
        Environment in which the prompt was rendered, e.g.
        ``"development"``, ``"staging"``, ``"production"``.
    variable_count:
        Number of template variables substituted during rendering.
    render_duration_ms:
        Optional wall-clock render time in milliseconds.
    output_hash:
        Optional SHA-256 hex digest of the rendered output, for tamper-
        evident audit trail verification.
    """

    prompt_id: str
    version: str
    environment: str
    variable_count: int
    render_duration_ms: Optional[float] = None
    output_hash: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("prompt_id", "version", "environment"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"PromptRenderedPayload.{attr} must be a non-empty string")
        if not isinstance(self.variable_count, int) or self.variable_count < 0:
            raise ValueError("PromptRenderedPayload.variable_count must be a non-negative int")
        if self.render_duration_ms is not None and (
            not isinstance(self.render_duration_ms, (int, float))
            or self.render_duration_ms < 0
        ):
            raise ValueError(
                "PromptRenderedPayload.render_duration_ms must be a non-negative number or None"
            )
        if self.output_hash is not None and not isinstance(self.output_hash, str):
            raise TypeError("PromptRenderedPayload.output_hash must be a string or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "environment": self.environment,
            "variable_count": self.variable_count,
        }
        if self.render_duration_ms is not None:
            result["render_duration_ms"] = self.render_duration_ms
        if self.output_hash is not None:
            result["output_hash"] = self.output_hash
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptRenderedPayload":
        """Reconstruct a :class:`PromptRenderedPayload` from a plain dict."""
        return cls(
            prompt_id=str(data["prompt_id"]),
            version=str(data["version"]),
            environment=str(data["environment"]),
            variable_count=int(data["variable_count"]),
            render_duration_ms=data.get("render_duration_ms"),
            output_hash=data.get("output_hash"),
        )


__all__: list[str] = [
    "PromptSavedPayload",
    "PromptPromotedPayload",
    "PromptApprovedPayload",
    "PromptRolledBackPayload",
    "PromptRejectedPayload",
    "PromptRenderedPayload",
]
