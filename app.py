from flask import Flask, request, redirect
from datetime import datetime
import requests
import ipaddress

app = Flask(__name__)

LOG_FILE = "visitors.log"
IPS_FILE = "ips.txt"  # список IP и подсетей

# --- Telegram настройки ---
TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

def load_ips():
    """Загружает IP и подсети из файла"""
    subnets = []
    try:
        with open(IPS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        subnets.append(ipaddress.ip_network(line))
                    except ValueError:
                        print(f"⚠️ Неверный IP или подсеть в ips.txt: {line}")
    except FileNotFoundError:
        print(f"Файл {IPS_FILE} не найден.")
    return subnets

SUBNETS = load_ips()

def is_ip_in_list(ip):
    """Проверяет, принадлежит ли IP указанным подсетям"""
    try:
        ip_addr = ipaddress.ip_address(ip)
        for subnet in SUBNETS:
            if ip_addr in subnet:
                return True
    except ValueError:
        pass
    return False

def get_real_ip():
    """Без nginx всегда используем remote_addr"""
    return request.remote_addr

@app.route("/watch")
def watch():
    video_id = request.args.get('v')
    if not video_id:
        return "Не указан параметр v (ID видео).", 400

    user_ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Неизвестен')
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = f"{time} - IP: {user_ip} - Видео: {video_id} - User-Agent: {user_agent}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    print(log_line.strip())

    tg_message = (
        f"🔔 Новый переход!\n"
        f"Видео: {video_id}\n"
        f"IP: {user_ip}\n"
        f"User-Agent: {user_agent}\n"
        f"Время: {time}"
    )
    send_telegram_message(tg_message)

    if is_ip_in_list(user_ip):
        rus_message = f"🚨 Русские на сервере! IP: {user_ip}"
        print(rus_message)
        send_telegram_message(rus_message)

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    return redirect(youtube_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
