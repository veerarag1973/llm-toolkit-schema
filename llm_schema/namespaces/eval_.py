"""llm_schema.namespaces.eval\\_ — Evaluation scenario payload types.

Classes
-------
EvalScenarioPayload
    ``llm.eval.scenario.completed`` — a single eval scenario finished.
EvalRegressionPayload
    ``llm.eval.regression.detected`` — a performance regression was
    detected versus a prior baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EvalScenarioPayload:
    """Payload for ``llm.eval.scenario.completed``.

    Parameters
    ----------
    scenario_id:
        Unique identifier for the eval scenario.
    scenario_name:
        Human-readable name, e.g. ``"GPT-4o / summarisation / ROUGE-L"``.
    status:
        Outcome: ``"passed"``, ``"failed"``, ``"skipped"``.
    score:
        Optional numeric score, e.g. ROUGE-L F1 or accuracy percentage.
    metrics:
        Optional dict of metric name → value pairs for multi-metric evals.
    baseline_score:
        Optional score from the reference baseline run.
    duration_ms:
        Optional wall-clock time for the scenario in milliseconds.
    """

    scenario_id: str
    scenario_name: str
    status: str
    score: Optional[float] = None
    metrics: Optional[Dict[str, float]] = None
    baseline_score: Optional[float] = None
    duration_ms: Optional[float] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.scenario_id or not isinstance(self.scenario_id, str):
            raise ValueError("EvalScenarioPayload.scenario_id must be a non-empty string")
        if not self.scenario_name or not isinstance(self.scenario_name, str):
            raise ValueError("EvalScenarioPayload.scenario_name must be a non-empty string")
        if self.status not in frozenset({"passed", "failed", "skipped"}):
            raise ValueError(
                f"EvalScenarioPayload.status must be passed/failed/skipped, got {self.status!r}"
            )
        if self.score is not None and not isinstance(self.score, (int, float)):
            raise ValueError("EvalScenarioPayload.score must be a number or None")
        if self.metrics is not None:
            if not isinstance(self.metrics, dict):
                raise TypeError("EvalScenarioPayload.metrics must be a dict or None")
            for k, v in self.metrics.items():
                if not isinstance(k, str) or not isinstance(v, (int, float)):
                    raise TypeError("EvalScenarioPayload.metrics must map str → number")
        if self.baseline_score is not None and not isinstance(self.baseline_score, (int, float)):
            raise ValueError("EvalScenarioPayload.baseline_score must be a number or None")
        if self.duration_ms is not None and (
            not isinstance(self.duration_ms, (int, float)) or self.duration_ms < 0
        ):
            raise ValueError("EvalScenarioPayload.duration_ms must be a non-negative number or None")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "status": self.status,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.metrics is not None:
            result["metrics"] = dict(self.metrics)
        if self.baseline_score is not None:
            result["baseline_score"] = self.baseline_score
        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalScenarioPayload":
        """Reconstruct an :class:`EvalScenarioPayload` from a plain dict."""
        metrics_raw = data.get("metrics")
        return cls(
            scenario_id=str(data["scenario_id"]),
            scenario_name=str(data["scenario_name"]),
            status=str(data["status"]),
            score=data.get("score"),
            metrics=dict(metrics_raw) if metrics_raw is not None else None,
            baseline_score=data.get("baseline_score"),
            duration_ms=data.get("duration_ms"),
        )


@dataclass(frozen=True)
class EvalRegressionPayload:
    """Payload for ``llm.eval.regression.detected``.

    Parameters
    ----------
    scenario_id:
        Unique identifier for the eval scenario.
    scenario_name:
        Human-readable name for the scenario.
    current_score:
        Score achieved in the current run.
    baseline_score:
        Score from the reference baseline.
    regression_delta:
        Signed delta (current − baseline).  Negative indicates degradation.
    threshold:
        Minimum acceptable delta (e.g. ``-0.02`` allows at most 2% drop).
    metrics:
        Optional dict of per-metric current values for diagnostics.
    """

    scenario_id: str
    scenario_name: str
    current_score: float
    baseline_score: float
    regression_delta: float
    threshold: float
    metrics: Optional[Dict[str, float]] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.scenario_id or not isinstance(self.scenario_id, str):
            raise ValueError("EvalRegressionPayload.scenario_id must be a non-empty string")
        if not self.scenario_name or not isinstance(self.scenario_name, str):
            raise ValueError("EvalRegressionPayload.scenario_name must be a non-empty string")
        for attr in ("current_score", "baseline_score", "regression_delta", "threshold"):
            if not isinstance(getattr(self, attr), (int, float)):
                raise ValueError(f"EvalRegressionPayload.{attr} must be a number")
        if self.metrics is not None:
            if not isinstance(self.metrics, dict):
                raise TypeError("EvalRegressionPayload.metrics must be a dict or None")
            for k, v in self.metrics.items():
                if not isinstance(k, str) or not isinstance(v, (int, float)):
                    raise TypeError("EvalRegressionPayload.metrics must map str → number")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "current_score": self.current_score,
            "baseline_score": self.baseline_score,
            "regression_delta": self.regression_delta,
            "threshold": self.threshold,
        }
        if self.metrics is not None:
            result["metrics"] = dict(self.metrics)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvalRegressionPayload":
        """Reconstruct an :class:`EvalRegressionPayload` from a plain dict."""
        metrics_raw = data.get("metrics")
        return cls(
            scenario_id=str(data["scenario_id"]),
            scenario_name=str(data["scenario_name"]),
            current_score=float(data["current_score"]),
            baseline_score=float(data["baseline_score"]),
            regression_delta=float(data["regression_delta"]),
            threshold=float(data["threshold"]),
            metrics=dict(metrics_raw) if metrics_raw is not None else None,
        )


__all__: list[str] = [
    "EvalScenarioPayload",
    "EvalRegressionPayload",
]
