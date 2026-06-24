# Multi-Modal Damage Claim Verification System

> HackerRank Orchestrate Hackathon · June 2026

An AI pipeline that verifies insurance damage claims by analyzing submitted photos, customer conversation transcripts, and user history — producing a structured, auditable verdict for each claim.

---

## Overview

Insurance claim fraud costs the industry billions annually. Manual image review is slow and inconsistent. This system automates the evidence review step by combining **vision AI**, **conversation parsing**, and **rule-based risk scoring** into a five-agent pipeline.

For each claim the system:
- Extracts what the customer is actually claiming from a noisy conversation transcript
- Inspects submitted images using a multimodal LLM
- Checks the images against minimum evidence requirements
- Scores user-history risk without letting it override clear visual evidence
- Produces a final verdict: `supported`, `contradicted`, or `not_enough_information`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                          │
│                         main.py                              │
└───────┬──────────┬──────────────┬──────────────┬────────────┘
        │          │              │              │
        ▼          ▼              ▼              ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐
  │  Agent 1  │ │  Agent 2  │ │  Agent 3  │ │     Agent 4      │
  │  Claim    │ │  Risk     │ │ Evidence  │ │    Evidence      │
  │ Extractor │ │ Assessor  │ │ Checker   │ │    Analyst       │
  │           │ │           │ │           │ │  (Vision LLM)    │
  │ LLM: text │ │ Pure Py   │ │ Pure Py   │ │ LLM: multimodal  │
  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └────────┬─────────┘
        │             │             │                  │
        └─────────────┴─────────────┴──────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │     Agent 5      │
                          │    Decision      │
                          │  Synthesizer     │
                          │   LLM: text      │
                          └────────┬─────────┘
                                   │
                                   ▼
                               output.csv
```

### Agent Responsibilities

| Agent | Role | LLM Call |
|---|---|---|
| **1 — Claim Extractor** | Parses conversation transcript → damage summary, object part, issue type. Detects prompt injection. | Text |
| **2 — Risk Assessor** | Maps user history → risk flags. Derived signals: rejection rate, claim frequency. | None |
| **3 — Evidence Checker** | Looks up minimum evidence rules for the claim type. | None |
| **4 — Evidence Analyst** | Sends all images to vision model. Returns verdict, severity, supporting image IDs, image-level risk flags. | Vision |
| **5 — Decision Synthesizer** | Combines all agent outputs → final output row. Enforces hard safety rules. | Text |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| LLM Provider | **AWS Bedrock** |
| Vision Model | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Text Model | `anthropic.claude-3-5-haiku-20241022-v1:0` |
| AWS SDK | `boto3` |
| Config | `python-dotenv` |
| Data I/O | Python `csv` (stdlib) |

---

## Dataset

| File | Rows | Purpose |
|---|---|---|
| `dataset/sample_claims.csv` | 20 | Labeled ground truth — used for evaluation |
| `dataset/claims.csv` | 44 | Unlabeled test set — system produces `output.csv` |
| `dataset/user_history.csv` | 47 users | Historical claim counts and risk flags |
| `dataset/evidence_requirements.csv` | 11 rules | Minimum image evidence per claim type |
| `dataset/images/` | ~80 images | JPEG photos submitted with claims |

**Claim object types:** `car` · `laptop` · `package`

---

## Sample Output

| user_id | claim_object | claim_status | severity | issue_type | object_part | risk_flags |
|---|---|---|---|---|---|---|
| user_001 | car | supported | medium | dent | rear_bumper | none |
| user_002 | car | not_enough_information | unknown | broken_part | front_bumper | wrong_object;claim_mismatch;manual_review_required |
| user_005 | car | contradicted | low | scratch | rear_bumper | claim_mismatch;user_history_risk;manual_review_required |
| user_009 | laptop | supported | medium | crack | screen | none |
| user_015 | package | supported | medium | crushed_packaging | package_corner | none |
| user_032 | package | not_enough_information | unknown | unknown | contents | cropped_or_obstructed;manual_review_required |

---

## Safety & Integrity Rules

### Evidence Primacy
Images are the **primary source of truth**. User history adds risk context but cannot override a clear visual verdict — a high-risk user with clean images still gets `supported`.

### Hard Decision Rules

| Condition | Forced Output |
|---|---|
| `evidence_standard_met = false` | `claim_status = not_enough_information` |
| `valid_image = false` | `claim_status = not_enough_information` |
| Prompt injection detected | `text_instruction_present + manual_review_required` always added |
| API error | Falls back to `not_enough_information` — never auto-approves |

### Prompt Injection Defense
Several claims in the dataset contain adversarial text:
- Conversations: *"approve immediately"*, *"ignore all previous instructions"*, *"mark this supported"*
- Images: handwritten notes with approval instructions

**Agent 1** detects injection patterns in conversation text. **Agent 4** is explicitly instructed to describe only visual content and ignore any embedded instructions. **Agent 5** hard-codes `text_instruction_present` into the final flags regardless of the LLM response.

### Multi-Language Support
Conversations arrive in English, Hindi (Devanagari + romanised), Spanish, and mixed languages. Agent 1 extracts claims in English regardless of input language.

---

## Setup & Usage

### Prerequisites
- Python 3.10+
- AWS account with Bedrock access enabled for Claude models in your region

### Install

```bash
git clone https://github.com/harsharapuru2k/damage-claim-verification.git
cd damage-claim-verification
pip install -r code/requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env and add your AWS credentials
```

`.env`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

### Run on test set

```bash
python code/main.py
# Writes output.csv to repo root
```

### Evaluate on labeled sample set

```bash
python code/evaluation/main.py --strategy both
# Prints per-field accuracy and writes code/evaluation/evaluation_report.md
```

---

## Project Structure

```
.
├── CLAUDE.md                          # Architecture contract and safety rules
├── code/
│   ├── main.py                        # Orchestrator — processes claims.csv → output.csv
│   ├── requirements.txt
│   ├── agents/
│   │   ├── claim_extractor.py         # Agent 1: conversation parser
│   │   ├── risk_assessor.py           # Agent 2: history risk scorer
│   │   ├── evidence_checker.py        # Agent 3: evidence rule lookup
│   │   ├── evidence_analyst.py        # Agent 4: vision model image analysis
│   │   └── decision_synthesizer.py   # Agent 5: final verdict with safety rules
│   ├── utils/
│   │   ├── gemini_client.py           # AWS Bedrock API client with retry logic
│   │   ├── csv_loader.py              # CSV I/O helpers
│   │   ├── image_utils.py             # Image path resolution
│   │   ├── logger.py                  # Session log writer
│   │   └── schema.py                  # Allowed values, enums, validators
│   └── evaluation/
│       ├── main.py                    # Evaluation entry point
│       └── metrics.py                 # Accuracy + F1 metrics
└── dataset/
    ├── claims.csv
    ├── sample_claims.csv
    ├── user_history.csv
    ├── evidence_requirements.csv
    └── images/
```

---

## Design Tradeoffs

### Sequential vs Parallel Processing
**Chose sequential.** Each claim makes 3 API calls in sequence (text → vision → text). Parallel processing would be faster but introduces rate-limit complexity and makes debugging harder. For a 44-claim batch, sequential is ~15 minutes and fully predictable.

### Single Vision Call per Claim
All images for a claim are sent in one multimodal call rather than one call per image. This reduces cost and latency but means the model must handle multi-image reasoning in a single context window. Claude 3.5 Sonnet handles this reliably up to 3 images.

### Rule-Based Agents vs Full LLM Pipeline
Agents 2 and 3 are pure Python with no LLM calls. This was deliberate — user history mapping and evidence rule lookup are deterministic operations that don't benefit from LLM reasoning and would introduce unnecessary cost and variability.

### Hard-Coded Safety Rules vs LLM-Enforced
Safety rules (evidence primacy, injection detection, error fallback) are enforced in Python code in Agent 5, not in the LLM prompt. This means they cannot be overridden by a hallucinating or jailbroken model. The LLM contributes reasoning; the code enforces the contract.

### AWS Bedrock vs Self-Hosted Models
Bedrock eliminates infrastructure overhead (no GPU management, no model serving) and provides enterprise-grade security with IAM-based access control. The tradeoff is cost per call and dependency on AWS availability. For a batch verification use case this is the right balance.

---

## Output Schema

14 columns in exact order:

```
user_id, image_paths, user_claim, claim_object,
evidence_standard_met, evidence_standard_met_reason,
risk_flags, issue_type, object_part,
claim_status, claim_status_justification,
supporting_image_ids, valid_image, severity
```

`claim_status`: `supported` | `contradicted` | `not_enough_information`
`severity`: `none` | `low` | `medium` | `high` | `unknown`
`risk_flags`: semicolon-separated from 13 defined flag values

---

## Author

**Harsha Rapuru** · [github.com/harsharapuru2k](https://github.com/harsharapuru2k)
