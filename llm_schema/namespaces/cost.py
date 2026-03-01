"""llm_schema.namespaces.cost — Cost recording payload types.

Classes
-------
CostRecordedPayload
    ``llm.cost.recorded`` — captures the cost of one inference span.
BudgetThresholdPayload
    ``llm.cost.budget.threshold`` — signals a budget threshold crossing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CostRecordedPayload:
    """Payload for ``llm.cost.recorded``.

    Parameters
    ----------
    span_event_id:
        ULID of the ``llm.trace.span.completed`` event this cost is
        attributed to.
    model_name:
        Short model identifier, e.g. ``"gpt-4o"``.
    provider:
        Provider name, e.g. ``"openai"``.
    prompt_tokens:
        Number of prompt tokens billed.
    completion_tokens:
        Number of completion tokens billed.
    total_tokens:
        Total tokens billed (may differ from prompt + completion due to
        provider-specific accounting).
    cost_usd:
        Computed cost in US dollars.
    currency:
        ISO 4217 currency code (defaults to ``"USD"``).
    budget_id:
        Optional identifier of the budget this cost is attributed to.
    """

    span_event_id: str
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    currency: str = "USD"
    budget_id: Optional[str] = None

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        for attr in ("span_event_id", "model_name", "provider"):
            value = getattr(self, attr)
            if not value or not isinstance(value, str):
                raise ValueError(f"CostRecordedPayload.{attr} must be a non-empty string")
        for attr in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = getattr(self, attr)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"CostRecordedPayload.{attr} must be a non-negative int")
        if not isinstance(self.cost_usd, (int, float)) or self.cost_usd < 0:
            raise ValueError("CostRecordedPayload.cost_usd must be a non-negative number")
        if not self.currency or not isinstance(self.currency, str):
            raise ValueError("CostRecordedPayload.currency must be a non-empty string")

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "span_event_id": self.span_event_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "currency": self.currency,
        }
        if self.budget_id is not None:
            result["budget_id"] = self.budget_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostRecordedPayload":
        """Reconstruct a :class:`CostRecordedPayload` from a plain dict."""
        return cls(
            span_event_id=str(data["span_event_id"]),
            model_name=str(data["model_name"]),
            provider=str(data["provider"]),
            prompt_tokens=int(data["prompt_tokens"]),
            completion_tokens=int(data["completion_tokens"]),
            total_tokens=int(data["total_tokens"]),
            cost_usd=float(data["cost_usd"]),
            currency=str(data.get("currency", "USD")),
            budget_id=data.get("budget_id"),
        )


@dataclass(frozen=True)
class BudgetThresholdPayload:
    """Payload for ``llm.cost.budget.threshold``.

    Parameters
    ----------
    budget_id:
        Unique identifier of the budget that was crossed.
    threshold_type:
        Type of threshold: ``"warning"``, ``"critical"``, ``"hard_limit"``.
    threshold_usd:
        Configured threshold amount in US dollars.
    current_spend_usd:
        Current total spend at the time of the event.
    percentage_used:
        Percentage of budget consumed in ``[0.0, 100.0+]``.
    org_id:
        Optional organisation identifier for multi-tenant deployments.
    """

    budget_id: str
    threshold_type: str
    threshold_usd: float
    current_spend_usd: float
    percentage_used: float
    org_id: Optional[str] = None

    _VALID_THRESHOLD_TYPES: frozenset = frozenset({"warning", "critical", "hard_limit"})

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.budget_id or not isinstance(self.budget_id, str):
            raise ValueError("BudgetThresholdPayload.budget_id must be a non-empty string")
        if self.threshold_type not in frozenset({"warning", "critical", "hard_limit"}):
            raise ValueError(
                "BudgetThresholdPayload.threshold_type must be warning/critical/hard_limit, "
                f"got {self.threshold_type!r}"
            )
        if not isinstance(self.threshold_usd, (int, float)) or self.threshold_usd < 0:
            raise ValueError(
                "BudgetThresholdPayload.threshold_usd must be a non-negative number"
            )
        if not isinstance(self.current_spend_usd, (int, float)) or self.current_spend_usd < 0:
            raise ValueError(
                "BudgetThresholdPayload.current_spend_usd must be a non-negative number"
            )
        if not isinstance(self.percentage_used, (int, float)) or self.percentage_used < 0:
            raise ValueError(
                "BudgetThresholdPayload.percentage_used must be a non-negative number"
            )

    # -----------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict suitable for ``Event.payload``."""
        result: Dict[str, Any] = {
            "budget_id": self.budget_id,
            "threshold_type": self.threshold_type,
            "threshold_usd": self.threshold_usd,
            "current_spend_usd": self.current_spend_usd,
            "percentage_used": self.percentage_used,
        }
        if self.org_id is not None:
            result["org_id"] = self.org_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetThresholdPayload":
        """Reconstruct a :class:`BudgetThresholdPayload` from a plain dict."""
        return cls(
            budget_id=str(data["budget_id"]),
            threshold_type=str(data["threshold_type"]),
            threshold_usd=float(data["threshold_usd"]),
            current_spend_usd=float(data["current_spend_usd"]),
            percentage_used=float(data["percentage_used"]),
            org_id=data.get("org_id"),
        )


__all__: list[str] = [
    "CostRecordedPayload",
    "BudgetThresholdPayload",
]
