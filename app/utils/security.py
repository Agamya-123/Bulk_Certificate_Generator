import hashlib
import secrets
import string
from datetime import datetime, timezone


def generate_certificate_code(prefix: str = "CERT") -> str:
    """
    Generate a cryptographically secure, unique, and readable certificate code.
    Format: CERT-YYYY-XXXX-XXXX (e.g. CERT-2026-K9M2-P7X4)
    """
    year = datetime.now(timezone.utc).strftime("%Y")
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters (0, O, I, 1, L)
    clean_alphabet = "".join(ch for ch in alphabet if ch not in "0OI1L")

    part1 = "".join(secrets.choice(clean_alphabet) for _ in range(4))
    part2 = "".join(secrets.choice(clean_alphabet) for _ in range(4))
    return f"{prefix}-{year}-{part1}-{part2}"


def generate_verification_hash(job_id: str, recipient_email: str, cert_code: str) -> str:
    """Generate a SHA-256 integrity hash for certificate verification."""
    raw = f"{job_id}:{recipient_email}:{cert_code}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
