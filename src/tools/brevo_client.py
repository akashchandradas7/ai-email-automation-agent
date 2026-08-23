"""Brevo (Sendinblue) Transactional Email API Client."""
from typing import Optional, Dict, Any
import requests
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("brevo_client")


class BrevoClient:
    """Client for dispatching transactional emails through Brevo v3 API."""

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(
        self,
        api_key: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_email: Optional[str] = None,
        reply_to_email: Optional[str] = None,
    ):
        self.api_key = api_key or settings.BREVO_API_KEY
        self.sender_name = sender_name or settings.SENDER_NAME
        self.sender_email = sender_email or settings.SENDER_EMAIL
        self.reply_to_email = reply_to_email or settings.REPLY_TO_EMAIL

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None,
    ) -> bool:
        """
        Send a transactional email using the Brevo SMTP API.

        Args:
            to_email: Target recipient email.
            subject: Email subject line.
            html_content: HTML-formatted email body.
            to_name: Target recipient display name.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.api_key:
            logger.error("BREVO_API_KEY is not configured.")
            return False

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json",
        }

        recipient: Dict[str, Any] = {"email": to_email}
        if to_name:
            recipient["name"] = to_name

        payload = {
            "sender": {"name": self.sender_name, "email": self.sender_email},
            "to": [recipient],
            "replyTo": {"email": self.reply_to_email, "name": self.sender_name},
            "subject": subject,
            "htmlContent": html_content,
        }

        try:
            response = requests.post(
                self.API_URL, json=payload, headers=headers, timeout=10.0
            )
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email successfully dispatched to {to_email} (Subject: '{subject}').")
                return True
            else:
                logger.error(
                    f"Failed to send email to {to_email}. HTTP {response.status_code}: {response.text}"
                )
                return False
        except Exception as e:
            logger.exception(f"Exception during Brevo email dispatch to {to_email}: {str(e)}")
            return False
