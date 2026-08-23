# System Architecture — AI Email Automation Agent

## 1. Executive Summary

The **AI Email Automation Agent** is an enterprise-grade autonomous system engineered for cold outbound engagement, real-time inbound email triage, and dynamic CRM synchronization.

Unlike basic mail merge or rigid rule-based auto-responders, this agent operates as an intelligent microservice that combines:
1. **Pre-Flight DNS MX Verification** to protect domain reputation and prevent high bounce rates.
2. **Context-Aware Dynamic Outbound Outreach** utilizing psychological hooks and automatic 48-hour follow-up loops.
3. **Asynchronous Non-Blocking Webhook Processing** to immediately acknowledge third-party webhook relays (Brevo) in `< 100ms`.
4. **LLM-Powered Intent Classification & Spam Shield** (DeepSeek / OpenAI) that filters out automated bots, OTPs, and social media notifications.
5. **RAG-Grounded Knowledge Vault** ensuring that every response is strictly aligned with company value propositions and consultative sales rules.

---

## 2. High-Level Architecture Diagram

```mermaid
graph TD
    subgraph "External Ecosystem"
        LeadDB[(Google Sheets CRM)]
        BrevoSMTP[Brevo Transactional API]
        InboundDNS[DNS Server / MX Records]
        Prospect[Target Prospect / Client]
    end

    subgraph "AI Email Automation Agent"
        subgraph "Outbound Engine"
            CampaignRunner[Outbound Campaign Agent]
            DNSVerifier[DNS MX Pre-Flight Verifier]
            HookGenerator[Psychological Hook Builder]
        end

        subgraph "Inbound Microservice (Flask/Gunicorn)"
            WebhookReceiver[POST /brevo-webhook]
            ThreadWorker[Async Background Worker Thread]
            IntentClassifier[LLM Intent & Spam Classifier]
            KnowledgeVault[(Obsidian RAG Vault)]
            ResponseGenerator[Contextual Response Drafter]
        end
    end

    %% Outbound Flow
    LeadDB -->|1. Fetch Prospect Records| CampaignRunner
    CampaignRunner -->|2. Check MX Records| DNSVerifier
    DNSVerifier -->|Query MX| InboundDNS
    CampaignRunner -->|3. Construct Email & Hook| HookGenerator
    HookGenerator -->|4. Dispatch Message| BrevoSMTP
    BrevoSMTP -->|5. Deliver to Inbox| Prospect
    CampaignRunner -->|6. Log Status: Sent / Invalid| LeadDB

    %% Inbound Flow
    Prospect -->|7. Sends Reply / Inquiry| BrevoSMTP
    BrevoSMTP -->|8. Webhook Notification| WebhookReceiver
    WebhookReceiver -->|9. Acknowledge 200 OK (<100ms)| BrevoSMTP
    WebhookReceiver -->|10. Spawn Daemon Thread| ThreadWorker
    ThreadWorker -->|11. Extract Context & Rules| KnowledgeVault
    ThreadWorker -->|12. Intent Triage & Draft| IntentClassifier
    IntentClassifier -->|13. Output JSON Decision| ResponseGenerator
    ResponseGenerator -->|14. Auto-Reply via SMTP| BrevoSMTP
    ResponseGenerator -->|15. Sync State to CRM| LeadDB
```

---

## 3. Core Subsystems

### 3.1 Pre-Flight DNS Verification Engine (`src/tools/email_verifier.py`)
- **Problem Solved:** High bounce rates (>5%) quickly ruin domain sender reputation and lead to blacklisting across major mailbox providers (Google Workspace, Microsoft 365).
- **Mechanism:** Before any initial outreach is dispatched, the agent queries the recipient domain's DNS for active `MX` (Mail Exchange) records.
- **Fail-Safe:** Invalid domains or domains without operational mail servers are flagged in the CRM as `Invalid Email (No MX)` and immediately skipped.

### 3.2 Asynchronous Inbound Webhook Architecture (`src/main.py`)
- **Problem Solved:** Third-party webhook providers (such as Brevo) enforce a strict 5–10 second response timeout. Deep reasoning models (e.g., DeepSeek) can take 10–15 seconds to synthesize context and output structured JSON, causing webhook timeouts and duplicate retry floods.
- **Mechanism:** The `/brevo-webhook` endpoint parses the incoming payload, spawns an isolated background daemon thread (`threading.Thread`), and returns an HTTP `200 OK` response to Brevo within `~50ms`.
- **Worker Execution:** The daemon thread executes the LLM classification, generates the response, dispatches the email via Brevo, and logs the result to Google Sheets.

### 3.3 Two-Stage LLM Triage & Response Guardrails (`src/agents/classifier.py`)
- **Spam & Notification Filter:** Distinguishes between automated emails (Facebook notifications, verification codes, system auto-responders) and real human business inquiries.
- **RAG-Grounded Knowledge Base:** Injects company value propositions, objection handling frameworks, and consultative closing rules from the local markdown vault.
- **Structured JSON Output:** Enforces strict JSON schema output (`is_human_business_inquiry`, `reason`, `reply_body`) with robust regex fallback parsing.

### 3.4 Outbound Campaign & Follow-Up Lifecycle (`src/agents/outbound_agent.py`)
- **Dynamic Personalization:** Generates dynamic subject lines and opening hooks: `[Hook] + [Industry] + [Business Name]`.
- **48-Hour Follow-Up:** Detects prospects who were emailed > 48 hours ago and have not replied, automatically dispatching a tailored value-oriented follow-up.
- **Deduplication:** Cross-references the `Inbox` sheet to permanently suppress outbound emails to leads who have already replied.
