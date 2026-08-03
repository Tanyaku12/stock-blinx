from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "RAPI", "all.txt")

        items = []
        current_cat = 'S TIER (4x digit berulang)'

        if os.path.exists(file_path):
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

        data = json.dumps(items).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 's-maxage=60, stale-while-revalidate=300')
        self.end_headers()
        self.wfile.write(data)
