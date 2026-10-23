from app.core.config import settings
from app.services import email as email_service


def test_unconfigured_invitation_does_not_log_bearer_code(monkeypatch, capsys):
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    meeting_code = "private-meeting-code-123"
    address = "candidate-private@example.com"

    result = email_service.send_interview_invitation(
        "Candidate", address, meeting_code, "tomorrow", 30
    )

    output = capsys.readouterr().out
    assert result is False
    assert meeting_code not in output
    assert address not in output
    assert "was not delivered" in output


def test_smtp_exception_does_not_log_exception_or_invitation_credentials(
    monkeypatch, capsys
):
    monkeypatch.setattr(settings, "SMTP_USER", "smtp-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-password")
    monkeypatch.setattr(email_service.smtplib, "SMTP", lambda *args, **kwargs: _FailingSMTP())
    meeting_code = "private-meeting-code-456"
    address = "candidate-private@example.com"

    result = email_service.send_interview_invitation(
        "Candidate", address, meeting_code, "tomorrow", 30
    )

    output = capsys.readouterr().out
    assert result is False
    assert meeting_code not in output
    assert address not in output
    assert "smtp-secret-detail" not in output


class _FailingSMTP:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def starttls(self):
        raise RuntimeError("smtp-secret-detail")
