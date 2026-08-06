"""
merge_scan_update_rapi.py — Script lengkap untuk:
1. Auto-detect ID cantik baru (Tier SSS, SS, S, URUT) dari CGU-GEN-JAWA dan update ke RAPI (blinx.txt, rare.txt, all.txt)
2. Merge CGU-GEN-JAWA -> ALL (dedup by uid / couple_id)
3. Scan duplikat antara ALL dengan RAPI
4. Hapus folder CGU-GEN-JAWA jika sukses
"""

import json
import os
import sys
import shutil
import re
from purge_sold import purge_sold_accounts, get_sold_info

BASE   = "/root/max"
SRC    = os.path.join(BASE, "CGU-GEN-JAWA")
DST    = os.path.join(BASE, "ALL")
RAPI   = os.path.join(BASE, "RAPI")

# ─── Helpers ────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved {len(data)} entries → {path}")

EXCLUDED_RAPI_IDS = {"16732345502"}

def classify_rapi_id(account_id):
    """
    Kategori ID Cantik:
    - SSS TIER: 6x digit berulang berturut-turut (misal 666666, 888888, 333333)
    - SS TIER : 5x digit berulang berturut-turut (misal 88888, 00000, 77777, 99999)
    - URUT    : Digit berurutan (misal 0123, 1234, 2345, 3456, 4567, 5678, 6789)
    - S TIER  : 4x digit berulang berturut-turut (misal 1111, 2222, 3333, 4444, 5555, 7777, 8888, 9999, 0000)
    """
    s = str(account_id)
    sold_ids, _ = get_sold_info()
    if s in EXCLUDED_RAPI_IDS or s in sold_ids or len(s) < 10:
        return None

    # Check 6x repeat (SSS)
    if re.search(r"(\d)\1{5}", s):
        return "SSS"

    # Check 5x repeat (SS)
    if re.search(r"(\d)\1{4}", s):
        return "SS"

    # Check URUT (misal 45678, 0123, 1234, 5678, dll)
    sequences = ["01234", "12345", "23456", "34567", "45678", "56789", "0123", "1234", "2345", "3456", "4567", "5678", "6789"]
    for seq in sequences:
        if seq in s:
            return "URUT"

    # Check 4x repeat (S)
    if re.search(r"(\d)\1{3}", s):
        return "S"

    return None

def extract_all_ids_from_src(src_dir):
    """Kumpulkan semua account_id yang ada di CGU-GEN-JAWA."""
    extracted = set()
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".json"):
                fpath = os.path.join(root, f)
                try:
                    data = load_json(fpath)
                    for item in data:
                        if isinstance(item, dict):
                            if "account_id" in item:
                                extracted.add(str(item["account_id"]))
                            if "account1" in item and "account_id" in item["account1"]:
                                extracted.add(str(item["account1"]["account_id"]))
                            if "account2" in item and "account_id" in item["account2"]:
                                extracted.add(str(item["account2"]["account_id"]))
                except Exception:
                    pass
    return extracted

def read_rapi_txt(filepath):
    """Membaca isi file txt RAPI."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

def write_rapi_txt(filepath, lines):
    """Menulis isi file txt RAPI."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def update_rapi_files(new_ids, sync_spin=None):
    """Update blinx.txt, rare.txt, dan all.txt jika menemukan ID cantik baru."""
    blinx_path = os.path.join(RAPI, "blinx.txt")
    rare_path  = os.path.join(RAPI, "rare.txt")
    all_path   = os.path.join(RAPI, "all.txt")

    blinx_lines = read_rapi_txt(blinx_path)
    rare_lines  = read_rapi_txt(rare_path)

    existing_blinx = {line.strip() for line in blinx_lines if re.match(r"^\d{10,}$", line.strip())}
    existing_rare  = {line.strip() for line in rare_lines if re.match(r"^\d{10,}$", line.strip())}

    added_blinx = []
    added_rare  = []

    for acc_id in new_ids:
        cat = classify_rapi_id(acc_id)
        if cat in ["SSS", "SS", "URUT"]:
            if acc_id not in existing_blinx:
                added_blinx.append((cat, acc_id))
                existing_blinx.add(acc_id)
        elif cat == "S":
            if acc_id not in existing_rare:
                added_rare.append(acc_id)
                existing_rare.add(acc_id)

    # Insert added_blinx to blinx.txt
    if added_blinx:
        print(f"\n✨ Menambahkan {len(added_blinx)} ID cantik baru ke blinx.txt:")
        for cat, acc_id in added_blinx:
            print(f"   + [{cat}] {acc_id}")
            blinx_lines.append(acc_id)

        # Re-sort blinx sections numerically
        sss_list, ss_list, urut_list = [], [], []
        seqs = [
            "012345", "123456", "234567", "345678", "456789", "567890",
            "01234", "12345", "23456", "34567", "45678", "56789",
            "0123", "1234", "2345", "3456", "4567", "5678", "6789"
        ]
        for line in blinx_lines:
            s = line.strip()
            if s in EXCLUDED_RAPI_IDS:
                continue
            if re.match(r"^\d{10,}$", s):
                if re.search(r"(\d)\1{5}", s):
                    if s not in sss_list: sss_list.append(s)
                elif re.search(r"(\d)\1{4}", s):
                    if s not in ss_list: ss_list.append(s)
                elif any(sq in s for sq in seqs):
                    if s not in urut_list: urut_list.append(s)

        out = []
        out.append("--- SSS TIER (6x digit berulang) ---")
        out.extend(sorted(list(set(sss_list))))
        out.append("")
        out.append("")
        out.append("--- SS TIER (5x digit berulang) ---")
        out.extend(sorted(list(set(ss_list))))
        out.append("")
        out.append("")
        out.append("--- (URUT) ---")
        out.extend(sorted(list(set(urut_list))))

        write_rapi_txt(blinx_path, out)
    else:
        print("\n  ✓ Tidak ada ID cantik SSS/SS/URUT baru untuk blinx.txt")

    # Insert added_rare to rare.txt
    if added_rare:
        print(f"\n✨ Menambahkan {len(added_rare)} ID cantik baru (Tier S) ke rare.txt:")
        for acc_id in added_rare:
            print(f"   + [S] {acc_id}")
            rare_lines.append(acc_id)

        rare_ids = [line.strip() for line in rare_lines if re.match(r"^\d{10,}$", line.strip())]
        rare_sorted = sorted(list(set(rare_ids)))
        write_rapi_txt(rare_path, rare_sorted)
    else:
        print("  ✓ Tidak ada ID cantik Tier S baru untuk rare.txt")

    # Re-build all.txt with sections (gabungan SSS, SS, URUT, dan S TIER)
    all_blinx_lines = read_rapi_txt(blinx_path)
    all_rare_lines  = read_rapi_txt(rare_path)

    sss_list, ss_list, urut_list, s_list = [], [], [], []
    seqs = [
        "012345", "123456", "234567", "345678", "456789", "567890",
        "01234", "12345", "23456", "34567", "45678", "56789",
        "0123", "1234", "2345", "3456", "4567", "5678", "6789"
    ]

    for line in all_blinx_lines:
        s = line.strip()
        if s in EXCLUDED_RAPI_IDS:
            continue
        if re.match(r"^\d{10,}$", s):
            if re.search(r"(\d)\1{5}", s):
                if s not in sss_list: sss_list.append(s)
            elif re.search(r"(\d)\1{4}", s):
                if s not in ss_list: ss_list.append(s)
            elif any(sq in s for sq in seqs):
                if s not in urut_list: urut_list.append(s)

    for line in all_rare_lines:
        s = line.strip()
        if re.match(r"^\d{10,}$", s):
            if re.search(r"(\d)\1{3}", s):
                if s not in s_list and s not in sss_list and s not in ss_list:
                    s_list.append(s)

    all_out = []
    all_out.append("--- SSS TIER (6x digit berulang) ---")
    all_out.extend(sorted(list(set(sss_list))))
    all_out.append("")
    all_out.append("")
    all_out.append("--- SS TIER (5x digit berulang) ---")
    all_out.extend(sorted(list(set(ss_list))))
    all_out.append("")
    all_out.append("")
    all_out.append("--- (URUT) ---")
    all_out.extend(sorted(list(set(urut_list))))
    all_out.append("")
    all_out.append("")
    all_out.append("--- S TIER (4x digit berulang) ---")
    all_out.extend(sorted(list(set(s_list))))

    write_rapi_txt(all_path, all_out)
    tot_all = len(set(sss_list) | set(ss_list) | set(urut_list) | set(s_list))
    print(f"  ✓ Updated all.txt (total: {tot_all} target ID di RAPI)")
    rebuild_rapi_data_json(sync_spin=sync_spin)

def rebuild_rapi_data_json(sync_spin=None):
    """Rebuild RAPI/data.json from ALL/ matching RAPI IDs and sync to /root/spin/gajah and dark."""
    rapi_ids = set()
    for fname in ["blinx.txt", "rare.txt", "all.txt"]:
        fpath = os.path.join(RAPI, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if re.match(r"^\d{10,}$", s):
                        rapi_ids.add(s)

    all_dir = DST
    tokens_by_uid = {}
    tokens_path = os.path.join(all_dir, "TOKENS", "tokens-ID.json")
    if os.path.exists(tokens_path):
        for t in load_json(tokens_path):
            if "uid" in t:
                tokens_by_uid[t["uid"]] = t.get("jwt_token")

    found_accounts = {}
    hunter_dir = os.path.join(all_dir, "HUNTER")
    if os.path.exists(hunter_dir):
        for f in sorted(os.listdir(hunter_dir)):
            if f.endswith(".json"):
                fpath = os.path.join(hunter_dir, f)
                for item in load_json(fpath):
                    aid = str(item.get("account_id", ""))
                    if aid in rapi_ids and aid not in found_accounts:
                        obj = dict(item)
                        obj["source_file"] = f"ALL/HUNTER/{f}"
                        if obj.get("uid") in tokens_by_uid and not obj.get("jwt_token"):
                            obj["jwt_token"] = tokens_by_uid[obj["uid"]]
                        found_accounts[aid] = obj

    rare_path = os.path.join(all_dir, "RARE", "rare-ID.json")
    if os.path.exists(rare_path):
        for item in load_json(rare_path):
            aid = str(item.get("account_id", ""))
            if aid in rapi_ids and aid not in found_accounts:
                obj = dict(item)
                obj["source_file"] = "ALL/RARE/rare-ID.json"
                if obj.get("uid") in tokens_by_uid and not obj.get("jwt_token"):
                    obj["jwt_token"] = tokens_by_uid[obj["uid"]]
                found_accounts[aid] = obj

    acc_path = os.path.join(all_dir, "ACCOUNTS", "accounts-ID.json")
    if os.path.exists(acc_path):
        for item in load_json(acc_path):
            aid = str(item.get("account_id", ""))
            if aid in rapi_ids and aid not in found_accounts:
                obj = dict(item)
                obj["source_file"] = "ALL/ACCOUNTS/accounts-ID.json"
                if obj.get("uid") in tokens_by_uid and not obj.get("jwt_token"):
                    obj["jwt_token"] = tokens_by_uid[obj["uid"]]
                found_accounts[aid] = obj

    result_list = list(found_accounts.values())
    data_json_path = os.path.join(RAPI, "data.json")
    save_json(data_json_path, result_list)

    if sync_spin is None:
        sync_spin = os.environ.get("SYNC_SPIN", "").lower() in ["1", "true", "y", "yes"]

    if sync_spin:
        for spin_dst in ["/root/spin/gajah", "/root/spin/dark", "/root/spin/spin-gajah"]:
            if os.path.exists(spin_dst):
                dst_file = os.path.join(spin_dst, "data.json")
                save_json(dst_file, result_list)
                print(f"  ✓ Synced data.json → {spin_dst}")
    else:
        print("  ℹ Upload/sync ke spin dilewati.")

    # Auto update web catalog and push to GitHub for Vercel deployment
    auto_push_web_stock()

    return len(result_list)

def update_web_stock_data():
    """Generates stock/stock_data.js from RAPI/all.txt and RAPI/sold.txt."""
    try:
        api_dir = os.path.join(BASE, "api")
        if api_dir not in sys.path:
            sys.path.append(api_dir)
        from stock import load_all_stock
        items = load_all_stock()
        js_content = "window.STOCK_DATA = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n"
        web_stock_path = os.path.join(BASE, "stock", "stock_data.js")
        with open(web_stock_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"  ✓ Re-generated stock/stock_data.js ({len(items)} stock items)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to update stock/stock_data.js: {e}")
        return False

def auto_push_web_stock():
    """Auto commits and pushes changes to GitHub for Vercel deployment."""
    try:
        update_web_stock_data()
        os.system(f"cd {BASE} && git add .")
        status = os.popen(f"cd {BASE} && git status --porcelain").read().strip()
        if status:
            commit_msg = "Auto update stock_data.js & RAPI catalog [Vercel Push]"
            os.system(f'cd {BASE} && git commit -m "{commit_msg}"')
            push_res = os.system(f"cd {BASE} && git push origin main")
            if push_res == 0:
                print("  🚀 Successfully pushed changes to GitHub (Vercel deployment auto-triggered)!")
            else:
                print("  ❌ Git push failed.")
        else:
            print("  ℹ No changes detected for git commit.")
    except Exception as e:
                print(f"  ❌ Auto push error: {e}")

def merge_by_uid(dst_path, src_path, key="uid"):
    """Merge src JSON array into dst JSON array, dedup by key."""
    dst_data = load_json(dst_path) if os.path.exists(dst_path) else []
    src_data = load_json(src_path)

    existing_keys = {item[key] for item in dst_data if key in item}
    added = 0
    for item in src_data:
        k = item.get(key)
        if k not in existing_keys:
            dst_data.append(item)
            existing_keys.add(k)
            added += 1

    save_json(dst_path, dst_data)
    print(f"    → Merged {added} new / {len(src_data) - added} duplicates skipped (key={key})")
    return added

def merge_hunter(dst_dir, src_dir):
    """Merge hunter-XX.json files: match by number, dedup by uid."""
    src_files = [f for f in os.listdir(src_dir) if f.endswith(".json")]
    total_added = 0
    for fname in src_files:
        src_path  = os.path.join(src_dir,  fname)
        dst_path  = os.path.join(dst_dir,  fname)
        print(f"  Merging hunter file: {fname}")
        added = merge_by_uid(dst_path, src_path, key="uid")
        total_added += added
    return total_added

# ─── Ambil semua account_id dari RAPI/*.txt ──────────────────────────────────

def get_rapi_ids():
    """Kumpulkan semua account_id (numeric strings) dari file txt di RAPI."""
    ids = set()
    for fname in os.listdir(RAPI):
        if fname.endswith(".txt"):
            fpath = os.path.join(RAPI, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if re.match(r"^\d{10,}$", line):
                        ids.add(line)
    print(f"  → {len(ids)} account_id unik ditemukan di RAPI/")
    return ids

def scan_duplicates_in_all(rapi_ids):
    """Scan ALL/ untuk account yang sudah ada di RAPI."""
    duplicates = {}

    # Scan ACCOUNTS
    acc_path = os.path.join(DST, "ACCOUNTS", "accounts-ID.json")
    if os.path.exists(acc_path):
        data = load_json(acc_path)
        dupes = [item for item in data if str(item.get("account_id","")) in rapi_ids]
        if dupes:
            duplicates["ACCOUNTS"] = dupes
            print(f"  ⚠ {len(dupes)} duplikat ditemukan di ACCOUNTS (sudah ada di RAPI)")

    # Scan RARE
    rare_path = os.path.join(DST, "RARE", "rare-ID.json")
    if os.path.exists(rare_path):
        data = load_json(rare_path)
        dupes = [item for item in data if str(item.get("account_id","")) in rapi_ids]
        if dupes:
            duplicates["RARE"] = dupes
            print(f"  ⚠ {len(dupes)} duplikat ditemukan di RARE (sudah ada di RAPI)")

    # Scan TOKENS
    tok_path = os.path.join(DST, "TOKENS", "tokens-ID.json")
    if os.path.exists(tok_path):
        data = load_json(tok_path)
        dupes = [item for item in data if str(item.get("account_id","")) in rapi_ids]
        if dupes:
            duplicates["TOKENS"] = dupes
            print(f"  ⚠ {len(dupes)} duplikat ditemukan di TOKENS (sudah ada di RAPI)")

    # Scan HUNTER
    hunter_dir = os.path.join(DST, "HUNTER")
    if os.path.exists(hunter_dir):
        hunter_dupes = []
        for fname in os.listdir(hunter_dir):
            if fname.endswith(".json"):
                data = load_json(os.path.join(hunter_dir, fname))
                for item in data:
                    if str(item.get("account_id","")) in rapi_ids:
                        hunter_dupes.append({"file": fname, **item})
        if hunter_dupes:
            duplicates["HUNTER"] = hunter_dupes
            print(f"  ⚠ {len(hunter_dupes)} duplikat ditemukan di HUNTER (sudah ada di RAPI)")

    # Scan COUPLES
    couples_path = os.path.join(DST, "COUPLES", "couples-ID.json")
    if os.path.exists(couples_path):
        data = load_json(couples_path)
        dupes = []
        for item in data:
            a1 = str(item.get("account1", {}).get("account_id", ""))
            a2 = str(item.get("account2", {}).get("account_id", ""))
            if a1 in rapi_ids or a2 in rapi_ids:
                dupes.append(item)
        if dupes:
            duplicates["COUPLES"] = dupes
            print(f"  ⚠ {len(dupes)} duplikat ditemukan di COUPLES (sudah ada di RAPI)")

    return duplicates

def save_scan_report(duplicates):
    """Simpan laporan duplikat ke file."""
    report_path = os.path.join(BASE, "scan_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_duplicate_categories": len(duplicates),
            "summary": {k: len(v) for k, v in duplicates.items()},
            "details": duplicates
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 Laporan scan disimpan → {report_path}")

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Selalu jalankan purge akun sold di awal
    purge_sold_accounts()

    if not os.path.exists(SRC):
        print(f"⚠ Folder {SRC} tidak ditemukan.")
        print("Silakan taruh/upload folder CGU-GEN-JAWA di /root/max/ terlebih dahulu.")
        return

    print("=" * 60)
    print("[TUGAS 1] DETEKSI & UPDATE TARGET RAPI (BLINX, RARE, ALL)")
    print("=" * 60)

    try:
        new_ids = extract_all_ids_from_src(SRC)
        print(f"Kumpulkan {len(new_ids)} ID unik dari {SRC}...")
        update_rapi_files(new_ids)
        print("✅ TUGAS 1 SELESAI — Auto-update RAPI berhasil!")
    except Exception as e:
        print(f"❌ TUGAS 1 GAGAL: {e}")
        import traceback; traceback.print_exc()

    print("\n" + "=" * 60)
    print("[TUGAS 2] MERGE CGU-GEN-JAWA → ALL")
    print("=" * 60)

    task2_ok = True
    try:
        # 2a. ACCOUNTS
        print("\n[2a] Merging ACCOUNTS...")
        src = os.path.join(SRC, "ACCOUNTS", "accounts-ID.json")
        dst = os.path.join(DST, "ACCOUNTS", "accounts-ID.json")
        if os.path.exists(src):
            merge_by_uid(dst, src, key="uid")

        # 2b. COUPLES
        print("\n[2b] Merging COUPLES...")
        src = os.path.join(SRC, "COUPLES", "couples-ID.json")
        dst = os.path.join(DST, "COUPLES", "couples-ID.json")
        if os.path.exists(src):
            merge_by_uid(dst, src, key="couple_id")

        # 2c. HUNTER
        print("\n[2c] Merging HUNTER...")
        src_hunter = os.path.join(SRC, "HUNTER")
        dst_hunter = os.path.join(DST, "HUNTER")
        if os.path.exists(src_hunter):
            merge_hunter(dst_hunter, src_hunter)

        # 2d. RARE
        print("\n[2d] Merging RARE...")
        src = os.path.join(SRC, "RARE", "rare-ID.json")
        dst = os.path.join(DST, "RARE", "rare-ID.json")
        if os.path.exists(src):
            merge_by_uid(dst, src, key="uid")

        # 2e. TOKENS
        print("\n[2e] Merging TOKENS...")
        src = os.path.join(SRC, "TOKENS", "tokens-ID.json")
        dst = os.path.join(DST, "TOKENS", "tokens-ID.json")
        if os.path.exists(src):
            merge_by_uid(dst, src, key="uid")

        print("\n✅ TUGAS 2 SELESAI — Merge berhasil!")

    except Exception as e:
        print(f"\n❌ TUGAS 2 GAGAL: {e}")
        import traceback; traceback.print_exc()
        task2_ok = False

    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[TUGAS 3] SCAN DUPLIKAT (ALL vs RAPI)")
    print("=" * 60)

    task3_ok = True
    try:
        print("\nMengumpulkan account_id dari RAPI/...")
        rapi_ids = get_rapi_ids()

        print("\nScanning ALL/ untuk duplikat dengan RAPI/...")
        duplicates = scan_duplicates_in_all(rapi_ids)

        total_dupes = sum(len(v) for v in duplicates.values())
        print(f"\n⚠ Total {total_dupes} entri RAPI ditemukan di folder ALL/.")

        save_scan_report(duplicates)
        print("\n✅ TUGAS 3 SELESAI — Scan RAPI selesai!")

    except Exception as e:
        print(f"\n❌ TUGAS 3 GAGAL: {e}")
        import traceback; traceback.print_exc()
        task3_ok = False

    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[TUGAS 4] HAPUS CGU-GEN-JAWA")
    print("=" * 60)

    if task2_ok and task3_ok:
        try:
            shutil.rmtree(SRC)
            print(f"\n✅ TUGAS 4 SELESAI — Folder CGU-GEN-JAWA berhasil dihapus!")
        except Exception as e:
            print(f"\n❌ TUGAS 4 GAGAL: {e}")
    else:
        print("\n⚠ Tugas 4 dilewati karena tugas sebelumnya belum selesai.")

    print("\n" + "=" * 60)
    print("SEMUA PROSES SELESAI")
    print("=" * 60)

if __name__ == "__main__":
    main()
