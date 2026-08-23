"""Inbound Email Intent Classifier & Spam Triage Agent."""
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("email_classifier")


class EmailClassifierAgent:
    """Agent responsible for classifying inbound email messages and filtering noise."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL
        self.model = model or settings.LLM_MODEL
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "sk-dummy-placeholder",
            )
        return self._client

    def classify_and_generate(
        self,
        incoming_email_text: str,
        sender_name: str,
        knowledge_context: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluate an inbound email, filter automated/spam messages, and generate a draft if genuine.

        Returns:
            dict containing:
                - is_human_business_inquiry: bool
                - reason: str
                - reply_body: str
        """
        system_prompt = f"""You are an intelligent and professional AI email triage and response agent for {settings.SENDER_NAME}.

TASK 1: CLASSIFICATION
Analyze the incoming email carefully. We receive automated messages (social media notifications, newsletters, OTP/verification codes, phishing, cold sales spam). You MUST filter these out.
You must ONLY mark 'is_human_business_inquiry: true' if the email is from a legitimate human inquiring about our services, responding to our outreach, asking business questions, or scheduling a meeting.

TASK 2: CONTEXTUAL RESPONSE DRAFTING
If 'is_human_business_inquiry' is true, write a polite, high-status, consultative, and persuasive reply based strictly on our knowledge base.
- Do NOT include subject lines or markdown email headers.
- Speak in professional American English.
- End with a professional sign-off from {settings.SENDER_NAME}.
- If false, leave 'reply_body' as an empty string.

KNOWLEDGE BASE & GUIDELINES:
{knowledge_context}

OUTPUT FORMAT:
Output your answer STRICTLY as a valid JSON object:
{{
  "is_human_business_inquiry": true/false,
  "reason": "Brief explanation of your classification",
  "reply_body": "Generated email body or empty string"
}}
"""

        user_prompt = f"Sender Name: {sender_name}\n\nEmail Content:\n{incoming_email_text}\n\nProvide the classification JSON:"

        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            raw_content = completion.choices[0].message.content or "{}"
            return self._parse_json_response(raw_content)
        except Exception as e:
            logger.error(f"Error during LLM email classification: {e}")
            return {
                "is_human_business_inquiry": False,
                "reason": f"AI Parsing/Generation Error: {str(e)}",
                "reply_body": "",
            }

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        """Robustly parse JSON response from LLM."""
        try:
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)

            parsed = json.loads(cleaned)
            return {
                "is_human_business_inquiry": bool(parsed.get("is_human_business_inquiry", False)),
                "reason": str(parsed.get("reason", "No reason provided")),
                "reply_body": str(parsed.get("reply_body", "")),
            }
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON: {e} | Raw: {content}")
            return {
                "is_human_business_inquiry": False,
                "reason": "Failed to parse JSON response",
                "reply_body": "",
            }
