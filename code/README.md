# Multi-Modal Evidence Review — Solution

5-agent pipeline using Gemini Vision + text models to verify damage claims from images, conversations, and user history.

## Setup

```bash
cd hackerrank-orchestrate-june26

# Install dependencies
pip install -r code/requirements.txt

# Set your Gemini API key
export GOOGLE_API_KEY=your_key_here
# or copy .env.example → .env and fill in the key
```

## Run on Test Set

```bash
python code/main.py
```

Writes `output.csv` to the repo root. All paths are resolved automatically.

Options:
```bash
python code/main.py --verbose          # Print per-agent details
python code/main.py --output my.csv   # Custom output path
```

## Evaluate on Sample Set

```bash
# Compare both strategies (recommended before submission)
python code/evaluation/main.py --strategy both

# Single strategy
python code/evaluation/main.py --strategy B
```

Writes `code/evaluation/evaluation_report.md` with metrics, cost, and latency analysis.

## Architecture

```
Orchestrator (main.py)
    │
    ├── Agent 1: ClaimExtractor       — parses conversation → structured claim (1 text call)
    ├── Agent 2: RiskAssessor         — user history → risk flags (no LLM)
    ├── Agent 3: EvidenceChecker      — rule lookup → evidence checklist (no LLM)
    ├── Agent 4: EvidenceAnalyst      — Gemini Vision → image verdict (1 vision call)
    └── Agent 5: DecisionSynthesizer  — combine all → final row (1 text call)
```

## Model Strategy

| Agent | Model | Why |
|---|---|---|
| Agent 1 (text) | `gemini-2.5-flash` | Fast text parsing |
| Agent 4 (vision) | `gemini-2.5-pro` | Best multimodal reasoning |
| Agent 5 (text) | `gemini-2.5-flash` | Structured output synthesis |

Override via env vars: `GEMINI_VISION_MODEL`, `GEMINI_TEXT_MODEL`

## Safety Rules

- Images are the **primary source of truth** — history flags add context but cannot override visual evidence
- `evidence_standard_met=false` → always `claim_status=not_enough_information`
- Prompt injection detected in conversation or image text → always adds `text_instruction_present` + `manual_review_required`
- All errors fall back to `not_enough_information` — never auto-approve on failure

## Files

```
code/
├── main.py                    # Orchestrator + CLI
├── requirements.txt
├── README.md                  # This file
├── agents/
│   ├── claim_extractor.py     # Agent 1
│   ├── risk_assessor.py       # Agent 2
│   ├── evidence_checker.py    # Agent 3
│   ├── evidence_analyst.py    # Agent 4
│   └── decision_synthesizer.py  # Agent 5
├── utils/
│   ├── schema.py              # Enums, allowed values, validators
│   ├── gemini_client.py       # API wrapper with retry
│   ├── csv_loader.py          # CSV I/O
│   ├── image_utils.py         # Image loading
│   └── logger.py              # AGENTS.md log writer
└── evaluation/
    ├── main.py                # Evaluation entry point
    ├── metrics.py             # Accuracy + F1 metrics
    └── evaluation_report.md   # Written after evaluation runs
```
