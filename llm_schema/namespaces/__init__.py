"""llm_schema.namespaces — Namespace-specific payload dataclasses.

Each sub-module provides frozen dataclasses that model the ``payload`` field
of :class:`~llm_schema.event.Event` for a given namespace.

All payload classes share the same contract:

* ``frozen=True`` dataclass — immutable after construction.
* ``to_dict() -> dict`` — serialise to a plain dict for ``Event.payload``.
* ``from_dict(data) -> cls`` — reconstruct from a plain dict.
* ``__post_init__`` — validates every field at construction time.

Sub-modules
-----------
cache
    :class:`CacheHitPayload`, :class:`CacheMissPayload`,
    :class:`CacheEvictedPayload`
cost
    :class:`CostRecordedPayload`, :class:`BudgetThresholdPayload`
diff
    :class:`DiffComparisonPayload`, :class:`DiffReportPayload`
eval\\_
    :class:`EvalScenarioPayload`, :class:`EvalRegressionPayload`
fence
    :class:`ValidationPassedPayload`, :class:`FenceValidationFailedPayload`,
    :class:`RetryTriggeredPayload`
guard
    :class:`GuardBlockedPayload`, :class:`GuardFlaggedPayload`
prompt
    :class:`PromptSavedPayload`, :class:`PromptPromotedPayload`,
    :class:`PromptApprovedPayload`, :class:`PromptRolledBackPayload`
redact
    :class:`PIIDetectedPayload`, :class:`PIIRedactedPayload`,
    :class:`ScanCompletedPayload`
template
    :class:`TemplateRenderedPayload`, :class:`VariableMissingPayload`,
    :class:`TemplateValidationFailedPayload`
trace
    :class:`TokenUsage`, :class:`ModelInfo`, :class:`ToolCall`,
    :class:`SpanCompletedPayload` (**FROZEN v1**)
"""

from llm_schema.namespaces.cache import CacheEvictedPayload, CacheHitPayload, CacheMissPayload
from llm_schema.namespaces.cost import BudgetThresholdPayload, CostRecordedPayload
from llm_schema.namespaces.diff import DiffComparisonPayload, DiffReportPayload
from llm_schema.namespaces.eval_ import EvalRegressionPayload, EvalScenarioPayload
from llm_schema.namespaces.fence import (
    FenceValidationFailedPayload,
    RetryTriggeredPayload,
    ValidationPassedPayload,
)
from llm_schema.namespaces.guard import GuardBlockedPayload, GuardFlaggedPayload
from llm_schema.namespaces.prompt import (
    PromptApprovedPayload,
    PromptPromotedPayload,
    PromptRolledBackPayload,
    PromptSavedPayload,
)
from llm_schema.namespaces.redact import PIIDetectedPayload, PIIRedactedPayload, ScanCompletedPayload
from llm_schema.namespaces.template import (
    TemplateRenderedPayload,
    TemplateValidationFailedPayload,
    VariableMissingPayload,
)
from llm_schema.namespaces.trace import ModelInfo, SpanCompletedPayload, TokenUsage, ToolCall

__all__: list[str] = [
    # cache
    "CacheHitPayload",
    "CacheMissPayload",
    "CacheEvictedPayload",
    # cost
    "CostRecordedPayload",
    "BudgetThresholdPayload",
    # diff
    "DiffComparisonPayload",
    "DiffReportPayload",
    # eval
    "EvalScenarioPayload",
    "EvalRegressionPayload",
    # fence
    "ValidationPassedPayload",
    "FenceValidationFailedPayload",
    "RetryTriggeredPayload",
    # guard
    "GuardBlockedPayload",
    "GuardFlaggedPayload",
    # prompt
    "PromptSavedPayload",
    "PromptPromotedPayload",
    "PromptApprovedPayload",
    "PromptRolledBackPayload",
    # redact (namespace)
    "PIIDetectedPayload",
    "PIIRedactedPayload",
    "ScanCompletedPayload",
    # template
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
    # trace (FROZEN v1)
    "TokenUsage",
    "ModelInfo",
    "ToolCall",
    "SpanCompletedPayload",
]
