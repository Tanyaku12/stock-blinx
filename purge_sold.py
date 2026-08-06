"""
purge_sold.py — Hapus data akun SOLD dari /RAPI/ maupun /ALL/
Membaca list ID sold dari /root/max/RAPI/sold.txt, lalu menghapus semua data terkait
(berdasarkan account_id maupun uid) dari seluruh file di /root/max/RAPI/ dan /root/max/ALL/.
"""

import os
import json
import re
import sys

BASE = "/root/max"
RAPI = os.path.join(BASE, "RAPI")
DST  = os.path.join(BASE, "ALL")

def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ❌ Error loading {path}: {e}")
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved {len(data)} entries → {path}")

def get_sold_info():
    """Membaca list ID sold dari RAPI/sold.txt dan mengumpulkan sold_ids & sold_uids."""
    sold_file = os.path.join(RAPI, "sold.txt")
    sold_ids = set()
    if os.path.exists(sold_file):
        with open(sold_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("---"):
                    continue
                acc_id = line.split("|")[0].strip()
                if acc_id and acc_id.isdigit():
                    sold_ids.add(acc_id)

    sold_uids = set()
    # Collect associated UIDs from RAPI/data.json
    rapi_data_path = os.path.join(RAPI, "data.json")
    if os.path.exists(rapi_data_path):
        for item in load_json(rapi_data_path):
            aid = str(item.get("account_id", ""))
            uid = str(item.get("uid", ""))
            if aid in sold_ids and uid:
                sold_uids.add(uid)

    # Collect associated UIDs from ALL/ACCOUNTS/accounts-ID.json
    acc_path = os.path.join(DST, "ACCOUNTS", "accounts-ID.json")
    if os.path.exists(acc_path):
        for item in load_json(acc_path):
            aid = str(item.get("account_id", ""))
            uid = str(item.get("uid", ""))
            if aid in sold_ids and uid:
                sold_uids.add(uid)

    return sold_ids, sold_uids

def purge_sold_accounts():
    print("=" * 60)
    print("[PURGE SOLD] MENGHAPUS DATA AKUN SOLD DARI /RAPI/ DAN /ALL/")
    print("=" * 60)

    sold_ids, sold_uids = get_sold_info()
    if not sold_ids:
        print("ℹ Tidak ada ID sold yang ditemukan di RAPI/sold.txt.")
        return 0

    print(f"📌 Found {len(sold_ids)} SOLD account IDs in RAPI/sold.txt: {sorted(list(sold_ids))}")
    if sold_uids:
        print(f"📌 Found {len(sold_uids)} associated UIDs: {sorted(list(sold_uids))}")

    total_removed = 0

    # ─── 1. Hapus dari RAPI/*.txt ─────────────────────────────────────────────
    for fname in ["blinx.txt", "rare.txt", "all.txt"]:
        fpath = os.path.join(RAPI, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                lines = [l.rstrip("\n") for l in f]
            new_lines = []
            removed_count = 0
            for line in lines:
                s = line.strip()
                if s in sold_ids:
                    removed_count += 1
                else:
                    new_lines.append(line)
            if removed_count > 0:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write("\n".join(new_lines) + "\n")
                print(f"  ✓ Hapus {removed_count} ID sold dari RAPI/{fname}")
                total_removed += removed_count

    # ─── 2. Hapus dari RAPI/data.json ──────────────────────────────────────────
    rapi_data_path = os.path.join(RAPI, "data.json")
    rapi_data = load_json(rapi_data_path)
    if rapi_data:
        new_rapi_data = [
            item for item in rapi_data
            if str(item.get("account_id", "")) not in sold_ids
            and str(item.get("uid", "")) not in sold_uids
        ]
        removed = len(rapi_data) - len(new_rapi_data)
        if removed > 0:
            save_json(rapi_data_path, new_rapi_data)
            print(f"  ✓ Hapus {removed} akun sold dari RAPI/data.json")
            total_removed += removed

            # Sync update data.json to spin dirs
            for spin_dst in ["/root/spin/gajah", "/root/spin/dark", "/root/spin/spin-gajah"]:
                if os.path.exists(spin_dst):
                    dst_file = os.path.join(spin_dst, "data.json")
                    save_json(dst_file, new_rapi_data)
                    print(f"  ✓ Synced updated data.json → {spin_dst}")

    # ─── 3. Hapus dari ALL/ACCOUNTS/accounts-ID.json ─────────────────────────
    acc_path = os.path.join(DST, "ACCOUNTS", "accounts-ID.json")
    acc_data = load_json(acc_path)
    if acc_data:
        new_acc_data = [
            item for item in acc_data
            if str(item.get("account_id", "")) not in sold_ids
            and str(item.get("uid", "")) not in sold_uids
        ]
        removed = len(acc_data) - len(new_acc_data)
        if removed > 0:
            save_json(acc_path, new_acc_data)
            print(f"  ✓ Hapus {removed} akun sold dari ALL/ACCOUNTS/accounts-ID.json")
            total_removed += removed

    # ─── 4. Hapus dari ALL/RARE/rare-ID.json ─────────────────────────────────
    rare_path = os.path.join(DST, "RARE", "rare-ID.json")
    rare_data = load_json(rare_path)
    if rare_data:
        new_rare_data = [
            item for item in rare_data
            if str(item.get("account_id", "")) not in sold_ids
            and str(item.get("uid", "")) not in sold_uids
        ]
        removed = len(rare_data) - len(new_rare_data)
        if removed > 0:
            save_json(rare_path, new_rare_data)
            print(f"  ✓ Hapus {removed} akun sold dari ALL/RARE/rare-ID.json")
            total_removed += removed

    # ─── 5. Hapus dari ALL/TOKENS/tokens-ID.json ───────────────────────────────
    tokens_path = os.path.join(DST, "TOKENS", "tokens-ID.json")
    tokens_data = load_json(tokens_path)
    if tokens_data:
        new_tokens_data = [
            item for item in tokens_data
            if str(item.get("account_id", "")) not in sold_ids
            and str(item.get("uid", "")) not in sold_uids
        ]
        removed = len(tokens_data) - len(new_tokens_data)
        if removed > 0:
            save_json(tokens_path, new_tokens_data)
            print(f"  ✓ Hapus {removed} token sold dari ALL/TOKENS/tokens-ID.json")
            total_removed += removed

    # ─── 6. Hapus dari ALL/COUPLES/couples-ID.json ─────────────────────────────
    couples_path = os.path.join(DST, "COUPLES", "couples-ID.json")
    couples_data = load_json(couples_path)
    if couples_data:
        new_couples_data = []
        for item in couples_data:
            a1_id = str(item.get("account1", {}).get("account_id", ""))
            a2_id = str(item.get("account2", {}).get("account_id", ""))
            a1_uid = str(item.get("account1", {}).get("uid", ""))
            a2_uid = str(item.get("account2", {}).get("uid", ""))
            if (a1_id in sold_ids or a2_id in sold_ids or a1_uid in sold_uids or a2_uid in sold_uids):
                continue
            new_couples_data.append(item)
        removed = len(couples_data) - len(new_couples_data)
        if removed > 0:
            save_json(couples_path, new_couples_data)
            print(f"  ✓ Hapus {removed} couple sold dari ALL/COUPLES/couples-ID.json")
            total_removed += removed

    # ─── 7. Hapus dari ALL/HUNTER/*.json ──────────────────────────────────────
    hunter_dir = os.path.join(DST, "HUNTER")
    if os.path.exists(hunter_dir):
        for fname in os.listdir(hunter_dir):
            if fname.endswith(".json"):
                hpath = os.path.join(hunter_dir, fname)
                hdata = load_json(hpath)
                new_hdata = [
                    item for item in hdata
                    if str(item.get("account_id", "")) not in sold_ids
                    and str(item.get("uid", "")) not in sold_uids
                ]
                removed = len(hdata) - len(new_hdata)
                if removed > 0:
                    save_json(hpath, new_hdata)
                    print(f"  ✓ Hapus {removed} akun sold dari ALL/HUNTER/{fname}")
                    total_removed += removed

    # Update web catalog js
    try:
        if BASE not in sys.path:
            sys.path.append(BASE)
        from merge_and_scan import update_web_stock_data
        update_web_stock_data()
    except Exception as e:
        print(f"  ℹ Update web stock data warning: {e}")

    print(f"\n🎉 Selesai! Total {total_removed} entri data akun sold telah dihapus dari /RAPI/ dan /ALL/.")
    return total_removed

if __name__ == "__main__":
    purge_sold_accounts()
