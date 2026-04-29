import requests
from django.conf import settings


def send_otp(phone: str, code: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    text = (
        f"📱 <b>OTP So'rovi</b>\n\n"
        f"Telefon: <code>{phone}</code>\n"
        f"Kod: <b>{code}</b>\n\n"
        f"⏱ Muddati: 2 daqiqa"
    )
    response = requests.post(
        url,
        json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        },
        timeout=10,
    )
    response.raise_for_status()
