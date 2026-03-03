"""llm_toolkit_schema.namespaces — Namespace-specific payload dataclasses.

Each sub-module provides frozen dataclasses that model the ``payload`` field
of :class:`~llm_toolkit_schema.event.Event` for a given namespace.

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
    :class:`RetryTriggeredPayload`, :class:`FencePolicy`
guard
    :class:`GuardBlockedPayload`, :class:`GuardFlaggedPayload`,
    :class:`GuardPolicy`
prompt
    :class:`PromptSavedPayload`, :class:`PromptPromotedPayload`,
    :class:`PromptApprovedPayload`, :class:`PromptRolledBackPayload`
redact
    :class:`PIIDetectedPayload`, :class:`PIIRedactedPayload`,
    :class:`ScanCompletedPayload`
template
    :class:`TemplateRenderedPayload`, :class:`VariableMissingPayload`,
    :class:`TemplateValidationFailedPayload`, :class:`TemplatePolicy`
trace
    :class:`TokenUsage`, :class:`ModelInfo`, :class:`ToolCall`,
    :class:`SpanCompletedPayload` (**FROZEN v1**)
"""

from llm_toolkit_schema.namespaces.cache import CacheEvictedPayload, CacheHitPayload, CacheMissPayload
from llm_toolkit_schema.namespaces.cost import BudgetThresholdPayload, CostRecordedPayload
from llm_toolkit_schema.namespaces.diff import DiffComparisonPayload, DiffReportPayload
from llm_toolkit_schema.namespaces.eval_ import EvalRegressionPayload, EvalScenarioPayload
from llm_toolkit_schema.namespaces.fence import (
    FencePolicy,
    FenceValidationFailedPayload,
    RetryTriggeredPayload,
    ValidationPassedPayload,
)
from llm_toolkit_schema.namespaces.guard import GuardBlockedPayload, GuardFlaggedPayload, GuardPolicy
from llm_toolkit_schema.namespaces.inspect import InspectIssueSummary, InspectReportPayload
from llm_toolkit_schema.namespaces.prompt import (
    PromptApprovedPayload,
    PromptPromotedPayload,
    PromptRejectedPayload,
    PromptRenderedPayload,
    PromptRolledBackPayload,
    PromptSavedPayload,
)
from llm_toolkit_schema.namespaces.redact import PIIDetectedPayload, PIIRedactedPayload, ScanCompletedPayload
from llm_toolkit_schema.namespaces.template import (
    TemplatePolicy,
    TemplateRenderedPayload,
    TemplateValidationFailedPayload,
    VariableMissingPayload,
)
from llm_toolkit_schema.namespaces.trace import ModelInfo, SpanCompletedPayload, TokenUsage, ToolCall

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
    "FencePolicy",
    # guard
    "GuardBlockedPayload",
    "GuardFlaggedPayload",
    "GuardPolicy",
    # inspect
    "InspectIssueSummary",
    "InspectReportPayload",
    # prompt
    "PromptSavedPayload",
    "PromptPromotedPayload",
    "PromptApprovedPayload",
    "PromptRolledBackPayload",
    "PromptRejectedPayload",
    "PromptRenderedPayload",
    # redact (namespace)
    "PIIDetectedPayload",
    "PIIRedactedPayload",
    "ScanCompletedPayload",
    # template
    "TemplateRenderedPayload",
    "VariableMissingPayload",
    "TemplateValidationFailedPayload",
    "TemplatePolicy",
    # trace (FROZEN v1)
    "TokenUsage",
    "ModelInfo",
    "ToolCall",
    "SpanCompletedPayload",
]
