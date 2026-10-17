"""The Safety Gate (section 2 of the architecture).

Public surface:
    build_guard()  -> a Guard with a `.check(text) -> GuardResult` method
    GuardResult    -> the verdict (passed / which rail fired / message)
    GuardCategory  -> the set of rail categories

`build_guard()` picks the mode once, at import/startup, based on config:
    OPENAI_API_KEY present -> LLMGuard (primary)
    otherwise              -> RuleGuard (dependency-light fallback)
Both implement the same interface, so callers never branch on the mode.
"""
from __future__ import annotations

from safety_gate.config import settings
from safety_gate.guardrails.base import Guard, GuardCategory, GuardResult
from safety_gate.guardrails.rule_guard import RuleGuard

__all__ = ["build_guard", "Guard", "GuardResult", "GuardCategory"]


def build_guard() -> Guard:
    """Select the Safety Gate implementation for this process."""
    if settings.llm_guard_available:
        # Imported lazily so the openai package is only needed in LLM mode.
        try:
            from safety_gate.guardrails.llm_guard import LLMGuard

            return LLMGuard(fallback=RuleGuard())
        except Exception as exc:  # openai missing / import failure -> degrade gracefully
            import logging

            logging.getLogger("spectrasense.guard").warning(
                "LLM guard unavailable (%s); falling back to rule-based gate.", exc
            )
    return RuleGuard()
