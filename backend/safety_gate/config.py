"""Runtime configuration, read once from the environment.

The one decision that matters here is which Safety Gate runs:
  - OPENAI_API_KEY present  -> LLM-backed guard (primary, the main feature)
  - OPENAI_API_KEY absent    -> rule-based guard (dependency-light fallback)
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


@dataclass(frozen=True)
class Settings:
    # --- Safety Gate: LLM provider (OpenAI) ---
    openai_api_key: str | None = _env("OPENAI_API_KEY")
    openai_model: str = _env("OPENAI_MODEL", "gpt-4o-mini")  # fast, cheap classifier
    openai_base_url: str | None = _env("OPENAI_BASE_URL")  # for OpenAI-compatible gateways

    # --- behaviour ---
    # Force the fallback even when a key exists (useful for demos / tests): GUARD_MODE=rules
    guard_mode_override: str | None = _env("GUARD_MODE")

    @property
    def llm_guard_available(self) -> bool:
        """True when the LLM gate can run (key present and not explicitly disabled)."""
        if self.guard_mode_override == "rules":
            return False
        if self.guard_mode_override == "llm":
            return True
        return bool(self.openai_api_key)


settings = Settings()
