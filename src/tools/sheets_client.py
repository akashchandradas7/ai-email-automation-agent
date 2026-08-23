"""Google Sheets CRM Integration Client."""
import json
import os
from typing import Optional, Tuple, List, Dict, Any, Set
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("sheets_client")


class SheetsClient:
    """Client for reading leads and logging interaction statuses to Google Sheets."""

    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(
        self,
        sheet_link: Optional[str] = None,
        creds_json: Optional[str] = None,
        creds_file: Optional[str] = None,
    ):
        self.sheet_link = sheet_link or settings.SHEET_LINK
        self.creds_json = creds_json or settings.GOOGLE_CREDENTIALS_JSON
        self.creds_file = creds_file or settings.CREDENTIALS_FILE
        self._client: Optional[Any] = None
        self._spreadsheet: Optional[Any] = None

    def _authenticate(self) -> Any:
        """Authenticate using JSON string or service account keyfile."""
        if self._client is not None:
            return self._client

        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        if self.creds_json:
            creds_dict = json.loads(self.creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                creds_dict, self.SCOPES
            )
        elif os.path.exists(self.creds_file):
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.creds_file, self.SCOPES
            )
        else:
            raise FileNotFoundError(
                "Google Service Account credentials not provided in env or credentials.json file."
            )

        self._client = gspread.authorize(creds)
        return self._client

    def get_spreadsheet(self) -> Any:
        """Get or open the main Google Spreadsheet."""
        if self._spreadsheet is None:
            client = self._authenticate()
            self._spreadsheet = client.open_by_url(self.sheet_link)
        return self._spreadsheet

    def get_sheets(self) -> Tuple[Any, Optional[Any]]:
        """Retrieve main leads worksheet and inbox worksheet."""
        spreadsheet = self.get_spreadsheet()
        main_sheet = spreadsheet.sheet1
        try:
            inbox_sheet = spreadsheet.worksheet("Inbox")
        except Exception:
            inbox_sheet = None
        return main_sheet, inbox_sheet

    def get_or_create_inbox_sheet(self) -> Any:
        """Retrieve the Inbox worksheet or create it if absent."""
        import gspread
        spreadsheet = self.get_spreadsheet()
        try:
            return spreadsheet.worksheet("Inbox")
        except Exception:
            logger.info("Worksheet 'Inbox' not found; creating new worksheet.")
            sheet = spreadsheet.add_worksheet(title="Inbox", rows="1000", cols="10")
            sheet.append_row([
                "Timestamp",
                "Client Email",
                "Client Name",
                "Client Message",
                "AI Draft",
                "Status",
            ])
            return sheet

    def get_replied_emails(self) -> Set[str]:
        """Fetch all client emails that have engaged or replied in the Inbox sheet."""
        replied = set()
        try:
            _, inbox_sheet = self.get_sheets()
            if inbox_sheet:
                records = inbox_sheet.get_all_records()
                for r in records:
                    ce = str(r.get("Client Email", "")).strip().lower()
                    if ce:
                        replied.add(ce)
        except Exception as e:
            logger.warning(f"Error fetching replied emails from Inbox: {e}")
        return replied

    def log_inbound_interaction(
        self,
        timestamp: str,
        from_email: str,
        from_name: str,
        incoming_text: str,
        reply_body: str,
        status: str,
    ) -> bool:
        """Log an inbound email and the AI's triage status to the Inbox sheet."""
        try:
            inbox = self.get_or_create_inbox_sheet()
            inbox.append_row([
                timestamp,
                from_email,
                from_name,
                incoming_text,
                reply_body,
                status,
            ])
            logger.info(f"Logged interaction for {from_email} with status '{status}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to log inbound interaction to Google Sheet: {e}")
            return False
