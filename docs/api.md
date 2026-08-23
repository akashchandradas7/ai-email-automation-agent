# API & Webhook Specifications

## Base URL

```text
http://localhost:5000  (Development)
https://your-domain.onrender.com (Production)
```

---

## Endpoints

### 1. Service Health Check

`GET /`

Returns the health status and current version of the microservice.

**Response:**
```json
{
  "agent": "AI Email Automation Agent",
  "status": "healthy",
  "timestamp": "2026-08-23T18:00:00.000000Z",
  "version": "1.0.0"
}
```

---

### 2. Inbound Brevo Webhook

`POST /brevo-webhook`

Receives inbound email notifications from Brevo Inbound Parsing. Acknowledges receipt immediately (`200 OK`) and processes the message asynchronously in a background worker thread.

**Request Headers:**
- `Content-Type: application/json`

**Sample Payload:**
```json
{
  "items": [
    {
      "From": {
        "Name": "Sarah Jenkins",
        "Address": "sarah.jenkins@acmecorp.com"
      },
      "To": [
        {
          "Name": "Support",
          "Address": "hello@support.yourdomain.com"
        }
      ],
      "Subject": "Question about AI Employee automation",
      "TextBody": "Hi, I saw your email regarding workflow automation. How does your AI integrate with our existing CRM?",
      "RawHtmlBody": "<p>Hi, I saw your email regarding workflow automation. How does your AI integrate with our existing CRM?</p>"
    }
  ]
}
```

**Response (`200 OK` returned immediately in < 100ms):**
```json
{
  "message": "Webhook payload received and queued for asynchronous processing",
  "status": "success"
}
```

---

### 3. Trigger Outbound Campaign Batch

`GET` or `POST /trigger-emails`

Triggers an execution of the outbound outreach campaign batch against the connected Google Sheets CRM.

**Response (`200 OK`):**
```json
{
  "followups_sent": 3,
  "initial_sent": 20,
  "status": "success",
  "total_ever_sent": 140
}
```
