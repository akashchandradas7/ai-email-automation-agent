"""Autonomous Outbound Email Campaign Agent."""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.config.settings import settings
from src.tools.brevo_client import BrevoClient
from src.tools.sheets_client import SheetsClient
from src.tools.email_verifier import verify_email_domain
from src.utils.logger import get_logger

logger = get_logger("outbound_agent")


class OutboundCampaignAgent:
    """Orchestrates cold outbound and follow-up email campaigns with rate-limiting and verification."""

    HOOKS: List[str] = [
        "AI Workflow",
        "Automate Busywork",
        "AI Automation",
        "Scale Effortlessly",
    ]

    def __init__(
        self,
        brevo_client: Optional[BrevoClient] = None,
        sheets_client: Optional[SheetsClient] = None,
    ):
        self.brevo = brevo_client or BrevoClient()
        self.sheets = sheets_client or SheetsClient()

    @staticmethod
    def build_initial_email(name: str, business_name: str, industry: str) -> str:
        """Construct the HTML body for the initial psychological outreach email."""
        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; max-width: 600px; line-height: 1.6;">
          <p>Hi {name},</p>
          <p>We have yet to be properly introduced. I was researching {business_name} and noticed your impressive growth in the {industry} sector.</p>
          <p>As founders scale, they often find themselves drowning in operational chaos—too many emails, open loops, and follow-ups. I'm reaching out because GrowthFlow builds custom AI Employees that completely automate this busywork, allowing your team to reclaim their time.</p>
          <p>I know you likely already have an operations process in place, but our fully managed AI workforce integrates seamlessly to handle the repetitive tasks that shouldn't be eating up your day. We handle everything from infrastructure to proactive maintenance.</p>
          <p>Do you have time over the next week or two to learn more? Let me know what works for you.</p>
          <br>
          <p>Best regards,</p>
          <p><strong>{settings.SENDER_NAME}</strong><br>
          <a href="https://growthflow.ltd/" style="color: #1a73e8; text-decoration: none;">growthflow.ltd</a></p>
        </div>
        """

    @staticmethod
    def build_followup_email(name: str, business_name: str, industry: str) -> str:
        """Construct the HTML body for the 48-hour follow-up email."""
        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; max-width: 600px; line-height: 1.6;">
          <p>Hi {name},</p>
          <p>I just wanted to see if you had a chance to read my previous email.</p>
          <p>We are helping companies in the {industry} space save countless hours by deploying AI agents that work 24/7 without limits. I'd love to share a quick 3-step strategy on how this could work specifically for {business_name}.</p>
          <p>Do you have time over the next week or two for a brief chat? Let me know what works for you.</p>
          <br>
          <p>Best regards,</p>
          <p><strong>{settings.SENDER_NAME}</strong><br>
          <a href="https://growthflow.ltd/" style="color: #1a73e8; text-decoration: none;">growthflow.ltd</a></p>
        </div>
        """

    def run_campaign(self, max_daily: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute an outbound campaign batch across the Google Sheets CRM.

        Returns:
            Summary dictionary with sent count and follow-up metrics.
        """
        try:
            main_sheet, _ = self.sheets.get_sheets()
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets CRM: {e}")
            return {"status": "error", "message": str(e)}

        headers = main_sheet.row_values(1)
        if "Status" not in headers:
            main_sheet.update_cell(1, len(headers) + 1, "Status")
            headers.append("Status")

        status_col_idx = headers.index("Status") + 1
        records = main_sheet.get_all_records()
        replied_emails = self.sheets.get_replied_emails()

        total_ever_sent = sum(
            1 for row in records if str(row.get("Status", "")).startswith("Sent")
        )
        daily_limit = max_daily if max_daily is not None else (20 if total_ever_sent < 200 else 50)

        initial_sent = 0
        followups_sent = 0
        now = datetime.now()

        for index, row in enumerate(records):
            row_num = index + 2
            email = str(row.get("Email", "")).strip()
            if not email:
                continue

            name = str(row.get("Contact Name", "")).strip() or "there"
            business_name = str(row.get("Business Name", "")).strip() or "your company"
            industry = str(row.get("Industry", "")).strip() or "your industry"
            status = str(row.get("Status", "")).strip()

            # 1. Skip if the prospect already engaged
            if email.lower() in replied_emails:
                if "Replied" not in status:
                    main_sheet.update_cell(row_num, status_col_idx, "Replied")
                continue

            # 2. Initial cold outreach
            if status == "" or status == "None":
                if initial_sent >= daily_limit:
                    continue

                # Pre-flight DNS validation
                is_valid, reason = verify_email_domain(email)
                if not is_valid:
                    main_sheet.update_cell(
                        row_num, status_col_idx, f"Invalid Email ({reason})"
                    )
                    continue

                hook = random.choice(self.HOOKS)
                subject = f"{hook} + {industry} + {business_name}"
                html = self.build_initial_email(name, business_name, industry)

                if self.brevo.send_email(to_email=email, subject=subject, html_content=html, to_name=name):
                    main_sheet.update_cell(
                        row_num, status_col_idx, f"Sent - {now.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    initial_sent += 1
                else:
                    main_sheet.update_cell(row_num, status_col_idx, "Failed")

            # 3. 48-hour follow-up dispatch
            elif status.startswith("Sent - "):
                timestamp_str = status.replace("Sent - ", "").strip()
                try:
                    sent_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if now - sent_time > timedelta(hours=48):
                        hook = random.choice(self.HOOKS)
                        subject = f"Re: {hook} + {industry} + {business_name}"
                        html = self.build_followup_email(name, business_name, industry)

                        if self.brevo.send_email(to_email=email, subject=subject, html_content=html, to_name=name):
                            main_sheet.update_cell(
                                row_num,
                                status_col_idx,
                                f"Followup Sent - {now.strftime('%Y-%m-%d %H:%M:%S')}",
                            )
                            followups_sent += 1
                except Exception as ex:
                    logger.warning(f"Error parsing timestamp for {email}: {ex}")

        return {
            "status": "success",
            "initial_sent": initial_sent,
            "followups_sent": followups_sent,
            "total_ever_sent": total_ever_sent + initial_sent,
        }
