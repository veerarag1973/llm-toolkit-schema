"""llm_schema.namespaces.template — Prompt template payload types.

Classes
-------
TemplateRenderedPayload
    ``llm.template.rendered`` — a template was rendered successfully.
VariableMissingPayload
    ``llm.template.variable.missing`` — required variables were absent.
TemplateValidationFailedPayload
    ``llm.template.validation.failed`` — the template itself failed static
    validation (distinct from :class:`~llm_schema.namespaces.fence.FenceValidationFailedPayload`,
    which validates *rendered output*).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TemplateRenderedPayload:
    """Payload for ``llm.template.rendered``.

    Parameters
    ----------
    template_id:
        Unique identifier for the template.
    template_version:
        Version string for the template, e.g. ``"2.1.0"``.
    variable_count:
        Number of variables that were substituted during rendering.
    render_duration_ms:
        Optional wall-clock render time in milliseconds.
    output_length:
        Optional character length of the rendered output.
    """

    template_id: str
    template_version: str
    variable_count: int
    render_duration_ms: Optional[float] = None
    output_length: Optional[int] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError("TemplateRenderedPayload.template_id must be a non-empty string")
        if not self.template_version or not isinstance(self.template_version, str):
            raise ValueError("TemplateRenderedPayload.template_version must be a non-empty string")
        if not isinstance(self.variable_count, int) or self.variable_count < 0:
            raise ValueError("TemplateRenderedPayload.variable_count must be a non-negative int")
        if self.render_duration_ms is not None and (
            not isinstance(self.render_duration_ms, (int, float))
            or self.render_duration_ms < 0
        ):
            raise ValueError(
                "TemplateRenderedPayload.render_duration_ms must be a non-negative number or None"
            )
        if self.output_length is not None and (
            not isinstance(self.output_length, int) or self.output_length < 0
        ):
            raise ValueError(
                "TemplateRenderedPayload.output_length must be a non-negative int or None"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "template_id": self.template_id,
            "template_version": self.template_version,
            "variable_count": self.variable_count,
        }
        if self.render_duration_ms is not None:
            result["render_duration_ms"] = self.render_duration_ms
        if self.output_length is not None:
            result["output_length"] = self.output_length
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateRenderedPayload":
        """Reconstruct a :class:`TemplateRenderedPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            template_version=str(data["template_version"]),
            variable_count=int(data["variable_count"]),
            render_duration_ms=data.get("render_duration_ms"),
            output_length=(
                int(data["output_length"]) if data.get("output_length") is not None else None
            ),
        )


@dataclass(frozen=True)
class VariableMissingPayload:
    """Payload for ``llm.template.variable.missing``.

    Parameters
    ----------
    template_id:
        Unique identifier for the template that was being rendered.
    missing_variables:
        List of variable names that were required but absent from the
        render context.
    required_variables:
        Full list of variable names declared as required by the template.
    """

    template_id: str
    missing_variables: List[str]
    required_variables: List[str]

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError("VariableMissingPayload.template_id must be a non-empty string")
        if not isinstance(self.missing_variables, list) or not self.missing_variables:
            raise ValueError("VariableMissingPayload.missing_variables must be a non-empty list")
        for v in self.missing_variables:
            if not isinstance(v, str):
                raise TypeError("Each missing_variable must be a string")
        if not isinstance(self.required_variables, list) or not self.required_variables:
            raise ValueError(
                "VariableMissingPayload.required_variables must be a non-empty list"
            )
        for v in self.required_variables:
            if not isinstance(v, str):
                raise TypeError("Each required_variable must be a string")
        # Every missing variable must appear in required variables.
        missing_set = frozenset(self.missing_variables)
        required_set = frozenset(self.required_variables)
        extra = missing_set - required_set
        if extra:
            raise ValueError(
                f"missing_variables contains names not in required_variables: {extra}"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        return {
            "template_id": self.template_id,
            "missing_variables": list(self.missing_variables),
            "required_variables": list(self.required_variables),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableMissingPayload":
        """Reconstruct a :class:`VariableMissingPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            missing_variables=list(data["missing_variables"]),
            required_variables=list(data["required_variables"]),
        )


@dataclass(frozen=True)
class TemplateValidationFailedPayload:
    """Payload for ``llm.template.validation.failed``.

    This event is raised when the *template definition itself* fails
    validation (e.g. syntax errors, undefined variables in the template
    body), as opposed to validation of rendered LLM output which is handled
    by :class:`~llm_schema.namespaces.fence.FenceValidationFailedPayload`.

    Parameters
    ----------
    template_id:
        Unique identifier for the template that failed validation.
    validation_errors:
        Ordered list of human-readable error messages.
    validator:
        Optional identifier of the validator component that raised the
        errors.
    """

    template_id: str
    validation_errors: List[str]
    validator: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.template_id or not isinstance(self.template_id, str):
            raise ValueError(
                "TemplateValidationFailedPayload.template_id must be a non-empty string"
            )
        if not isinstance(self.validation_errors, list) or not self.validation_errors:
            raise ValueError(
                "TemplateValidationFailedPayload.validation_errors must be a non-empty list"
            )
        for err in self.validation_errors:
            if not isinstance(err, str):
                raise TypeError("Each validation_error must be a string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "template_id": self.template_id,
            "validation_errors": list(self.validation_errors),
        }
        if self.validator is not None:
            result["validator"] = self.validator
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateValidationFailedPayload":
        """Reconstruct a :class:`TemplateValidationFailedPayload` from a plain dict."""
        return cls(
            template_id=str(data["template_id"]),
            validation_errors=list(data["validation_errors"]),
            validator=data.get("validator"),
        )


__all__: list[str] = [
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
]
