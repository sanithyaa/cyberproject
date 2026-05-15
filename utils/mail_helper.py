"""
Email helper – wraps Flask-Mail for OTP and notification emails.
"""
from flask import current_app, render_template_string
from flask_mail import Message
from extensions import mail
import pyotp, base64, os


def generate_otp_secret() -> str:
    """Generate a new TOTP secret for a user."""
    return pyotp.random_base32()


def get_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret, interval=300)  # 5-minute window


def send_otp_email(user_email: str, otp_code: str):
    print("🔐 OTP for", user_email, ":", otp_code)
    """Send a one-time password to the user's email."""
    body = f"""
    <h2>Your Voting System OTP</h2>
    <p>Your one-time password is: <strong style="font-size:24px">{otp_code}</strong></p>
    <p>This code expires in <strong>5 minutes</strong>.</p>
    <p>If you did not request this, please ignore this email.</p>
    """
    msg = Message(
        subject='Your OTP – Secure Voting System',
        recipients=[user_email],
        html=body,
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Mail send failed: {e}')
        return False


def send_vote_confirmation(user_email: str, candidate_name: str):
    """Send a vote receipt email."""
    body = f"""
    <h2>Vote Confirmation</h2>
    <p>Your vote for <strong>{candidate_name}</strong> has been recorded successfully.</p>
    <p>Thank you for participating in the election.</p>
    """
    msg = Message(
        subject='Vote Confirmation – Secure Voting System',
        recipients=[user_email],
        html=body,
    )
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Vote confirmation mail failed: {e}')
