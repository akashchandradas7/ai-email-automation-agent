"""Unit tests for DNS MX record verification."""
import unittest
from src.tools.email_verifier import verify_email_domain


class TestEmailVerifier(unittest.TestCase):
    def test_verify_email_domain_syntax(self):
        """Ensure invalid syntax email formats are immediately rejected."""
        is_valid, reason = verify_email_domain("not-an-email")
        self.assertFalse(is_valid)

    def test_verify_email_domain_missing_domain(self):
        """Ensure missing domain is rejected."""
        is_valid, reason = verify_email_domain("user@")
        self.assertFalse(is_valid)

    def test_verify_email_domain_empty(self):
        """Ensure empty email is rejected."""
        is_valid, reason = verify_email_domain("")
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
