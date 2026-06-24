"""
Agent 3 — Evidence Checker

Pure Python lookup — no LLM call.
Matches claim_object + issue_type to evidence_requirements.csv rules.
"""

from .base import BaseAgent


_ISSUE_TO_APPLIES = {
    "dent": "dent or scratch",
    "scratch": "dent or scratch",
    "crack": "crack, broken, or missing part",
    "glass_shatter": "crack, broken, or missing part",
    "broken_part": "crack, broken, or missing part",
    "missing_part": "crack, broken, or missing part",
    "torn_packaging": "crushed, torn, or seal damage",
    "crushed_packaging": "crushed, torn, or seal damage",
    "water_damage": "water, stain, or label damage",
    "stain": "water, stain, or label damage",
}

_ALWAYS_INCLUDE = {"REQ_GENERAL_OBJECT_PART", "REQ_REVIEW_TRUST"}


class EvidenceChecker(BaseAgent):

    def run(
        self,
        claim_object: str,
        issue_type: str,
        evidence_requirements: list[dict],
        image_count: int = 1,
    ) -> dict:
        applicable_rules = []
        requirement_ids = set(_ALWAYS_INCLUDE)

        if image_count > 1:
            requirement_ids.add("REQ_GENERAL_MULTI_IMAGE")

        applies_to_target = _ISSUE_TO_APPLIES.get(issue_type, "")

        for req in evidence_requirements:
            req_id = req.get("requirement_id", "")
            obj = req.get("claim_object", "all")
            applies_to = req.get("applies_to", "")
            desc = req.get("minimum_image_evidence", "")

            if req_id in requirement_ids:
                applicable_rules.append(desc)
                continue

            if obj not in ("all", claim_object):
                continue

            if applies_to_target and applies_to_target in applies_to:
                requirement_ids.add(req_id)
                applicable_rules.append(desc)
            elif applies_to in ("general claim review", "multi-image rows", "reviewability"):
                requirement_ids.add(req_id)
                if desc not in applicable_rules:
                    applicable_rules.append(desc)

        # Ensure always-included rules are present even if not in loop
        for req in evidence_requirements:
            if req.get("requirement_id") in _ALWAYS_INCLUDE:
                desc = req.get("minimum_image_evidence", "")
                if desc and desc not in applicable_rules:
                    applicable_rules.insert(0, desc)

        return {
            "applicable_rules": applicable_rules,
            "requirement_ids": sorted(requirement_ids),
        }
