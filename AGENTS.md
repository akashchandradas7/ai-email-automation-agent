# AGENTS.md — Development Guidelines for AI Coding Agents

> **Audience:** Automated agents, LLM harnesses, and developers extending this repository.

---

## 1. Project Overview

The **AI Email Automation Agent** is an autonomous microservice built for:
- Outbound cold engagement and 48-hour follow-up automation.
- Pre-flight DNS MX verification to protect domain sender reputation.
- Inbound Brevo webhook triage with asynchronous background threading.
- DeepSeek/OpenAI LLM intent classification and RAG-grounded response generation.
- Real-time bi-directional synchronization with Google Sheets CRM.

---

## 2. Command Reference

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\Activate.ps1 on Windows
pip install -e ".[dev]"
cp .env.example .env
```

### Running the Microservice
```bash
python -m src.main
# Or via Gunicorn
gunicorn --bind 0.0.0.0:5000 src.main:app
```

### Running Tests
```bash
pytest tests/ -v --tb=short
pytest tests/ --cov=src --cov-report=term-missing
```

### Linting & Formatting
```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

---

## 3. Architecture & Conventions

### Directory Layout
- `src/agents/`: LLM prompt orchestration, classification schemas, and outbound logic.
- `src/tools/`: Integration wrappers (`brevo_client.py`, `sheets_client.py`, `email_verifier.py`).
- `src/knowledge_base/`: Markdown knowledge vault injected into LLM context prompts.
- `src/config/`: Typed settings management via `src/config/settings.py`.
- `src/utils/`: Standardized logging via `src/utils/logger.py`.
- `src/main.py`: Flask service exposing `/`, `/brevo-webhook`, and `/trigger-emails`.

### Critical Coding Rules
1. **Asynchronous Webhook Handling:** Never execute blocking network calls (LLM calls, Google Sheets API updates) synchronously inside the `/brevo-webhook` request thread. Always delegate heavy processing to background daemon threads (`threading.Thread`) or task queues to return `200 OK` in `< 100ms`.
2. **Robust JSON Parsing:** Always use defensive regex matching (`re.search(r'\{.*\}', content, re.DOTALL)`) when parsing structured JSON from LLM outputs to prevent markdown delimiter crashes.
3. **Pre-Flight DNS Checks:** Always invoke `verify_email_domain()` before initiating cold outbound emails.

---

## 4. Security & Data Boundaries

> [!CAUTION]
> **Strict Security Guardrails:**
> - **NEVER** commit real API keys, bearer tokens, or Google service account credentials to Git.
> - **NEVER** include real client email addresses, names, or identifiable corporate data in test fixtures or logs.
> - All new environment variables must be declared in `.env.example` with generic placeholder values.
