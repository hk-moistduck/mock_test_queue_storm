# QueueStorm Warmup — CRM Ticket Classifier

A small, rule-based web service that classifies inbound CRM support tickets for a digital finance company. Built for the **SUST CSE Carnival 2026 Codex Community Hackathon** (QueueStorm Warmup task).

Two endpoints. One pipeline. Deterministic. Deploy-ready. No GPU. No LLM. No secrets in the repo.

---

## Overview

| | |
|---|---|
| **Language** | Python 3.12 |
| **Framework** | FastAPI 0.115 |
| **Validation** | Pydantic v2 |
| **Classifier** | Rule-based (regex + keyword sets) |
| **Safety** | Post-processing deny-list filter |
| **Logging** | loguru (JSON to stdout) |
| **Tests** | pytest + httpx.AsyncClient |
| **Deploy** | Docker (preferred) or Procfile (Heroku/Render) |

---

## Architecture

The service is a thin HTTP shell around a **single deterministic pipeline**. Every ticket flows through these stages in order:

```
HTTP request
   │
   ▼
Pydantic schema validation     ← unknown fields rejected (extra="forbid")
   │
   ▼
Normalize message              ← NFKC + lowercase
   │
   ▼
Classify case_type             ← ordered rule match (phishing > wrong_xfer > refund > payment > other)
   │
   ▼
Assign severity                ← base per case_type + critical/escalate override
   │
   ▼
Route to department            ← pure lookup table
   │
   ▼
Build agent_summary            ← template strings (no LLM)
   │
   ▼
Sanitize summary               ← replace risky phrases, redact card numbers
   │
   ▼
Compute confidence             ← rule-weighted signal count + severity bonus
   │
   ▼
Flag human_review_required     ← phishing OR critical
   │
   ▼
HTTP response
```

Why this order? Safety comes *after* summarization so classification sees the raw message and can detect phishing; the *output* is what we keep clean.

---

## API

### `GET /health`

Service health check. Returns in single-digit milliseconds. No external calls.

**Response (200):**

```json
{
  "status": "ok",
  "service": "queue-storm-warmup",
  "version": "0.1.0",
  "uptime_seconds": 12.34,
  "timestamp": "2026-06-25T12:00:00.000000+00:00"
}
```

**Latency SLA:** < 10 seconds.

---

### `POST /sort-ticket`

Classify a single CRM support ticket.

**Request body:**

```json
{
  "ticket_id": "T-1001",
  "channel": "email",
  "locale": "en-US",
  "message": "I got a phishing email asking me to verify my account with my OTP."
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `ticket_id` | string | yes | Unique ticket ID, max 128 chars |
| `channel` | string | no | Originating channel, max 64 chars |
| `locale` | string | no | BCP-47 locale tag (e.g. `en-US`, `bn-BD`) |
| `message` | string | yes | Free-text ticket body, max 5000 chars |

**Response (200):**

```json
{
  "ticket_id": "T-1001",
  "case_type": "phishing_or_social_engineering",
  "severity": "critical",
  "department": "fraud_risk",
  "agent_summary": "Customer reports a potential phishing or social-engineering attempt via email. Recommend escalating to fraud_risk and advising the customer not to click links, not to share codes, and to verify via official channels only. Severity: critical — prioritize immediately.",
  "human_review_required": true,
  "confidence": 0.95
}
```

**Latency SLA:** < 30 seconds.

**Validation:** Unknown fields are rejected with HTTP 422.

---

## Classification Rules

Five `case_type` values, evaluated in order (first match wins):

| Order | `case_type` | Routed to | Base severity |
|---|---|---|---|
| 1 | `phishing_or_social_engineering` | `fraud_risk` | high |
| 2 | `wrong_transfer` | `dispute_resolution` | high |
| 3 | `refund_request` | `dispute_resolution` | medium |
| 4 | `payment_failed` | `payments_ops` | medium |
| 5 | `other` (default) | `customer_support` | low |

Each `case_type` matches on (a) a list of compiled regex patterns (strong signal) and (b) a frozenset of keywords (weaker signal). See `src/app/rules/patterns.py` and `src/app/rules/keywords.py` for the full rule data.

### Severity Algorithm

```
severity = base(case_type)
if any CRITICAL_KEYWORD in message:    severity = critical
elif any ESCALATE_KEYWORD in message:  severity = bump_one_tier(severity)
severity = min(severity, critical)      # never downgrade
```

### `human_review_required`

`true` if `case_type == phishing_or_social_engineering` OR `severity == critical`.

---

## Safety

The agent_summary is post-processed by a deterministic deny-list filter (`src/app/safety.py`) that:

1. **Replaces risky phrases** with safe alternatives:
   - "share/provide/enter your PIN/OTP/password" → "do not share your credentials"
   - "share your card number" → "do not share your card details"
2. **Redacts card-number-like digit runs:**
   - Bare 13–19 digit runs → `[REDACTED-CARD]`
   - Grouped 4-4-4-... style (with spaces/dashes) → `[REDACTED-CARD]`
3. **Hard-guard fallback:** if any deny pattern still matches after replacements, the entire summary is replaced with:
   > "Issue acknowledged and queued for review. No sensitive credentials are required to proceed."

### Example

Input message:
```
"Phishing email asked for my PIN and showed a link bit.ly/abc123. 
Also they had my card number 4111 1111 1111 1111."
```

Output `agent_summary`:
```
"Customer reports a potential phishing or social-engineering attempt. 
Recommend escalating to fraud_risk and advising the customer not to click links, 
not to share codes, and to verify via official channels only. 
Severity: critical — prioritize immediately."
```

The summary **never** asks for credentials. Card numbers **never** appear.

---

## Local Development

### Prerequisites

- **Python 3.12** (required)
- pip

### Setup

```bash
# 1. Clone (or navigate to) the project
cd queue-storm-warmup

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 4. Install runtime + dev dependencies
pip install -r requirements-dev.txt

# 5. Run the tests
pytest -q

# 6. Start the dev server
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000/docs> for the auto-generated OpenAPI/Swagger UI.

### Manual smoke

```bash
# Health
curl http://localhost:8000/health

# Phishing example
curl -X POST http://localhost:8000/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-1","message":"I got a phishing email asking me to verify my account with my OTP"}'

# Payment failed example
curl -X POST http://localhost:8000/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-2","message":"Payment failed at checkout, card was declined"}'

# Wrong transfer example
curl -X POST http://localhost:8000/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-3","message":"I accidentally transferred money to the wrong account"}'
```

---

## Configuration

All configuration is via environment variables. No secrets in the repo. See `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | loguru level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `APP_ENV` | `development` | Environment label surfaced in startup logs |
| `SUMMARY_MAX_CHARS` | `280` | Hard cap on agent_summary length |

To override locally, copy `.env.example` to `.env` (gitignored) and edit.

---

## Docker

```bash
# Build
docker build -t queue-storm-warmup .

# Run
docker run --rm -p 8000:8000 queue-storm-warmup

# Health check (from another terminal)
curl http://localhost:8000/health
```

The image is based on `python:3.12-slim` (~30 MB installed deps), no GPU, no native build tools.

---

## Cloud Deployment

The service is designed to deploy as-is to any platform that runs a Docker container or a `Procfile`.

### Railway / Render / Fly.io

- **Build command:** `pip install -r requirements.txt` (or use the included Dockerfile)
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check URL:** `GET /health`
- **Environment:** set `LOG_LEVEL=INFO`, `APP_ENV=production` (optional)

### Heroku-style (Procfile)

The included `Procfile` already handles `$PORT`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Cloud Run / App Runner

- Use the Dockerfile. Cloud Run sets `PORT=8080`; override the CMD or pass `--port`.

---

## Testing

```bash
pytest -q                  # all tests, quiet
pytest tests/test_safety.py -v   # one file, verbose
pytest -k "phishing" -v     # by keyword
```

Test files:

| File | What it covers |
|---|---|
| `test_health.py` | `/health` shape + <10s SLA |
| `test_sort_ticket_schema.py` | Request validation, response contract |
| `test_classifier.py` | One example per `case_type` |
| `test_severity.py` | Severity matrix and critical overrides |
| `test_safety.py` | Deny-list filter unit + end-to-end |
| `test_summarizer.py` | Summary length, content, formatting |
| `test_confidence.py` | Score bounds, floors, severity bonus |
| `test_routing.py` | `case_type` → `department` mapping, `human_review_required` flag |

Coverage is **deliberately weighted toward the safety filter** — that is the single highest-stakes invariant in the system.

---

## Project Layout

```
queue-storm-warmup/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── .dockerignore
├── Procfile
├── .env.example
├── .gitignore
├── README.md
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI factory + lifespan
│       ├── config.py               # pydantic-settings
│       ├── logging_config.py       # loguru JSON setup
│       ├── schemas.py              # Pydantic models + enums
│       ├── classifier.py           # process_ticket() orchestrator
│       ├── severity.py             # assign_severity()
│       ├── summarizer.py           # build_summary() (template-driven)
│       ├── safety.py               # sanitize_summary() (deny-list)
│       ├── confidence.py           # compute_confidence() (rule-weighted)
│       ├── rules/
│       │   ├── keywords.py         # frozensets: PHISHING/REFUND/...
│       │   └── patterns.py         # compiled regexes + safety deny-list
│       └── api/
│           ├── health.py           # GET /health
│           └── sort_ticket.py      # POST /sort-ticket
└── tests/
    ├── conftest.py
    ├── test_health.py
    ├── test_sort_ticket_schema.py
    ├── test_classifier.py
    ├── test_severity.py
    ├── test_safety.py
    ├── test_summarizer.py
    ├── test_confidence.py
    └── test_routing.py
```

---

## Limitations

- **Rule-based, English-first.** Bengali currency symbols (৳) and numerals are detected, but no formal i18n beyond that. Novel phrasings may fall through to `case_type=other`.
- **No ML, no embeddings.** This is intentional: deterministic, auditable, no GPU, fast. Easy to extend with more rules.
- **No persistent state.** Each request is independent. There is no database.
- **No auth.** The hackathon scope assumes the service is behind an API gateway. Add auth at the gateway, not here.

---

## Extending the Classifier

Adding a new rule is a **data change**, not a code change:

1. Add keywords to the appropriate frozenset in `src/app/rules/keywords.py`.
2. Add patterns to the appropriate tuple in `src/app/rules/patterns.py`.
3. If a new `case_type` is needed:
   - Add the enum to `src/app/schemas.py`.
   - Add base severity + routing in `src/app/severity.py` and `src/app/classifier.py`.
   - Add a summary template in `src/app/summarizer.py`.
4. Add tests in `tests/test_classifier.py`.

---

## License

MIT — see project metadata in `pyproject.toml`.

---

## Acknowledgments

Built for the **SUST CSE Carnival 2026 Codex Community Hackathon** (QueueStorm Warmup task).