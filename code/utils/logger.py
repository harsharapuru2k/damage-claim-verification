from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / "hackerrank_orchestrate" / "log.txt"

_SECRET_PATTERN = re.compile(
    r"(AIza[0-9A-Za-z\-_]{35}|ya29\.[0-9A-Za-z\-_]+|[A-Za-z0-9]{39})",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    return _SECRET_PATTERN.sub("[REDACTED]", str(text))


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_turn(title: str, user_prompt: str, summary: str, actions: list[str]) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n## [{_ts()}] {title[:80]}\n\n"
            f"User Prompt (verbatim, secrets redacted):\n{_redact(user_prompt)}\n\n"
            f"Agent Response Summary:\n{_redact(summary)}\n\n"
            f"Actions:\n"
        )
        for action in actions:
            entry += f"* {_redact(action)}\n"
        entry += (
            f"\nContext:\n"
            f"tool=Claude Code (claude-sonnet-4-6)\n"
            f"branch=main\n"
            f"repo_root={os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))}\n"
            f"worktree=main\n"
            f"parent_agent=none\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def log_claim_processed(claim_id: str, claim_object: str, status: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n## [{_ts()}] Claim processed: {claim_id} ({claim_object})\n\n"
            f"Agent Response Summary:\n"
            f"Processed claim {claim_id} for object type '{claim_object}'. "
            f"Final status: {status}.\n\n"
            f"Actions:\n"
            f"* evidence_analyst: Gemini vision call\n"
            f"* decision_synthesizer: Gemini text call\n"
            f"* output row written to output.csv\n\n"
            f"Context:\n"
            f"tool=Claude Code (claude-sonnet-4-6)\n"
            f"branch=main\n"
            f"repo_root={os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))}\n"
            f"worktree=main\n"
            f"parent_agent=none\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
