"""Evaluation metrics for claim verification output."""


def exact_match_accuracy(predicted: list[str], ground_truth: list[str]) -> float:
    if not ground_truth:
        return 0.0
    correct = sum(p == g for p, g in zip(predicted, ground_truth))
    return correct / len(ground_truth)


def flag_set_f1(predicted: list[str], ground_truth: list[str]) -> float:
    """Compute macro-averaged F1 over semicolon-separated flag sets."""
    if not ground_truth:
        return 0.0
    f1_scores = []
    for pred, gt in zip(predicted, ground_truth):
        pred_set = set(p.strip() for p in pred.split(";") if p.strip() and p.strip() != "none")
        gt_set = set(g.strip() for g in gt.split(";") if g.strip() and g.strip() != "none")

        if not gt_set and not pred_set:
            f1_scores.append(1.0)
            continue
        if not gt_set or not pred_set:
            f1_scores.append(0.0)
            continue

        intersection = pred_set & gt_set
        precision = len(intersection) / len(pred_set)
        recall = len(intersection) / len(gt_set)
        if precision + recall == 0:
            f1_scores.append(0.0)
        else:
            f1_scores.append(2 * precision * recall / (precision + recall))

    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


def compute_all_metrics(predictions: list[dict], ground_truth: list[dict]) -> dict:
    fields_exact = [
        "claim_status",
        "evidence_standard_met",
        "severity",
        "issue_type",
        "object_part",
        "valid_image",
    ]
    results = {}

    for field in fields_exact:
        pred_vals = [str(p.get(field, "")).strip().lower() for p in predictions]
        gt_vals = [str(g.get(field, "")).strip().lower() for g in ground_truth]
        results[field] = exact_match_accuracy(pred_vals, gt_vals)

    pred_flags = [str(p.get("risk_flags", "none")) for p in predictions]
    gt_flags = [str(g.get("risk_flags", "none")) for g in ground_truth]
    results["risk_flags_f1"] = flag_set_f1(pred_flags, gt_flags)

    weights = {
        "claim_status": 3.0,
        "evidence_standard_met": 2.0,
        "severity": 1.5,
        "issue_type": 1.5,
        "object_part": 1.5,
        "valid_image": 1.0,
        "risk_flags_f1": 2.0,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(results[k] * weights[k] for k in weights)
    results["overall_weighted"] = weighted_sum / total_weight

    return results


def per_row_comparison(predictions: list[dict], ground_truth: list[dict]) -> list[dict]:
    rows = []
    for i, (pred, gt) in enumerate(zip(predictions, ground_truth)):
        row = {
            "row": i + 1,
            "user_id": gt.get("user_id", ""),
            "claim_object": gt.get("claim_object", ""),
        }
        for field in ["claim_status", "evidence_standard_met", "severity", "issue_type", "object_part"]:
            row[f"pred_{field}"] = pred.get(field, "")
            row[f"gt_{field}"] = gt.get(field, "")
            row[f"match_{field}"] = str(pred.get(field, "")).lower() == str(gt.get(field, "")).lower()
        rows.append(row)
    return rows
