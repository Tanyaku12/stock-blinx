#!/usr/bin/env python3
"""
VIP Stock Store - Web Server
Serves static web application and provides live /api/stock endpoint reading /root/max/RAPI/all.txt
"""

import http.server
import socketserver
import json
import os

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
ALL_TXT_PATH = os.path.join(os.path.dirname(__file__), "RAPI", "all.txt")

def parse_all_txt(file_path):
    if not os.path.exists(file_path):
        return []
    
    items = []
    current_cat = 'S TIER (4x digit berulang)'

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('---'):
                current_cat = line.strip('- ').strip()
            else:
                items.append({
                    'number': line,
                    'category': current_cat
                })
    return items

class VIPStockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        # API Endpoint for Live Stock Data
        if self.path == '/api/stock':
            items = parse_all_txt(ALL_TXT_PATH)
            data = json.dumps(items).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
            return

        # Direct access to RAPI/all.txt
        if self.path == '/RAPI/all.txt' or self.path == '/all.txt':
            if os.path.exists(ALL_TXT_PATH):
                with open(ALL_TXT_PATH, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
                return

        return super().do_GET()

if __name__ == "__main__":
    os.chdir(WEB_DIR)
    with socketserver.TCPServer(("", PORT), VIPStockHandler) as httpd:
        print(f"==================================================")
        print(f" 🚀 VIP Stock Store Server Running!")
        print(f" 🌐 Web UI: http://localhost:{PORT}")
        print(f" 📊 API Stock: http://localhost:{PORT}/api/stock")
        print(f" 📄 Reading stock from: {ALL_TXT_PATH}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
