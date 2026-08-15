# backend/alerts.py
"""
SMS alert dispatch. Sends real messages through Twilio when credentials are
configured via environment variables; otherwise falls back to a clearly-labeled
console simulation so the app still runs end-to-end in local development.

Required environment variables for live SMS:
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_FROM_NUMBER   (a Twilio phone number in E.164 format, e.g. +1415XXXXXXX)
"""
import os
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

_client = None
if Client and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms_alert(phone_number, message):
    """
    Sends a single SMS. Uses live Twilio when credentials are set; otherwise
    prints a clearly-labeled simulation and still returns success so callers
    (and demos) don't break when no Twilio account is attached.
    """
    if _client is None or not TWILIO_FROM_NUMBER:
        print("\n[SMS SIMULATION] Twilio credentials not configured — set "
              "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER for live SMS.")
        print(f"Recipient: {phone_number}")
        print(f"Payload:   {message}\n")
        return {"success": True, "simulated": True, "message": "SMS simulated (no Twilio credentials set)"}

    try:
        msg = _client.messages.create(body=message, from_=TWILIO_FROM_NUMBER, to=phone_number)
        return {"success": True, "simulated": False, "sid": msg.sid, "status": msg.status}
    except TwilioRestException as e:
        return {"success": False, "simulated": False, "error": str(e)}


def send_emergency_sms(location, threat_level):
    """
    Looks up every NGO registered for the affected region and dispatches an
    emergency alert SMS to each of their registered contact numbers.

    NOTE: app.py's /api/trigger_alert route calls this function — it previously
    only existed as send_sms_alert(), so this route was crashing with an
    AttributeError before this fix.
    """
    ngos = database.get_ngos_by_region(location)
    if not ngos:
        return {
            "success": True,
            "dispatched": 0,
            "message": f"No NGOs registered for '{location}' — nothing to dispatch."
        }

    message = (
        f"CoastSentinel AI ALERT: {threat_level} risk detected near {location}. "
        f"Please review the dashboard and coordinate a response."
    )

    results = []
    for ngo in ngos:
        result = send_sms_alert(ngo["phone"], message)
        results.append({"ngo": ngo["org_name"], "phone": ngo["phone"], **result})

    return {
        "success": True,
        "dispatched": len(results),
        "threat_level": threat_level,
        "location": location,
        "results": results
    }