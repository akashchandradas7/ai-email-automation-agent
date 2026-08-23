import os
from dataclasses import dataclass
from typing import Optional


def load_env(filepath: str = ".env") -> None:
    """Load environment variables from a local file if present."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip('"').strip("'")
                    except ValueError:
                        pass


load_env()


@dataclass(frozen=True)
class Settings:
    # Brevo API
    BREVO_API_KEY: str = os.environ.get("BREVO_API_KEY", "")
    SENDER_EMAIL: str = os.environ.get("SENDER_EMAIL", "info@example.com")
    SENDER_NAME: str = os.environ.get("SENDER_NAME", "GrowthFlow Team")
    REPLY_TO_EMAIL: str = os.environ.get("REPLY_TO_EMAIL", "hello@support.example.com")

    # LLM (OpenAI-compatible / DeepSeek / Nvidia NIM)
    LLM_API_KEY: str = os.environ.get("LLM_API_KEY", os.environ.get("NVIDIA_API_KEY", os.environ.get("OPENAI_API_KEY", "")))
    LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "deepseek-ai/deepseek-v4-pro")

    # Google Sheets CRM
    SHEET_LINK: str = os.environ.get(
        "SHEET_LINK",
        "https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
    )
    GOOGLE_CREDENTIALS_JSON: Optional[str] = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    CREDENTIALS_FILE: str = os.environ.get("CREDENTIALS_FILE", "credentials.json")

    # Application
    PORT: int = int(os.environ.get("PORT", "5000"))
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    KNOWLEDGE_BASE_DIR: str = os.environ.get(
        "KNOWLEDGE_BASE_DIR",
        os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    )


settings = Settings()
