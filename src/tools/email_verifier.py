"""DNS MX Record Pre-Flight Verifier."""
from typing import Tuple
from src.utils.logger import get_logger

logger = get_logger("email_verifier")


def verify_email_domain(email: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    Validate that an email address has an active domain with valid MX records.

    Args:
        email: Recipient email address to verify.
        timeout: DNS resolution timeout in seconds.

    Returns:
        Tuple of (is_valid: bool, reason: str)
    """
    if not email or "@" not in email:
        return False, "Invalid email format"

    domain = email.split("@")[1].strip()
    if not domain:
        return False, "Missing domain"

    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        records = resolver.resolve(domain, "MX")
        if records and len(records) > 0:
            return True, "Valid MX record found"
        return False, "No MX records found for domain"
    except ImportError:
        logger.warning("dnspython is not installed; skipping DNS validation.")
        return True, "DNS verification skipped (dnspython not installed)"
    except Exception as e:
        # Check for specific dns exception types dynamically
        err_name = type(e).__name__
        if "NXDOMAIN" in err_name:
            logger.warning(f"Domain {domain} does not exist (NXDOMAIN).")
            return False, f"Domain '{domain}' does not exist"
        elif "NoAnswer" in err_name:
            logger.warning(f"Domain {domain} has no MX records.")
            return False, f"Domain '{domain}' has no mail exchange (MX) records"
        elif "Timeout" in err_name:
            logger.warning(f"DNS resolution timed out for domain {domain}.")
            return False, f"DNS timeout resolving '{domain}'"
        else:
            logger.warning(f"DNS verification error for {domain}: {str(e)}")
            return False, f"DNS verification error: {str(e)}"
