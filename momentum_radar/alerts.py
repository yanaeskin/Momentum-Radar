import os
import requests

def send_telegram(signal):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    text = (f"Momentum Radar candidate: {signal.get('symbol')}\\n"
            f"Score: {signal.get('score')}/100\\n"
            f"Reference close: ${signal.get('price')}\\n"
            f"Indicative stop: ${signal.get('stop')}\\n"
            f"RSI: {signal.get('rsi14')} | RVOL: {signal.get('rvol')}\\n"
            "Research alert only — not an order.")
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": text}, timeout=10)
        return r.ok
    except requests.RequestException:
        return False
