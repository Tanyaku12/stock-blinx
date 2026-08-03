from http.server import BaseHTTPRequestHandler
import json
import os

def determine_tier(num_str):
    for d in range(10):
        if str(d) * 6 in num_str:
            return 'SSS TIER (6x digit berulang)'
    for d in range(10):
        if str(d) * 5 in num_str:
            return 'SS TIER (5x digit berulang)'
    return 'S TIER (4x digit berulang)'

def load_all_stock():
    possible_dirs = [
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.getcwd(),
        "/var/task",
        os.path.abspath(".")
    ]

    all_path = None
    sold_path = None
    for p in possible_dirs:
        test_all = os.path.join(p, "RAPI", "all.txt")
        if os.path.exists(test_all):
            all_path = test_all
            sold_path = os.path.join(p, "RAPI", "sold.txt")
            break

    items = []
    
    # Load available stock from all.txt
    if all_path and os.path.exists(all_path):
        current_cat = 'S TIER (4x digit berulang)'
        with open(all_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('---'):
                    current_cat = line.strip('- ').strip()
                else:
                    items.append({
                        'number': line,
                        'category': current_cat,
                        'status': 'AVAILABLE'
                    })

    # Load sold stock from sold.txt
    if sold_path and os.path.exists(sold_path):
        current_cat = 'S TIER (4x digit berulang)'
        with open(sold_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('---'):
                    current_cat = line.strip('- ').strip()
                elif '|' in line:
                    num, cat = line.split('|', 1)
                    items.append({
                        'number': num.strip(),
                        'category': cat.strip(),
                        'status': 'SOLD'
                    })
                else:
                    items.append({
                        'number': line,
                        'category': determine_tier(line),
                        'status': 'SOLD'
                    })
    return items

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        items = load_all_stock()
        data = json.dumps(items).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 's-maxage=60, stale-while-revalidate=300')
        self.end_headers()
        self.wfile.write(data)
