import requests
from django.conf import settings


def send_telegram_message(message: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False

    return True
