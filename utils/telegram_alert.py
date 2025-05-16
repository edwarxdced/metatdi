import requests

from config import BOT_TOKEN, CHAT_ID


def send_telegram_alert(message: str) -> bool:
    return True
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        response = requests.post(url, data=data, timeout=10)
        print(f"Telegram response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False
    
