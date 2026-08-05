from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import urllib.request

APPROVED_TOKENS_FILE = "/tmp/approved_tokens.json"

def get_approved_tokens():
    if os.path.exists(APPROVED_TOKENS_FILE):
        try:
            with open(APPROVED_TOKENS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_approved_token(token):
    tokens = get_approved_tokens()
    tokens.add(token.strip().upper())
    try:
        with open(APPROVED_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(tokens), f)
    except Exception as e:
        print("Error saving token:", e)

def send_telegram_msg(bot_token, chat_id, text, reply_markup=None):
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print("Telegram send error:", e)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

        try:
            update = json.loads(body) if body else {}

            # Handle Telegram Inline Keyboard Callback Query
            if "callback_query" in update:
                cq = update["callback_query"]
                cq_id = cq.get("id")
                data_str = cq.get("data", "")
                chat_id = cq.get("message", {}).get("chat", {}).get("id")

                if data_str.startswith("ACC:"):
                    token_to_acc = data_str.split("ACC:", 1)[1].strip().upper()
                    save_approved_token(token_to_acc)
                    send_telegram_msg(bot_token, chat_id, f"✅ <b>BERHASIL ACC!</b>\n\nLink klaim bonus token <code>{token_to_acc}</code> telah AKTIF.\n\nLink: https://stock-blinx.vercel.app/bonus?token={token_to_acc}")

            # Handle Telegram Messages (Commands like /approve TOKEN or /acc TOKEN)
            elif "message" in update:
                msg = update["message"]
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()

                if text.startswith("/approve") or text.startswith("/acc") or text.startswith("/acc_"):
                    parts = text.split(maxsplit=1)
                    if len(parts) > 1:
                        token = parts[1].strip().upper()
                        save_approved_token(token)
                        send_telegram_msg(bot_token, chat_id, f"✅ <b>BERHASIL ACC!</b>\n\nKode/Token Bonus <code>{token}</code> telah disetujui.\nCustomer dapat membuka link: https://stock-blinx.vercel.app/bonus?token={token}")
                    else:
                        send_telegram_msg(bot_token, chat_id, "⚠️ Format salah. Gunakan: <code>/approve KODE_TOKEN</code>")
                elif text == "/start":
                    send_telegram_msg(bot_token, chat_id, "👋 Selamat datang di Bot Telegram Approval Stock Blinx Bonus!\n\nGunakan perintah <code>/approve KODE</code> untuk menyetujui klaim bonus customer.")
        except Exception as e:
            print("Telegram webhook error:", e)

        data = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        data = json.dumps({"status": "Telegram bot webhook active"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(data)
