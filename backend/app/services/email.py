import smtplib
from html import escape
from urllib.parse import quote
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings


def send_password_reset_email(email: str, token: str) -> bool:
    """Send a one-hour, password-reset-only token without logging its value."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False

    base_url = settings.FRONTEND_BASE_URL.rstrip("/") or (
        settings.FRONTEND_URLS[0].rstrip("/") if settings.FRONTEND_URLS else ""
    )
    if not base_url:
        return False

    reset_url = f"{base_url}/reset-password?token={quote(token, safe='')}"
    message = MIMEMultipart("alternative")
    message["Subject"] = "InterviewGuard password reset"
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message.attach(MIMEText(
        f"Use this link within one hour to reset your InterviewGuard password: {reset_url}",
        "plain",
    ))
    message.attach(MIMEText(
        f"<p>Use this link within one hour to reset your InterviewGuard password:</p><p><a href=\"{escape(reset_url, quote=True)}\">Reset password</a></p>",
        "html",
    ))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, email, message.as_string())
        return True
    except Exception:
        print("Password reset email delivery failed.")
        return False

def send_interview_invitation(
    candidate_name: str, 
    candidate_email: str, 
    meeting_id: str, 
    scheduled_at: str, 
    duration_minutes: int
) -> bool:
    """
    Sends a styled HTML email invitation containing the meeting room details and join URL.
    Falls back to log output if SMTP settings are not provided or error occurs.
    """
    base_url = (settings.INTERVIEW_BASE_URL or settings.FRONTEND_BASE_URL).rstrip("/") or "http://localhost:5173"
    join_url = f"{base_url}/meeting-check?room={meeting_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #f4f6f8;
                color: #333333;
                margin: 0;
                padding: 40px 20px;
            }}
            .card {{
                max-width: 600px;
                background: #ffffff;
                border-radius: 8px;
                padding: 30px;
                margin: 0 auto;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                border-top: 5px solid #4F46E5;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #4F46E5;
            }}
            .details {{
                background-color: #f9fafb;
                border-radius: 6px;
                padding: 20px;
                margin: 20px 0;
                border: 1px solid #e5e7eb;
            }}
            .details table {{
                width: 100%;
            }}
            .details td {{
                padding: 8px 0;
            }}
            .details td.label {{
                font-weight: bold;
                color: #6b7280;
                width: 30%;
            }}
            .btn-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .btn {{
                background-color: #4F46E5;
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 6px;
                font-weight: bold;
                display: inline-block;
            }}
            .footer {{
                text-align: center;
                font-size: 12px;
                color: #9ca3af;
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="header">
                <span class="logo">InterviewGuard AI</span>
                <h2>Interview Invitation</h2>
            </div>
            <p>Dear {escape(candidate_name)},</p>
            <p>You have been invited to participate in a live online video interview. Please find the details of the session below:</p>
            
            <div class="details">
                <table>
                    <tr>
                        <td class="label">Date & Time</td>
                        <td>{scheduled_at}</td>
                    </tr>
                    <tr>
                        <td class="label">Duration</td>
                        <td>{duration_minutes} minutes</td>
                    </tr>
                    <tr>
                        <td class="label">Meeting ID</td>
                        <td><code>{meeting_id}</code></td>
                    </tr>
                </table>
            </div>
            
            <p><strong>Note:</strong> This session may process camera frames for supported monitoring observations. Model availability varies by deployment. Automated flags require human review and are not proof of misconduct. Please ensure you are in a quiet, well-lit room and join using a desktop/laptop computer with an active webcam and microphone.</p>
            
            <div class="btn-container">
                <a href="{join_url}" class="btn">Join Interview Lobby</a>
            </div>
            
            <p>If you have any technical difficulties, please contact support.</p>
            
            <div class="footer">
                <p>&copy; 2026 InterviewGuard AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Check if SMTP details are loaded
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("\n" + "=" * 60)
        print("MOCK EMAIL SENT (SMTP NOT CONFIGURED)")
        print(f"Subject: Live Interview Invitation - InterviewGuard AI")
        print("Invitation credentials were not logged; email was not delivered.")
        print("=" * 60 + "\n")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Live Interview Invitation - InterviewGuard AI"
        msg['From'] = settings.SMTP_FROM
        msg['To'] = candidate_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, candidate_email, msg.as_string())
            
        print("Successfully sent interview invitation email.")
        return True
    except Exception:
        print("Error sending invitation email via SMTP.")
        return False
