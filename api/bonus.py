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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [""])[0].strip().upper()
        code = params.get("code", [""])[0].strip().upper()

        target_token = token or code
        approved_tokens = get_approved_tokens()

        # Simple verification: If token is in approved_tokens or matches master/admin test token 'BLINX2026' or 'ADMIN123'
        is_approved = False
        if target_token:
            if target_token in approved_tokens or target_token in ["BLINX2026", "ADMIN123", "ACC2026"]:
                is_approved = True

        response_data = {
            "token": target_token,
            "approved": is_approved,
            "message": "Bonus unlocked successfully!" if is_approved else "Bonus access requires Admin approval via Telegram Bot."
        }

        data = json.dumps(response_data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        
        try:
            req_data = json.loads(body) if body else {}
            token = req_data.get("token", "").strip().upper()
            action = req_data.get("action", "")

            if action == "approve" and token:
                save_approved_token(token)
                res = {"success": True, "token": token, "message": f"Token {token} approved successfully!"}
            else:
                res = {"success": False, "message": "Invalid action or token"}
        except Exception as e:
            res = {"success": False, "error": str(e)}

        data = json.dumps(res).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)
