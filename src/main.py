"""AI Email Automation Agent — Webhook & Microservice Entrypoint."""
import json
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, request, jsonify

from src.config.settings import settings
from src.utils.logger import get_logger
from src.tools.brevo_client import BrevoClient
from src.tools.sheets_client import SheetsClient
from src.agents.reply_generator import ReplyGeneratorAgent
from src.agents.outbound_agent import OutboundCampaignAgent

logger = get_logger("main_service")
app = Flask(__name__)

brevo_client = BrevoClient()
sheets_client = SheetsClient()
reply_agent = ReplyGeneratorAgent()
outbound_agent = OutboundCampaignAgent(brevo_client=brevo_client, sheets_client=sheets_client)


def process_inbound_webhook_payload(data: Dict[str, Any]) -> None:
    """Background worker to process incoming webhook items without blocking HTTP responses."""
    try:
        raw_json_str = json.dumps(data)
        items: List[Dict[str, Any]] = data.get("items", []) if "items" in data else [data]

        for item in items:
            # Extract sender address
            from_email = ""
            if isinstance(item.get("From"), dict):
                from_email = item.get("From", {}).get("Address", "")
            elif isinstance(item.get("From"), str):
                from_email = item.get("From", "")
            elif "from" in item:
                from_email = str(item.get("from", ""))

            # Extract sender name
            from_name = "Customer"
            if isinstance(item.get("From"), dict):
                from_name = item.get("From", {}).get("Name", "Customer")

            subject = item.get("Subject", "") or item.get("subject", "Inquiry")
            text_body = (
                item.get("TextBody", "")
                or item.get("RawHtmlBody", "")
                or item.get("text", "")
                or raw_json_str
            )

            # Prevent loops on self-sent emails or empty senders
            if not from_email or settings.SENDER_EMAIL.lower() in from_email.lower():
                logger.info(f"Skipping self-sent or invalid sender: {from_email}")
                continue

            logger.info(f"Processing inbound message from {from_email} (Subject: '{subject}')")

            # Execute LLM classification & RAG response generation
            ai_result = reply_agent.process_inbound_message(
                incoming_text=text_body,
                sender_name=from_name,
            )

            is_valid = ai_result.get("is_human_business_inquiry", False)
            reason = ai_result.get("reason", "No reason provided")
            reply_body = ai_result.get("reply_body", "")

            status = "Filtered"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if is_valid and reply_body:
                # Dispatch response via Brevo
                formatted_html = f"<html><body><p>{reply_body.replace(chr(10), '<br>')}</p></body></html>"
                sent_ok = brevo_client.send_email(
                    to_email=from_email,
                    subject=f"Re: {subject}",
                    html_content=formatted_html,
                    to_name=from_name,
                )
                status = "Auto-Replied" if sent_ok else "Send Failed"
            else:
                status = f"Filtered: {reason}"

            # Log to Google Sheets Inbox CRM
            sheets_client.log_inbound_interaction(
                timestamp=timestamp,
                from_email=from_email,
                from_name=from_name,
                incoming_text=text_body,
                reply_body=reply_body,
                status=status,
            )

    except Exception as e:
        logger.exception(f"Unhandled error in webhook background thread: {e}")


@app.route("/", methods=["GET"])
def health_check():
    """Service status and health check."""
    return jsonify({
        "status": "healthy",
        "agent": "AI Email Automation Agent",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), 200


@app.route("/brevo-webhook", methods=["POST"])
def brevo_webhook():
    """Inbound webhook receiver. Returns 200 OK immediately and spawns background worker."""
    data = request.get_json(force=True, silent=True) or {}
    logger.info("Received incoming webhook notification.")

    worker_thread = threading.Thread(
        target=process_inbound_webhook_payload,
        args=(data,),
        daemon=True,
    )
    worker_thread.start()

    return jsonify({
        "status": "success",
        "message": "Webhook payload received and queued for asynchronous processing",
    }), 200


@app.route("/trigger-emails", methods=["GET", "POST"])
def trigger_emails():
    """Trigger an outbound campaign batch across the connected Google Sheets CRM."""
    try:
        result = outbound_agent.run_campaign()
        return jsonify(result), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error executing outbound campaign: {e}\n{tb}")
        return jsonify({"status": "error", "message": str(e), "traceback": tb}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT)
