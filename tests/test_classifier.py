"""Unit tests for LLM intent classification parsing."""
import unittest
from unittest.mock import MagicMock, patch
from src.agents.classifier import EmailClassifierAgent


class TestEmailClassifier(unittest.TestCase):
    def test_parse_json_response_clean(self):
        """Verify clean JSON parsing."""
        raw = '{"is_human_business_inquiry": true, "reason": "Prospect requested pricing", "reply_body": "Hello, thank you..."}'
        res = EmailClassifierAgent._parse_json_response(raw)
        self.assertTrue(res["is_human_business_inquiry"])
        self.assertEqual(res["reason"], "Prospect requested pricing")
        self.assertIn("Hello", res["reply_body"])

    def test_parse_json_response_markdown_wrapped(self):
        """Verify parsing when LLM outputs markdown fences."""
        raw = '```json\n{"is_human_business_inquiry": false, "reason": "Automated notification", "reply_body": ""}\n```'
        res = EmailClassifierAgent._parse_json_response(raw)
        self.assertFalse(res["is_human_business_inquiry"])
        self.assertEqual(res["reason"], "Automated notification")
        self.assertEqual(res["reply_body"], "")

    def test_parse_json_response_malformed(self):
        """Verify fallback on corrupted JSON."""
        raw = "Invalid non-json response text"
        res = EmailClassifierAgent._parse_json_response(raw)
        self.assertFalse(res["is_human_business_inquiry"])
        self.assertIn("Failed to parse", res["reason"])

    @patch("src.agents.classifier.OpenAI")
    def test_classify_and_generate_mock(self, mock_openai_cls):
        """Test full agent flow with mocked LLM completion."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"is_human_business_inquiry": true, "reason": "Valid inquiry", "reply_body": "Custom response"}'
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_completion

        agent = EmailClassifierAgent(api_key="sk-test")
        agent._client = mock_client

        result = agent.classify_and_generate("Can we meet tomorrow?", "John Doe", "Knowledge context")
        self.assertTrue(result["is_human_business_inquiry"])
        self.assertEqual(result["reply_body"], "Custom response")


if __name__ == "__main__":
    unittest.main()
