"""
Agent 2 — Risk Assessor

Pure Python logic — no LLM call.
Maps user history to risk_flags and produces a summary context string.
"""

from __future__ import annotations
from .base import BaseAgent


class RiskAssessor(BaseAgent):

    def run(
        self,
        user_id: str,
        user_history: dict,
        prompt_injection_detected: bool = False,
    ) -> dict:
        flags: set[str] = set()
        history_row = user_history.get(user_id)

        if history_row is None:
            return {
                "risk_flags": [],
                "history_context": f"No prior history found for {user_id}.",
            }

        raw_flags = history_row.get("history_flags", "none")
        for f in raw_flags.split(";"):
            f = f.strip()
            if f and f != "none":
                flags.add(f)

        # Derived signals
        try:
            past = int(history_row.get("past_claim_count", 0))
            rejected = int(history_row.get("rejected_claim", 0))
            last_90 = int(history_row.get("last_90_days_claim_count", 0))

            if past > 0 and (rejected / past) > 0.5 and last_90 >= 4:
                flags.add("user_history_risk")
            if last_90 >= 5:
                flags.add("manual_review_required")
        except (ValueError, ZeroDivisionError):
            pass

        if prompt_injection_detected:
            flags.add("manual_review_required")

        summary = history_row.get("history_summary", "No summary available.")

        return {
            "risk_flags": sorted(flags) if flags else [],
            "history_context": summary,
        }
