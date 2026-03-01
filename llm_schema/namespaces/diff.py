"""llm_schema.namespaces.diff — Diff & comparison payload types.

Classes
-------
DiffComparisonPayload
    Payload for ``llm.diff.comparison.completed`` events — captures the
    result of comparing two prompt or output artefacts.
DiffReportPayload
    Payload for ``llm.diff.report.generated`` events — describes an
    exported diff report artefact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DiffComparisonPayload:
    """Payload for ``llm.diff.comparison.completed``.

    Parameters
    ----------
    source_id:
        Identifier of the source artefact (e.g. prompt ULID or text hash).
    target_id:
        Identifier of the target artefact being compared against.
    diff_type:
        Type of comparison: ``"text"``, ``"semantic"``, ``"structural"``,
        etc.
    similarity_score:
        Optional float in ``[0.0, 1.0]`` representing similarity.
    source_text:
        Optional raw text of the source artefact.
    target_text:
        Optional raw text of the target artefact.
    diff_result:
        Optional dict containing format-specific diff output.
    """

    source_id: str
    target_id: str
    diff_type: str
    similarity_score: Optional[float] = None
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    diff_result: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.source_id or not isinstance(self.source_id, str):
            raise ValueError("DiffComparisonPayload.source_id must be a non-empty string")
        if not self.target_id or not isinstance(self.target_id, str):
            raise ValueError("DiffComparisonPayload.target_id must be a non-empty string")
        if not self.diff_type or not isinstance(self.diff_type, str):
            raise ValueError("DiffComparisonPayload.diff_type must be a non-empty string")
        if self.similarity_score is not None:
            if not isinstance(self.similarity_score, (int, float)):
                raise ValueError("DiffComparisonPayload.similarity_score must be a number or None")
            if not (0.0 <= self.similarity_score <= 1.0):
                raise ValueError(
                    "DiffComparisonPayload.similarity_score must be in [0.0, 1.0], "
                    f"got {self.similarity_score}"
                )
        if self.diff_result is not None and not isinstance(self.diff_result, dict):
            raise TypeError("DiffComparisonPayload.diff_result must be a dict or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "diff_type": self.diff_type,
        }
        if self.similarity_score is not None:
            result["similarity_score"] = self.similarity_score
        if self.source_text is not None:
            result["source_text"] = self.source_text
        if self.target_text is not None:
            result["target_text"] = self.target_text
        if self.diff_result is not None:
            result["diff_result"] = dict(self.diff_result)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiffComparisonPayload":
        """Reconstruct a :class:`DiffComparisonPayload` from a plain dict."""
        return cls(
            source_id=str(data["source_id"]),
            target_id=str(data["target_id"]),
            diff_type=str(data["diff_type"]),
            similarity_score=data.get("similarity_score"),
            source_text=data.get("source_text"),
            target_text=data.get("target_text"),
            diff_result=dict(data["diff_result"]) if data.get("diff_result") is not None else None,
        )


@dataclass(frozen=True)
class DiffReportPayload:
    """Payload for ``llm.diff.report.generated``.

    Parameters
    ----------
    report_id:
        Unique identifier for the generated report.
    comparison_event_id:
        ULID of the ``llm.diff.comparison.completed`` event this report
        was generated from.
    format:
        Report format: ``"html"``, ``"markdown"``, ``"json"``, etc.
    export_path:
        Optional filesystem path where the report was written.
    export_url:
        Optional URL where the report can be retrieved.
    """

    report_id: str
    comparison_event_id: str
    format: str
    export_path: Optional[str] = None
    export_url: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.report_id or not isinstance(self.report_id, str):
            raise ValueError("DiffReportPayload.report_id must be a non-empty string")
        if not self.comparison_event_id or not isinstance(self.comparison_event_id, str):
            raise ValueError("DiffReportPayload.comparison_event_id must be a non-empty string")
        if not self.format or not isinstance(self.format, str):
            raise ValueError("DiffReportPayload.format must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "report_id": self.report_id,
            "comparison_event_id": self.comparison_event_id,
            "format": self.format,
        }
        if self.export_path is not None:
            result["export_path"] = self.export_path
        if self.export_url is not None:
            result["export_url"] = self.export_url
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiffReportPayload":
        """Reconstruct a :class:`DiffReportPayload` from a plain dict."""
        return cls(
            report_id=str(data["report_id"]),
            comparison_event_id=str(data["comparison_event_id"]),
            format=str(data["format"]),
            export_path=data.get("export_path"),
            export_url=data.get("export_url"),
        )


__all__: list[str] = [
    "DiffComparisonPayload",
    "DiffReportPayload",
]
