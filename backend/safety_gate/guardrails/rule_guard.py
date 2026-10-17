"""Dependency-light, deterministic Safety Gate.

This is the FALLBACK used when no OpenAI key is configured. It needs no network and no
heavy packages, so the service always has a working gate and the demo never breaks.

It mirrors the reference project's Colang rails (off-topic / jailbreak) and adds the
domain premise flags. Detection is keyword / phrase based and intentionally
conservative: when unsure it lets the enquiry through to the pipeline rather than
blocking a legitimate spectroscopy question.
"""
from __future__ import annotations

import re

from safety_gate.guardrails.base import Guard, GuardCategory, GuardResult
from safety_gate.guardrails.scope import message_for

# --- jailbreak: attempts to change the assistant's role / rules ---
_JAILBREAK_PATTERNS = [
    r"ignore (all |your )?(previous |prior )?instructions",
    r"disregard (your|the) (training|instructions|system prompt|guidelines)",
    r"forget (your|the) (system prompt|instructions|rules)",
    r"you are now (dan|an? unrestricted|in developer mode)",
    r"pretend you (have no|had no) (restrictions|rules|guidelines)",
    r"act as (an? )?(unrestricted|jailbroken|uncensored)",
    r"bypass (your )?(safety|guidelines|filters|rules)",
    r"override your (safety|guidelines|filters)",
    r"\bdo anything now\b",
    r"your new instructions are",
]

# --- injection: content trying to issue instructions through the enquiry text ---
_INJECTION_PATTERNS = [
    r"system\s*:\s*you (are|must)",
    r"</?(system|assistant|instruction)s?>",
    r"\[\s*(system|instruction)s?\s*\]",
    r"print (your|the) (system )?prompt",
    r"reveal (your|the) (system )?prompt",
    r"repeat (the|your) (above|previous) (text|instructions)",
]

# --- off-topic: clearly nothing to do with process spectroscopy ---
_OFF_TOPIC_PATTERNS = [
    r"\btell me a joke\b",
    r"\bwrite (me )?(a )?poem\b",
    r"\bwhat('s| is) the weather\b",
    r"\brecommend (me )?a (movie|film|song|book|restaurant)\b",
    r"\bwho won\b.*\b(game|match|election)\b",
    r"\bcapital of [a-z]+\b",
    r"\bwhat('s| is) \d+\s*[\+\-\*x]\s*\d+\b",
    r"\b(math|history|biology|geography) homework\b",
    r"\bwhat should i (eat|cook|watch)\b",
    r"\btranslate .* (into|to) (french|german|spanish|hindi)\b",
    r"\bwrite (me )?(some )?(python|java|javascript|c\+\+) code\b",
]

# --- domain premise flags ---
_APPROVAL_PATTERNS = [
    r"\b(can you |please |just )?approve (this|the|our|my) (concept|idea|plan|setup|design|cable|link|reuse)\b",
    r"\b(sign off|give (us |me )?(the )?go[- ]?ahead|green light)\b",
    r"\bconfirm (this|it|the concept) (will|is) (work|fine|ok|safe|valid)\b",
    r"\bcan the assistant approve\b",
]
_IMMEDIATE_CONFIG_PATTERNS = [
    r"\b(exact|precise|specific) (sensor|probe|method) (configuration|setup|setting)\b",
    r"\b(recommend|give|tell).{0,40}\b(best|exact) (spectroscopy )?method.{0,40}\b(immediately|right now|now|straight away)\b",
    r"\b(immediately|right now|straight away)\b.{0,40}\b(method|sensor|probe|configuration)\b",
    r"\bexact sensor configuration\b",
]
_RESEARCH_PROOF_PATTERNS = [
    r"\b(quote|cite|use) (its|the|this) (findings|results|study).{0,40}\bproof\b",
    r"\bproof that\b.{0,60}\b(ready|validated|approved|safe)\b",
    r"\bas proof\b.{0,40}\b(ready|validated|suitable)\b",
    r"\b(guide|use for).{0,40}\b(surgery|surgical|clinical|in vivo|tumor|tumour).{0,40}\b(decision|use)\b",
]


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


class RuleGuard:
    """Deterministic keyword/intent gate. Same interface as the LLM gate."""

    name = "rules"

    def check(self, text: str) -> GuardResult:
        t = text.lower().strip()

        # Hard rails first — these stop the request entirely. Order = severity.
        if _any(_JAILBREAK_PATTERNS, t):
            return self._block(GuardCategory.JAILBREAK)
        if _any(_INJECTION_PATTERNS, t):
            return self._block(GuardCategory.INJECTION)
        if _any(_OFF_TOPIC_PATTERNS, t) and not self._looks_spectroscopy(t):
            return self._block(GuardCategory.OFF_TOPIC)

        # Premise flags — on-topic, but push back. Can co-occur; pick the first as
        # primary and record the rest as extras.
        flags: list[GuardCategory] = []
        if _any(_APPROVAL_PATTERNS, t):
            flags.append(GuardCategory.APPROVAL_DEMAND)
        if _any(_IMMEDIATE_CONFIG_PATTERNS, t):
            flags.append(GuardCategory.IMMEDIATE_CONFIG)
        if _any(_RESEARCH_PROOF_PATTERNS, t):
            flags.append(GuardCategory.RESEARCH_AS_PROOF)
        if flags:
            primary, *extra = flags
            return GuardResult(
                passed=False,
                category=primary,
                message=message_for(primary),
                extra=extra,
                engine=self.name,
            )

        return GuardResult(passed=True, category=GuardCategory.NONE, engine=self.name)

    # A weak signal that an "off-topic" trigger is actually a spectroscopy question
    # (e.g. "what is the best method for..."). Keeps the gate from blocking real work.
    @staticmethod
    def _looks_spectroscopy(text: str) -> bool:
        terms = (
            "spectro", "nir", "mir", "atr", "raman", "fluoresc", "uv-vis", "uv vis",
            "probe", "fiber", "fibre", "absorb", "wavelength", "spectral", "process",
            "concentration", "moisture", "contamination", "in-line", "inline", "measure",
        )
        return any(term in text for term in terms)

    def _block(self, category: GuardCategory) -> GuardResult:
        return GuardResult(
            passed=False, category=category, message=message_for(category), engine=self.name
        )
