# backend/alerts.py

def send_sms_alert(phone_number, message):
    """
    SMS Alert Dispatcher module.
    Prints alerts to console. Integrate with Twilio/SMS Gateway for live production.
    """
    try:
        print(f"\n[SMS DISPATCH] Calling Gateway...")
        print(f"Recipient: {phone_number}")
        print(f"Payload:   {message}\n")
        return {"success": True, "message": "SMS dispatched successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}