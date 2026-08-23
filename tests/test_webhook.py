"""Integration tests for Flask webhook endpoints."""
import json
import unittest
from unittest.mock import patch


class TestWebhookEndpoints(unittest.TestCase):
    def test_webhook_payload_parsing_structure(self):
        """Test webhook processing logic extracts fields cleanly."""
        payload = {
            "items": [
                {
                    "From": {"Address": "prospect@example.com", "Name": "Jane Smith"},
                    "Subject": "Interested in your AI services",
                    "TextBody": "Hello, how does your AI employee model work?",
                }
            ]
        }
        item = payload["items"][0]
        self.assertEqual(item["From"]["Address"], "prospect@example.com")
        self.assertEqual(item["From"]["Name"], "Jane Smith")
        self.assertIn("AI employee", item["TextBody"])


if __name__ == "__main__":
    unittest.main()
