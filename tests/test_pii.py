import json
from pathlib import Path

from app import logging_config
from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_logger_scrubs_pii_from_context_and_nested_payload_before_file_write(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    logging_config.configure_logging()

    logging_config.get_logger().info(
        "pii_probe",
        service="test",
        session_id="demo.user@example.com",
        payload={
            "contacts": ["0912345678", {"cccd": "012345678901"}],
            "card": "4111 1111 1111 1111",
        },
    )

    raw_log = log_path.read_text(encoding="utf-8")
    record = json.loads(raw_log)
    for raw_value in (
        "demo.user@example.com",
        "0912345678",
        "012345678901",
        "4111 1111 1111 1111",
    ):
        assert raw_value not in raw_log
    assert record["session_id"] == "[REDACTED_EMAIL]"
    assert record["payload"]["contacts"] == [
        "[REDACTED_PHONE_VN]",
        {"cccd": "[REDACTED_CCCD]"},
    ]
    assert record["payload"]["card"] == "[REDACTED_CREDIT_CARD]"
