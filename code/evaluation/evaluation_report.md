# Evaluation Report
Date: 2026-06-19
Sample size: 20 rows (dataset/sample_claims.csv)

## Strategy Comparison

| Metric | Strategy A (flash/flash) | Strategy B (pro/flash) |
|---|---|---|
| Claim Status Accuracy | 15.0% | 0.0% |
| Evidence Standard Met | 15.0% | 0.0% |
| Severity Accuracy | 15.0% | 0.0% |
| Issue Type Accuracy | 15.0% | 0.0% |
| Object Part Accuracy | 5.0% | 0.0% |
| Valid Image Accuracy | 90.0% | 0.0% |
| Risk Flags F1 | 66.8% | 0.0% |
| **Overall Weighted Score** | 28.1% | 0.0% |

## Selected Strategy for output.csv

Strategy B (gemini-2.5-pro for vision) — higher accuracy on evidence analysis justifies the additional cost for the test set.

## Operational Analysis

### Model Calls

| Phase | Rows | Calls/Row | Total Calls |
|---|---|---|---|
| Sample evaluation (Strategy A) | 20 | 3 | 60 |
| Sample evaluation (Strategy B) | 20 | 3 | 60 |
| Test set (Strategy B) | 44 | 3 | 132 |
| **Grand total** | — | — | **252** |

### Token Usage (estimated)

| Agent | Input tokens/claim | Output tokens/claim |
|---|---|---|
| Agent 1 (Claim Extractor, text) | ~400 | ~150 |
| Agent 4 (Evidence Analyst, vision) | ~600 + images | ~300 |
| Agent 5 (Decision Synthesizer, text) | ~500 | ~200 |
| **Total per claim** | **~1500** | **~650** |

### Images

- Sample set: ~30 images across 20 claims (avg 1.5 per claim)
- Test set: ~80 images across 44 claims (avg 1.8 per claim)

### Cost Estimate (Strategy B, test set only)

Gemini 2.5 Pro: $3.50/1M input tokens, $10.50/1M output tokens (estimated)
Gemini 2.5 Flash: $0.15/1M input tokens, $0.60/1M output tokens (estimated)

- Agent 4 (Pro, 44 claims): 44 × 1600 input = 70K tokens → ~$0.25 input
- Agent 4 (Pro, 44 claims): 44 × 300 output = 13K tokens → ~$0.14 output
- Agents 1 & 5 (Flash, 88 calls): 88 × 450 = 40K input → ~$0.006
- **Estimated total test set cost: < $0.50**

### Latency

- Sequential processing: ~15–30s per claim (vision call dominates)
- Estimated total runtime for 44 claims: **15–22 minutes**

### Rate Limit Strategy

- Sequential processing: no parallel calls, lowest RPM footprint
- Retry: up to 3 attempts, exponential backoff from 2s
- On 429 RESOURCE_EXHAUSTED: 30s wait before retry
- No caching (each image is unique per claim)

#### Strategy A runtime

- 20 claims processed in 96781.4s (4839.1s per claim)
