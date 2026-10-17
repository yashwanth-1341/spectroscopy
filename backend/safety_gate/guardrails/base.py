"""Shared types for the Safety Gate: the categories, the verdict, and the interface.

The categories split into two groups:

  Hard rails (out of scope)  — the enquiry should not reach the pipeline at all:
    OFF_TOPIC, JAILBREAK, INJECTION

  Premise flags (insufficient / review) — the enquiry is on-topic, but it rests on a
  premise the assistant must push back on rather than satisfy. These map directly to
  the challenge's "clarification & uncertainty" and "explainability" criteria and to
  evaluation scenarios H04 / H05 / H06:
    APPROVAL_DEMAND     — "approve this concept now" without the needed information
    IMMEDIATE_CONFIG    — "give the exact method + sensor configuration immediately"
    RESEARCH_AS_PROOF   — "quote this research study as proof it is ready for clinical/field use"

A clean enquiry returns category NONE and passed=True.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Protocol


class GuardCategory(str, Enum):
    NONE = "none"
    # hard rails -> out_of_scope
    OFF_TOPIC = "off_topic"
    JAILBREAK = "jailbreak"
    INJECTION = "injection"
    # premise flags -> insufficient (still answered, but with a push-back)
    APPROVAL_DEMAND = "approval_demand"
    IMMEDIATE_CONFIG = "immediate_config"
    RESEARCH_AS_PROOF = "research_as_proof"

    @property
    def is_hard_block(self) -> bool:
        return self in {GuardCategory.OFF_TOPIC, GuardCategory.JAILBREAK, GuardCategory.INJECTION}

    @property
    def is_premise_flag(self) -> bool:
        return self in {
            GuardCategory.APPROVAL_DEMAND,
            GuardCategory.IMMEDIATE_CONFIG,
            GuardCategory.RESEARCH_AS_PROOF,
        }


@dataclass
class GuardResult:
    """The gate's verdict for one enquiry.

    passed=True, category=NONE          -> proceed to the pipeline.
    passed=False, category.is_hard_block -> stop; return an out_of_scope report.
    passed=False, category.is_premise_flag -> stop the normal path; return an
                                              insufficient report with the push-back
                                              and the questions that must come first.
    """

    passed: bool
    category: GuardCategory = GuardCategory.NONE
    message: str = ""
    # Extra premise flags detected alongside the primary one (LLM mode can report several).
    extra: List[GuardCategory] = field(default_factory=list)
    # Which engine produced the verdict — surfaced in the trace. "llm" | "rules"
    engine: str = "rules"

    @property
    def all_flags(self) -> List[GuardCategory]:
        flags = [self.category] if self.category is not GuardCategory.NONE else []
        for c in self.extra:
            if c not in flags:
                flags.append(c)
        return flags


class Guard(Protocol):
    """Every gate implementation exposes exactly this."""

    name: str

    def check(self, text: str) -> GuardResult: ...
