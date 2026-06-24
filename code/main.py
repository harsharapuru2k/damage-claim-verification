"""
main.py — Orchestrator entry point.

Usage:
  python code/main.py [options]

Runs the 5-agent pipeline on dataset/claims.csv and writes output.csv.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Allow imports from code/ directory
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from agents.claim_extractor import ClaimExtractor
from agents.risk_assessor import RiskAssessor
from agents.evidence_checker import EvidenceChecker
from agents.evidence_analyst import EvidenceAnalyst
from agents.decision_synthesizer import DecisionSynthesizer
from utils.csv_loader import load_claims, load_user_history, load_evidence_requirements, write_output
from utils.image_utils import resolve_image_paths
from utils.logger import log_claim_processed
from utils.schema import OUTPUT_COLUMNS


def build_args() -> argparse.Namespace:
    repo_root = str(Path(__file__).parent.parent)
    p = argparse.ArgumentParser(description="Multi-Modal Evidence Review — Damage Claims Verifier")
    p.add_argument("--claims", default=f"{repo_root}/dataset/claims.csv")
    p.add_argument("--history", default=f"{repo_root}/dataset/user_history.csv")
    p.add_argument("--requirements", default=f"{repo_root}/dataset/evidence_requirements.csv")
    p.add_argument("--output", default=f"{repo_root}/output.csv")
    p.add_argument("--verbose", action="store_true", help="Print per-agent output")
    return p.parse_args()


def process_claim(
    row: dict,
    user_history: dict,
    evidence_requirements: list[dict],
    agents: dict,
    repo_root: str,
    verbose: bool = False,
) -> dict:
    user_id = row.get("user_id", "unknown")
    claim_object = row.get("claim_object", "unknown")
    image_paths_str = row.get("image_paths", "")

    print(f"\n{'='*60}")
    print(f"Processing: {user_id} | {claim_object} | {image_paths_str[:50]}...")

    # Agent 1 — Extract claim from conversation
    agent1_out = agents["extractor"].run(
        user_claim=row.get("user_claim", ""),
        claim_object=claim_object,
    )
    if verbose:
        print(f"  [A1] {agent1_out}")

    # Agent 2 — Assess user history risk
    agent2_out = agents["risk_assessor"].run(
        user_id=user_id,
        user_history=user_history,
        prompt_injection_detected=agent1_out.get("prompt_injection_detected", False),
    )
    if verbose:
        print(f"  [A2] {agent2_out}")

    # Resolve image paths
    abs_paths = resolve_image_paths(image_paths_str, repo_root)
    image_count = len(abs_paths)

    # Agent 3 — Look up evidence requirements
    agent3_out = agents["evidence_checker"].run(
        claim_object=claim_object,
        issue_type=agent1_out.get("issue_type", "unknown"),
        evidence_requirements=evidence_requirements,
        image_count=image_count,
    )
    if verbose:
        print(f"  [A3] {agent3_out}")

    # Agent 4 — Analyse images with Gemini Vision
    agent4_out = agents["evidence_analyst"].run(
        image_paths_str=image_paths_str,
        abs_image_paths=abs_paths,
        agent1_out=agent1_out,
        agent3_out=agent3_out,
        claim_object=claim_object,
    )
    if verbose:
        print(f"  [A4] evidence_met={agent4_out.get('evidence_standard_met')} "
              f"issue={agent4_out.get('visible_issue_type')} "
              f"severity={agent4_out.get('severity')}")

    # Agent 5 — Synthesize final decision
    final_row = agents["synthesizer"].run(
        claim_row=row,
        agent1_out=agent1_out,
        agent2_out=agent2_out,
        agent3_out=agent3_out,
        agent4_out=agent4_out,
    )
    if verbose:
        print(f"  [A5] status={final_row.get('claim_status')} severity={final_row.get('severity')}")

    status = final_row.get("claim_status", "unknown")
    print(f"  → {status} | severity={final_row.get('severity')} | flags={final_row.get('risk_flags')}")
    log_claim_processed(user_id, claim_object, status)

    return final_row


def main() -> None:
    args = build_args()
    repo_root = str(Path(__file__).parent.parent)

    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        print("ERROR: AWS credentials not set.")
        print("Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to your .env file.")
        print("See .env.example for the required format.")
        sys.exit(1)

    print("Loading datasets...")
    claims = load_claims(args.claims)
    user_history = load_user_history(args.history)
    evidence_requirements = load_evidence_requirements(args.requirements)
    print(f"  Claims: {len(claims)} rows")
    print(f"  Users: {len(user_history)} records")
    print(f"  Evidence rules: {len(evidence_requirements)} rules")

    agents = {
        "extractor": ClaimExtractor(),
        "risk_assessor": RiskAssessor(),
        "evidence_checker": EvidenceChecker(),
        "evidence_analyst": EvidenceAnalyst(),
        "synthesizer": DecisionSynthesizer(),
    }

    output_rows = []
    start = time.time()

    for i, row in enumerate(claims):
        print(f"\n[{i+1}/{len(claims)}]", end="")
        try:
            result = process_claim(
                row=row,
                user_history=user_history,
                evidence_requirements=evidence_requirements,
                agents=agents,
                repo_root=repo_root,
                verbose=args.verbose,
            )
            output_rows.append(result)
        except Exception as e:
            print(f"\n  ERROR on row {i+1}: {e}")
            output_rows.append(_error_fallback_row(row))

    write_output(output_rows, args.output, OUTPUT_COLUMNS)
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Done. {len(output_rows)} rows written to {args.output}")
    print(f"Total time: {elapsed:.1f}s ({elapsed/len(output_rows):.1f}s per claim)")


def _error_fallback_row(row: dict) -> dict:
    return {
        "user_id": row.get("user_id", ""),
        "image_paths": row.get("image_paths", ""),
        "user_claim": row.get("user_claim", ""),
        "claim_object": row.get("claim_object", ""),
        "evidence_standard_met": "false",
        "evidence_standard_met_reason": "Processing error. Manual review required.",
        "risk_flags": "manual_review_required",
        "issue_type": "unknown",
        "object_part": "unknown",
        "claim_status": "not_enough_information",
        "claim_status_justification": "System error during processing.",
        "supporting_image_ids": "none",
        "valid_image": "true",
        "severity": "unknown",
    }


if __name__ == "__main__":
    main()
