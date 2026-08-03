"""
run_cracked.py — Wrapper untuk updateapis.py dengan bypass lisensi
Jalankan dengan: /root/.pyenv/versions/3.13.0/bin/python /root/max/run_cracked.py
"""
import sys
import os
import builtins

# ─── 1) Patch requests sebelum apapun di-import ─────────────────────────────

import importlib
import importlib.util
import runpy

# Pre-import requests dulu agar bisa di-patch
import requests

_orig_post = requests.post
_orig_session_post = requests.Session.post

class _MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = str(data)

    def json(self):
        return self._data

    def raise_for_status(self):
        pass

_SUCCESS_PAYLOAD = {
    "status": "success",
    "data": {
        "owner": "Cracked",
        "days_left": 9999,
        "expired_at": "2099-12-31",
        "expired": False,
        "active": True,
    },
    "rare_hunter": {
        "locked": False,
        "score_min": 13,
        "score_max": 27,
        "target_ids": [],
    },
    "message": "success",
    "result": "success",
}

def _mock_post(url, *args, **kwargs):
    url_str = str(url)
    if "serverapikeycgu" in url_str or "co-id.id" in url_str:
        return _MockResponse(_SUCCESS_PAYLOAD)
    return _orig_post(url, *args, **kwargs)

def _mock_session_post(self, url, *args, **kwargs):
    url_str = str(url)
    if "serverapikeycgu" in url_str or "co-id.id" in url_str:
        return _MockResponse(_SUCCESS_PAYLOAD)
    return _orig_session_post(self, url, *args, **kwargs)

requests.post = _mock_post
requests.Session.post = _mock_session_post

# ─── 2) Patch requests.get juga (untuk background_kill_checker) ─────────────

_orig_get = requests.get
_orig_session_get = requests.Session.get

def _mock_get(url, *args, **kwargs):
    url_str = str(url)
    if "serverapikeycgu" in url_str or "co-id.id" in url_str:
        return _MockResponse(_SUCCESS_PAYLOAD)
    return _orig_get(url, *args, **kwargs)

def _mock_session_get(self, url, *args, **kwargs):
    url_str = str(url)
    if "serverapikeycgu" in url_str or "co-id.id" in url_str:
        return _MockResponse(_SUCCESS_PAYLOAD)
    return _orig_session_get(self, url, *args, **kwargs)

requests.get = _mock_get
requests.Session.get = _mock_session_get

# ─── 3) Patch input() agar otomatis mengisi license key ─────────────────────

_orig_input = builtins.input
_license_key = "CGU-8833-2AF3-7914"
_license_injected = False

def _mock_input(prompt=""):
    global _license_injected
    p = str(prompt)
    if not _license_injected and ("license" in p.lower() or "lisensi" in p.lower() or "key" in p.lower() or "kunci" in p.lower()):
        print(prompt + _license_key)
        _license_injected = True
        return _license_key
    return _orig_input(prompt)

builtins.input = _mock_input

# ─── 4) Patch Telegram agar tidak kirim data asli ───────────────────────────

# Patch requests untuk Telegram juga (silent)
_orig_post_2 = requests.post

def _mock_post_final(url, *args, **kwargs):
    url_str = str(url)
    if "api.telegram.org" in url_str:
        # Diam-diam bypass Telegram telemetry
        return _MockResponse({"ok": True, "result": {}})
    return _orig_post_2(url, *args, **kwargs)

requests.post = _mock_post_final

TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "updateapis.py")

def _auto_merge_on_exit():
    cgu_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CGU-GEN-JAWA")
    if os.path.exists(cgu_dir):
        print("\n[AUTO-MERGE] Menjalankan merge_and_scan.py untuk CGU-GEN-JAWA...")
        merge_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merge_and_scan.py")
        if os.path.exists(merge_script):
            try:
                os.system(f"{sys.executable} {merge_script}")
            except Exception as e:
                print(f"[AUTO-MERGE ERROR] {e}")

import atexit
atexit.register(_auto_merge_on_exit)

try:
    runpy.run_path(TARGET, run_name="__main__")
except SystemExit as e:
    sys.exit(e.code)
except KeyboardInterrupt:
    print("\n[INFO] Dihentikan oleh user.")
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
