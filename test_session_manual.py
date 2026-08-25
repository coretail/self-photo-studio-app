"""Test manual validasi session (jalankan dengan venv python).

Menguji 3 skenario:
1. Session valid        -> 200
2. Session expired      -> 410
3. Session tidak ada    -> 404
"""

import json
import sqlite3
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# --- Skenario 3 (dilakukan duluan): session_code acak -> 404 ---
status, body = post("/api/sessions/validate", {"session_code": "SES-TIDAKADA"})
print("[TEST 3] session tidak ditemukan  ->", status)
print("         ", body)
assert status == 404, "harusnya 404"

# --- Buat session dummy (simulasi mesin foto studio) ---
status, body = post("/api/sessions/dummy?num_photos=4")
print("\n[SETUP ] buat dummy session      ->", status)
print("         ", body)
code = body["session_code"]

# --- Skenario 1: session valid -> 200 ---
status, body = post("/api/sessions/validate", {"session_code": code})
print("\n[TEST 1] session valid           ->", status)
print("         ", json.dumps(body, indent=2))
assert status == 200 and body["valid"] is True, "harusnya 200 valid"
assert len(body["photos"]) == 4, "harusnya 4 foto"

# --- Skenario 2: paksa expired langsung di DB lalu validate -> 410 ---
conn = sqlite3.connect("studio.db")
past = "2020-01-01 00:00:00.000000"
conn.execute(
    "UPDATE sessions SET expires_at = ? WHERE session_code = ?", (past, code)
)
conn.commit()
conn.close()

status, body = post("/api/sessions/validate", {"session_code": code})
print("\n[TEST 2] session expired          ->", status)
print("         ", body)
assert status == 410, "harusnya 410"

print("\nSEMUA TEST LULUS")
