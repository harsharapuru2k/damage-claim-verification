from enum import Enum


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class IssueType(str, Enum):
    DENT = "dent"
    SCRATCH = "scratch"
    CRACK = "crack"
    GLASS_SHATTER = "glass_shatter"
    BROKEN_PART = "broken_part"
    MISSING_PART = "missing_part"
    TORN_PACKAGING = "torn_packaging"
    CRUSHED_PACKAGING = "crushed_packaging"
    WATER_DAMAGE = "water_damage"
    STAIN = "stain"
    NONE = "none"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


CAR_PARTS = {
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender", "quarter_panel",
    "body", "unknown",
}

LAPTOP_PARTS = {
    "screen", "keyboard", "trackpad", "hinge", "lid", "corner",
    "port", "base", "body", "unknown",
}

PACKAGE_PARTS = {
    "box", "package_corner", "package_side", "seal", "label",
    "contents", "item", "unknown",
}

OBJECT_PARTS = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS,
}

RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required",
}

ISSUE_TYPES = {e.value for e in IssueType}
SEVERITY_VALUES = {e.value for e in Severity}
CLAIM_STATUSES = {e.value for e in ClaimStatus}

OUTPUT_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason",
    "risk_flags", "issue_type", "object_part",
    "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity",
]

INJECTION_PHRASES = [
    "approve immediately", "skip manual review", "skip review",
    "ignore all previous instructions", "ignore previous instructions",
    "follow the note", "follow the instruction", "mark this supported",
    "mark this as supported", "approve the claim", "auto approve",
    "claim approved", "approve this", "mark supported",
    "keep reopening tickets", "escalate publicly", "i will escalate",
    "reject again", "tired of repeat reviews",
]


def validate_issue_type(value: str, claim_object: str) -> str:
    if value in ISSUE_TYPES:
        return value
    return "unknown"


def validate_object_part(value: str, claim_object: str) -> str:
    allowed = OBJECT_PARTS.get(claim_object, set())
    if value in allowed:
        return value
    return "unknown"


def validate_severity(value: str) -> str:
    if value in SEVERITY_VALUES:
        return value
    return "unknown"


def validate_claim_status(value: str) -> str:
    if value in CLAIM_STATUSES:
        return value
    return "not_enough_information"


def validate_risk_flags(flags: list) -> str:
    if not flags:
        return "none"
    valid = [f for f in flags if f in RISK_FLAGS]
    if not valid:
        return "none"
    deduped = sorted(set(valid))
    if "none" in deduped and len(deduped) > 1:
        deduped.remove("none")
    return ";".join(deduped)
