from pathlib import Path
import pytest
from app.services.generator import CertificateData, CertificateGenerator


def test_generator_creates_valid_pdf(tmp_path: Path):
    output_pdf = tmp_path / "cert_test.pdf"
    data = CertificateData(
        recipient_name="Ada Lovelace",
        recipient_email="ada@example.com",
        event_name="Foundations of Computer Programming",
        issue_date="October 8, 2026",
        issuer_name="Dr. Alan Turing",
        issuer_title="Head of Computing",
        organization="Institute of Advanced Studies",
        certificate_code="CERT-2026-TEST-0001",
        recipient_identifier="REG-1815",
        custom_data={"grade": "A+", "track": "Algorithms"},
    )

    result_path = CertificateGenerator.generate_pdf(data, output_pdf)
    assert result_path.exists()
    assert result_path.is_file()
    assert result_path.stat().st_size > 1000  # Valid non-empty PDF

    # Check PDF header signature
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_generator_handles_very_long_strings(tmp_path: Path):
    output_pdf = tmp_path / "long_text_cert.pdf"
    long_name = "Dr. Wolfeschlegelsteinhausenbergerdorff The Third Senior High Achiever"
    long_event = (
        "International Advanced Masterclass in Distributed Microservices, Cloud Native Computing, "
        "and Ultra-High-Performance Network Protocol Engineering with Comprehensive Case Studies"
    )

    data = CertificateData(
        recipient_name=long_name,
        recipient_email="longname@example.com",
        event_name=long_event,
        issue_date="October 8, 2026",
        issuer_name="Prof. Very Long Issuer Signatory Name",
        issuer_title="Chief Executive Distinguished Distinguished Chair",
        organization="Global International Academy of Excellence",
        certificate_code="CERT-2026-LONG-9999",
    )

    result_path = CertificateGenerator.generate_pdf(data, output_pdf)
    assert result_path.exists()
    assert result_path.stat().st_size > 1000
