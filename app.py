from flask import Flask, request, redirect
import yaml

app = Flask(__name__)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

class ClientIP:
    def __init__(self, ip):
        self.ip = ip
    def __str__(self):
        return self.ip

class IPBlocklist:
    def __init__(self, path='ips.txt'):
        self.path = path
        self.bad_ips = self.load()
    def load(self):
        with open(self.path) as f:
            return f.read().splitlines()
    def is_blocked(self, ip):
        return ip in self.bad_ips

blocklist = IPBlocklist()

def get_client_ip():
    return str(ClientIP(request.remote_addr))

def prepare_message(ip):
    if blocklist.is_blocked(ip):
        return f"Русня на сервере: {ip}"
    return f"Новый IP: {ip}"

def log_to_file(ip):
    with open("visitors.txt", "a") as f:
        f.write(ip + "\n")

def send_telegram_message(message):
    import requests
    token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

@app.route("/")
def log_ip():
    ip = get_client_ip()
    message = prepare_message(ip)
    log_to_file(ip)
    send_telegram_message(message)
    return redirect(config["redirect_url"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
