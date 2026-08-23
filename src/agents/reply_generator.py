"""Inbound Reply Generator & Knowledge Vault Loader."""
import os
from typing import Dict, Any, Optional
from src.agents.classifier import EmailClassifierAgent
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("reply_generator")


class ReplyGeneratorAgent:
    """Agent that synthesizes Obsidian knowledge base context to generate authoritative replies."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = knowledge_dir or settings.KNOWLEDGE_BASE_DIR
        self.classifier = EmailClassifierAgent()
        self._cached_knowledge: Optional[str] = None

    def load_knowledge_base(self) -> str:
        """Load and concatenate all markdown documentation in the knowledge base vault."""
        if self._cached_knowledge is not None:
            return self._cached_knowledge

        combined = []
        if os.path.exists(self.knowledge_dir):
            for filename in sorted(os.listdir(self.knowledge_dir)):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.knowledge_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            combined.append(f"--- Document: {filename} ---\n{f.read()}")
                    except Exception as e:
                        logger.warning(f"Error reading knowledge doc {filename}: {e}")

        self._cached_knowledge = "\n\n".join(combined)
        return self._cached_knowledge

    def process_inbound_message(
        self,
        incoming_text: str,
        sender_name: str,
    ) -> Dict[str, Any]:
        """Triage the inbound message and return structured response."""
        knowledge = self.load_knowledge_base()
        return self.classifier.classify_and_generate(
            incoming_email_text=incoming_text,
            sender_name=sender_name,
            knowledge_context=knowledge,
        )
