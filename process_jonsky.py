"""
process_jonsky.py — Standardize and merge JONSKY-ACC into /root/max/ALL and /root/max/RAPI

Steps:
1. Parse JSONL files in /root/decode/JONSKY-ACC/ and consolidate per unique UID.
2. Standardize objects for:
   - ALL/ACCOUNTS/accounts-ID.json: [ {uid, password, account_id, name, region, date_created, thread_id}, ... ]
   - ALL/TOKENS/tokens-ID.json: [ {uid, account_id, jwt_token, name, password, date_time, region, thread_id}, ... ]
   - ALL/RARE/rare-ID.json (if score >= 20): [ {uid, password, account_id, name, region, rarity_type, rarity_score, reason, date_identified, jwt_token, thread_id}, ... ]
   - ALL/HUNTER/hunter-XX.json (if score >= 12): [ {uid, password, account_id, name, region, rarity_type, rarity_score, reason, date_identified, jwt_token, thread_id}, ... ]
3. Run update_rapi_files on new account_ids to update RAPI (blinx.txt, rare.txt, all.txt) and scan duplicates.
"""

import json
import os
import re

JONSKY_DIRS = ["/root/jon/JONSKY-ACC", "/root/decode/JONSKY-ACC", "/root/jonn/JONSKY-ACC"]
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
from merge_and_scan import extract_all_ids_from_src, update_rapi_files, get_rapi_ids, save_scan_report

def get_date_str(item):
    d = item.get("date_identified") or item.get("date_time") or ""
    return str(d).split(".")[0]

def main():
    print("=" * 60)
    print("[STEP 1] PARSING & CONSOLIDATING JONSKY-ACC DATA")
    print("=" * 60)

    jonsky_files = []
    found_dirs = []
    for j_dir in JONSKY_DIRS:
        if os.path.exists(j_dir):
            found_dirs.append(j_dir)
            for root, dirs, files in os.walk(j_dir):
                for f in files:
                    if f.endswith(".json"):
                        jonsky_files.append(os.path.join(root, f))

    if not jonsky_files:
        print("No JONSKY-ACC files found in /root/jon or /root/decode.")
        return

    all_by_uid = {}
    for fpath in jonsky_files:
        print(f"Reading {fpath}...")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                continue
            items = []
            if content.startswith("["):
                try:
                    items = json.loads(content)
                except Exception as e:
                    print(f"Error parsing json array in {fpath}: {e}")
            else:
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except Exception as e:
                        print(f"Error parsing line in {fpath}: {e}")
            for obj in items:
                uid = obj.get("uid")
                if uid is not None:
                    if uid not in all_by_uid:
                        all_by_uid[uid] = dict(obj)
                    else:
                        all_by_uid[uid].update(obj)

    print(f"Total consolidated unique accounts from JONSKY-ACC: {len(all_by_uid)}")

    print("\n" + "=" * 60)
    print("[STEP 2] MERGING TO ALL/ACCOUNTS & ALL/TOKENS")
    print("=" * 60)

    # 2a. ACCOUNTS
    acc_path = os.path.join(ALL_DIR, "ACCOUNTS", "accounts-ID.json")
    existing_accs = load_json(acc_path) if os.path.exists(acc_path) else []
    existing_acc_uids = {x["uid"] for x in existing_accs}

    added_acc_count = 0
    for uid, item in all_by_uid.items():
        if uid not in existing_acc_uids:
            std_acc = {
                "uid": item["uid"],
                "password": item.get("password", ""),
                "account_id": str(item.get("account_id", "")),
                "name": item.get("name", ""),
                "region": item.get("region", "ID"),
                "date_created": get_date_str(item),
                "thread_id": item.get("thread_id", 0)
            }
            existing_accs.append(std_acc)
            existing_acc_uids.add(uid)
            added_acc_count += 1

    save_json(acc_path, existing_accs)
    print(f"  → Merged {added_acc_count} new accounts to {acc_path}")

    # 2b. TOKENS
    tok_path = os.path.join(ALL_DIR, "TOKENS", "tokens-ID.json")
    existing_toks = load_json(tok_path) if os.path.exists(tok_path) else []
    existing_tok_uids = {x["uid"] for x in existing_toks}

    added_tok_count = 0
    for uid, item in all_by_uid.items():
        if uid not in existing_tok_uids and item.get("jwt_token"):
            std_tok = {
                "uid": item["uid"],
                "account_id": str(item.get("account_id", "")),
                "jwt_token": item.get("jwt_token", ""),
                "name": item.get("name", ""),
                "password": item.get("password", ""),
                "date_time": get_date_str(item),
                "region": item.get("region", "ID"),
                "thread_id": item.get("thread_id", 0)
            }
            existing_toks.append(std_tok)
            existing_tok_uids.add(uid)
            added_tok_count += 1

    save_json(tok_path, existing_toks)
    print(f"  → Merged {added_tok_count} new tokens to {tok_path}")

    print("\n" + "=" * 60)
    print("[STEP 3] MERGING TO ALL/RARE & ALL/HUNTER")
    print("=" * 60)

    # 3a. RARE (for score >= 20)
    rare_path = os.path.join(ALL_DIR, "RARE", "rare-ID.json")
    existing_rares = load_json(rare_path) if os.path.exists(rare_path) else []
    existing_rare_uids = {x["uid"] for x in existing_rares}

    added_rare_count = 0
    for uid, item in all_by_uid.items():
        score = item.get("rarity_score", 0)
        if score >= 20 and uid not in existing_rare_uids:
            std_rare = {
                "uid": item["uid"],
                "password": item.get("password", ""),
                "account_id": str(item.get("account_id", "")),
                "name": item.get("name", ""),
                "region": item.get("region", "ID"),
                "rarity_type": item.get("rarity_level", "RARE"),
                "rarity_score": item.get("rarity_score", 0),
                "reason": item.get("reason", ""),
                "date_identified": get_date_str(item),
                "jwt_token": item.get("jwt_token", ""),
                "thread_id": item.get("thread_id", 0)
            }
            existing_rares.append(std_rare)
            existing_rare_uids.add(uid)
            added_rare_count += 1

    save_json(rare_path, existing_rares)
    print(f"  → Merged {added_rare_count} new rare items to {rare_path}")

    # 3a-2. BONUS (3-digit urut / bonus accounts)
    bonus_path = os.path.join(ALL_DIR, "BONUS", "bonus-ID.json")
    os.makedirs(os.path.dirname(bonus_path), exist_ok=True)
    existing_bonuses = load_json(bonus_path) if os.path.exists(bonus_path) else []
    existing_bonus_uids = {x["uid"] for x in existing_bonuses}

    added_bonus_count = 0
    seqs_3only = ["012", "123", "234", "345", "456", "567", "678", "789", "890", "987", "876", "765", "654", "543", "432", "321", "210", "098"]
    for uid, item in all_by_uid.items():
        acc_id = str(item.get("account_id", ""))
        if any(sq in acc_id for sq in seqs_3only) and uid not in existing_bonus_uids:
            std_bonus = {
                "uid": item["uid"],
                "password": item.get("password", ""),
                "account_id": acc_id,
                "name": item.get("name", ""),
                "region": item.get("region", "ID"),
                "rarity_type": "BONUS",
                "rarity_score": item.get("rarity_score", 0),
                "reason": item.get("reason", ""),
                "date_identified": get_date_str(item),
                "jwt_token": item.get("jwt_token", ""),
                "thread_id": item.get("thread_id", 0)
            }
            existing_bonuses.append(std_bonus)
            existing_bonus_uids.add(uid)
            added_bonus_count += 1

    save_json(bonus_path, existing_bonuses)
    print(f"  → Merged {added_bonus_count} new bonus items to {bonus_path}")

    # 3b. HUNTER (for score >= 12)
    hunter_dir = os.path.join(ALL_DIR, "HUNTER")
    os.makedirs(hunter_dir, exist_ok=True)

    hunter_groups = {}
    for uid, item in all_by_uid.items():
        score = item.get("rarity_score", 0)
        if score >= 12:
            fname = f"hunter-{score}.json"
            if fname not in hunter_groups:
                hunter_groups[fname] = []
            std_hunter = {
                "uid": item["uid"],
                "password": item.get("password", ""),
                "account_id": str(item.get("account_id", "")),
                "name": item.get("name", ""),
                "region": item.get("region", "ID"),
                "rarity_type": item.get("rarity_level", "RARE"),
                "rarity_score": item.get("rarity_score", 0),
                "reason": item.get("reason", ""),
                "date_identified": get_date_str(item),
                "jwt_token": item.get("jwt_token", ""),
                "thread_id": item.get("thread_id", 0)
            }
            hunter_groups[fname].append(std_hunter)

    for fname, new_items in sorted(hunter_groups.items()):
        h_path = os.path.join(hunter_dir, fname)
        existing_h = load_json(h_path) if os.path.exists(h_path) else []
        existing_h_uids = {x["uid"] for x in existing_h}
        added_h = 0
        for item in new_items:
            if item["uid"] not in existing_h_uids:
                existing_h.append(item)
                existing_h_uids.add(item["uid"])
                added_h += 1
        save_json(h_path, existing_h)
        print(f"  → {fname}: Merged {added_h} new items (total: {len(existing_h)})")

    print("\n" + "=" * 60)
    print("[STEP 4] UPDATE TARGET RAPI & SCAN DUPLICATES")
    print("=" * 60)

    # Extract all account_ids from JONSKY-ACC
    all_jonsky_acc_ids = {str(item["account_id"]) for item in all_by_uid.values() if "account_id" in item}
    print(f"Extracted {len(all_jonsky_acc_ids)} unique account_ids from JONSKY-ACC")

    # Auto-detect and update blinx.txt, rare.txt, all.txt
    update_rapi_files(all_jonsky_acc_ids)

    # Scan duplicates via fast text matching to avoid memory overhead
    rapi_ids = get_rapi_ids()
    print("  ✓ RAPI IDs loaded for scan check.")
    print("\n" + "=" * 60)
    print("PROSES GABUNG & UPDATE JONSKY-ACC SELESAI!")
    print("=" * 60)

    # Clean up JONSKY-ACC directories after successful merge
    import shutil
    for j_dir in found_dirs:
        if os.path.exists(j_dir):
            shutil.rmtree(j_dir)
            print(f"  ✓ Folder {j_dir} berhasil dihapus setelah merge!")

if __name__ == "__main__":
    main()
