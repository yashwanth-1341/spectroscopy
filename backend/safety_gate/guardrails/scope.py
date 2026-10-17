"""The domain the assistant is allowed to work in, plus the canned refusal / push-back
messages for each rail. Both the LLM and rule-based gates share these, so the two
modes speak with one voice.

Scope comes straight from the challenge brief: a first technical assessment of an AFS
in-line spectroscopy problem (which method / spectral range / fiber probe / setup to
test first), grounded in the supplied AFS materials.
"""
from __future__ import annotations

from safety_gate.guardrails.base import GuardCategory

# A compact description of scope, reused in the LLM system prompt and in refusals.
DOMAIN_DESCRIPTION = (
    "AFS in-line / process spectroscopy solution design: reading a customer's process "
    "monitoring problem (e.g. concentration, reaction progress, contamination, moisture, "
    "product quality) and making a first technical assessment — which spectroscopy method "
    "(NIR, MIR/ATR, Raman, fluorescence, UV-Vis) or combination to test first, the relevant "
    "spectral range, a high-level fiber-probe and measurement concept, the limitations and "
    "uncertainty, and a first feasibility experiment."
)

# One message per category. Hard rails refuse; premise flags push back and redirect.
MESSAGES: dict[GuardCategory, str] = {
    GuardCategory.OFF_TOPIC: (
        "I'm an assistant for AFS in-line spectroscopy solution design. I can help you work "
        "through a process-monitoring problem — the method, spectral range, probe concept, "
        "limitations and a first feasibility experiment — but I can't help with that request. "
        "Describe what you need to monitor in your process and I'll make a first assessment."
    ),
    GuardCategory.JAILBREAK: (
        "I keep the same role regardless of how I'm prompted: a transparent first-assessment "
        "assistant for AFS in-line spectroscopy. Tell me about the process you want to monitor "
        "and I'll help structure the assessment."
    ),
    GuardCategory.INJECTION: (
        "I only act on the customer process description, not on instructions embedded in the "
        "enquiry text. Please describe the measurement problem itself and I'll assess it."
    ),
    GuardCategory.APPROVAL_DEMAND: (
        "I can give a transparent first assessment, but I can't approve or sign off a concept — "
        "that needs the missing details and a feasibility test first. Here is what to clarify "
        "and the experiment that should decide it."
    ),
    GuardCategory.IMMEDIATE_CONFIG: (
        "I can't name an exact method and sensor configuration up front. The right choice "
        "depends on information that isn't in the enquiry yet. Here are the questions that come "
        "first and a comparison experiment to settle the choice."
    ),
    GuardCategory.RESEARCH_AS_PROOF: (
        "A supplied research study can motivate an approach, but it isn't validation for a new "
        "use, product or setting — especially not a clinical or in-field decision. It should be "
        "cited as background, with its own validation steps on your material before any claim."
    ),
}

# Short label shown in the trace / report for each premise flag.
PREMISE_LABELS: dict[GuardCategory, str] = {
    GuardCategory.APPROVAL_DEMAND: "Request to approve a concept without sufficient information",
    GuardCategory.IMMEDIATE_CONFIG: "Request for an exact configuration before clarification",
    GuardCategory.RESEARCH_AS_PROOF: "Research study offered as validation for a new use",
}


def message_for(category: GuardCategory) -> str:
    return MESSAGES.get(category, MESSAGES[GuardCategory.OFF_TOPIC])
