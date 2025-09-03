import requests
from config import get_config

def send_telegram_message(message: str):
    """Sends a message to the configured Telegram chat."""
    config = get_config()
    token = config['telegram'].get('BOT_TOKEN')
    chat_id = config['telegram'].get('CHAT_ID')

    if not token or not chat_id:
        print("⚠️ Telegram BOT_TOKEN or CHAT_ID not set. Skipping message.")
        return

    max_length = 4096
    try:
        if len(message) <= max_length:
            send_text = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={requests.utils.quote(message)}"
            response = requests.get(send_text)
            response.raise_for_status()
        else:
            # Split the message into parts
            parts = []
            current_part = ""
            for line in message.split('\n'):
                if len(current_part) + len(line) + 1 > max_length:
                    parts.append(current_part)
                    current_part = ""
                current_part += line + "\n"
            if current_part:
                parts.append(current_part)

            for i, part in enumerate(parts):
                header = f"📊 **تقرير التحليل (جزء {i+1}/{len(parts)})**\n\n"
                send_text = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={requests.utils.quote(header + part)}"
                response = requests.get(send_text)
                response.raise_for_status()

        print("✅ تم إرسال التقرير بنجاح إلى تليجرام.")
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في إرسال رسالة تليجرام: {e}")
    except Exception as e:
        print(f"❌ خطأ غير متوقع أثناء إرسال رسالة تليجرام: {e}")
