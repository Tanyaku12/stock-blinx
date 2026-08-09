"""
process_zyx.py — Standardize and merge ZYXX-ULTRA (/root/zyx/ZYXX-ULTRA) into /root/max/ALL and /root/max/RAPI
"""

import json
import os
import shutil
import sys

ZYX_DIR = "/root/zyx/ZYXX-ULTRA"
MAX_DIR = "/root/max"
ALL_DIR = os.path.join(MAX_DIR, "ALL")
RAPI_DIR = os.path.join(MAX_DIR, "RAPI")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved {len(data)} entries → {path}")

# Import RAPI logic from merge_and_scan
from merge_and_scan import (
    update_rapi_files,
    get_rapi_ids,
    scan_duplicates_in_all,
    save_scan_report
)

def main():
    if not os.path.exists(ZYX_DIR):
        print(f"⚠ Folder {ZYX_DIR} tidak ditemukan.")
        return

    print("=" * 60)
    print("[STEP 1] PARSING & CONSOLIDATING ZYXX-ULTRA DATA")
    print("=" * 60)

    zyx_files = []
    for root, dirs, files in os.walk(ZYX_DIR):
        for f in files:
            if f.endswith(".json"):
                zyx_files.append(os.path.join(root, f))

    if not zyx_files:
        print("  ℹ Tidak ada file json baru ditemukan di ZYXX-ULTRA.")
        print("=" * 60)
        print("PROSES ZYXX-ULTRA SELESAI (0 FILE BARU).")
        print("=" * 60)
        return

    all_by_uid = {}
    couples = []
    zyx_acc_ids = set()

    for fpath in zyx_files:
        print(f"Reading {fpath}...")
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                items = []
                if content.startswith("["):
                    items = json.loads(content)
                elif content.startswith("{"):
                    items = [json.loads(content)]
                else:
                    for line in content.splitlines():
                        if line.strip():
                            items.append(json.loads(line.strip()))
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    if "couple_id" in item:
                        couples.append(item)
                        if "account1" in item and "account_id" in item["account1"]:
                            zyx_acc_ids.add(str(item["account1"]["account_id"]))
                        if "account2" in item and "account_id" in item["account2"]:
                            zyx_acc_ids.add(str(item["account2"]["account_id"]))
                        continue

                    uid = item.get("uid")
                    if "account_id" in item:
                        zyx_acc_ids.add(str(item["account_id"]))

                    if uid:
                        if uid not in all_by_uid:
                            all_by_uid[uid] = dict(item)
                        else:
                            all_by_uid[uid].update(item)
        except Exception as e:
            print(f"Error parsing file {fpath}: {e}")

    print(f"Total consolidated unique accounts from ZYXX-ULTRA: {len(all_by_uid)}")

    # 2. ACCOUNTS
    acc_path = os.path.join(ALL_DIR, "ACCOUNTS", "accounts-ID.json")
    os.makedirs(os.path.dirname(acc_path), exist_ok=True)
    existing_accs = load_json(acc_path) if os.path.exists(acc_path) else []
    existing_acc_uids = {x["uid"] for x in existing_accs if "uid" in x}

    added_acc_count = 0
    for uid, item in all_by_uid.items():
        if uid not in existing_acc_uids:
            std_acc = {
                "uid": item["uid"],
                "password": item.get("password", ""),
                "account_id": str(item.get("account_id", "")),
                "name": item.get("name", ""),
                "region": item.get("region", "ID"),
                "date_created": str(item.get("date_created", item.get("date_time", item.get("date_identified", "")))).split(".")[0],
                "thread_id": item.get("thread_id", 0)
            }
            existing_accs.append(std_acc)
            existing_acc_uids.add(uid)
            added_acc_count += 1

    save_json(acc_path, existing_accs)
    print(f"  → Merged {added_acc_count} new accounts to {acc_path}")

    # 3. UPDATE RAPI & SCAN
    if zyx_acc_ids:
        update_rapi_files(zyx_acc_ids)

    rapi_ids = get_rapi_ids()
    duplicates = scan_duplicates_in_all(rapi_ids)
    save_scan_report(duplicates)

    print("=" * 60)
    print("PROSES GABUNG & UPDATE ZYXX-ULTRA SELESAI!")
    print("=" * 60)

if __name__ == "__main__":
    main()
