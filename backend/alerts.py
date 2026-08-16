# backend/alerts.py
"""
Multi-channel alert dispatch: SMS via Twilio (when configured) and email via
SMTP (always available). Email needs no per-recipient verification the way
Twilio trial SMS does, so it's the channel that stays fully automated at
zero cost — SMS is an optional enhancement layered on top when Twilio is
configured (trial-verified numbers or a paid account).

Environment variables:
    Twilio (optional — SMS is skipped/simulated gracefully if unset):
        TWILIO_ACCOUNT_SID
        TWILIO_AUTH_TOKEN
        TWILIO_FROM_NUMBER

    SMTP (needed for live email; simulated if unset):
        SMTP_HOST          (default: smtp.gmail.com)
        SMTP_PORT          (default: 465)
        SMTP_EMAIL         (the sending Gmail address)
        SMTP_APP_PASSWORD  (a 16-character Gmail App Password — NOT your normal password)
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText

import database

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:  # pragma: no cover - twilio is in requirements.txt, but fail soft
    Client = None
    TwilioRestException = Exception

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD")

_client = None
if Client and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms_alert(phone_number, message):
    """Sends a single SMS via Twilio, or simulates it if Twilio isn't configured."""
    if _client is None or not TWILIO_FROM_NUMBER:
        print("\n[SMS SIMULATION] Twilio not configured — set TWILIO_ACCOUNT_SID, "
              "TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER for live SMS.")
        print(f"Recipient: {phone_number}")
        print(f"Payload:   {message}\n")
        return {"success": True, "simulated": True, "channel": "sms",
                "message": "SMS simulated (no Twilio credentials set)"}

    try:
        msg = _client.messages.create(body=message, from_=TWILIO_FROM_NUMBER, to=phone_number)
        return {"success": True, "simulated": False, "channel": "sms", "sid": msg.sid, "status": msg.status}
    except TwilioRestException as e:
        return {"success": False, "simulated": False, "channel": "sms", "error": str(e)}


def send_email_alert(to_email, subject, message):
    """
    Sends a real email via SMTP. Free, and — unlike Twilio trial SMS —
    needs no recipient pre-verification. Simulates (console-only) when
    SMTP_EMAIL / SMTP_APP_PASSWORD aren't set.
    """
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        print("\n[EMAIL SIMULATION] SMTP not configured — set SMTP_EMAIL and "
              "SMTP_APP_PASSWORD (a Gmail App Password) for live email.")
        print(f"Recipient: {to_email}")
        print(f"Subject:   {subject}")
        print(f"Body:      {message}\n")
        return {"success": True, "simulated": True, "channel": "email",
                "message": "Email simulated (no SMTP credentials set)"}

    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return {"success": True, "simulated": False, "channel": "email"}
    except Exception as e:
        return {"success": False, "simulated": False, "channel": "email", "error": str(e)}


def send_emergency_sms(location, threat_level):
    """
    Dispatches an emergency alert to every NGO registered for the affected
    region, over every channel available: SMS via Twilio when configured,
    and email via SMTP always. Email requires no per-recipient verification,
    so alerts stay fully automated even with zero paid services.
    """
    ngos = database.get_ngos_by_region(location)
    if not ngos:
        return {
            "success": True,
            "dispatched": 0,
            "message": f"No NGOs registered for '{location}' — nothing to dispatch."
        }

    sms_text = (
        f"CoastSentinel AI ALERT: {threat_level} risk detected near {location}. "
        f"Please review the dashboard and coordinate a response."
    )
    email_subject = f"CoastSentinel AI Alert: {threat_level} risk near {location}"
    email_body = (
        f"A {threat_level} coastal risk has been detected near {location}.\n\n"
        f"Please log into the CoastSentinel AI dashboard to review the affected "
        f"sector and coordinate a cleanup or response.\n\n"
        f"— CoastSentinel AI (automated alert)"
    )

    results = []
    for ngo in ngos:
        sms_result = send_sms_alert(ngo["phone"], sms_text)
        email_result = send_email_alert(ngo["email"], email_subject, email_body)
        results.append({
            "ngo": ngo["org_name"],
            "phone": ngo["phone"],
            "email": ngo["email"],
            "sms": sms_result,
            "email": email_result
        })

    return {
        "success": True,
        "dispatched": len(results),
        "threat_level": threat_level,
        "location": location,
        "results": results
    }