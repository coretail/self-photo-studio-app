"""Test manual Preview & Adjust (Task 5).

Alur: dummy session -> select 4 foto -> GET selection ->
POST adjust-photos (valid) -> verifikasi tersimpan -> kasus error.
"""

import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# Setup
_, b = call("/api/sessions/dummy?num_photos=4", {})
code = b["session_code"]
print(f"[SETUP ] session {code}")
photos = [f"photo_{i:02d}.jpg" for i in range(1, 5)]
status, _ = call(f"/api/sessions/{code}/select-photos",
                 {"frame_id": 1, "filenames": photos})
print("[SETUP ] pilih 4 foto utk Strip  ->", status)
assert status == 200

# TEST 1: GET selection
status, sel = call(f"/api/sessions/{code}/selection")
print("\n[TEST 1] GET selection           ->", status, "frame", sel["frame_id"],
      "| adjustments:", sel["adjustments"])
assert status == 200 and sel["adjustments"] is None

# TEST 2: POST adjust valid
adj = [{"filename": n, "x": 100 + i * 10, "y": 200 + i * 450, "scale": 1.25}
       for i, n in enumerate(photos)]
status, body = call(f"/api/sessions/{code}/adjust-photos",
                    {"frame_id": 1, "adjustments": adj})
print("\n[TEST 2] POST adjust-photos      ->", status)
print("         ", body["message"])
assert status == 200 and body["saved"] == 4

# TEST 3: tersimpan di DB dan bisa dibaca kembali
status, sel = call(f"/api/sessions/{code}/selection")
a = sel["adjustments"][0]
print("\n[TEST 3] baca ulang adjustments  ->", status, json.dumps(a))
assert a["filename"] == "photo_01.jpg" and a["x"] == 100 and a["scale"] == 1.25

# TEST 4: adjustment tidak lengkap -> 400
bad = adj[:3]
status, body = call(f"/api/sessions/{code}/adjust-photos",
                    {"frame_id": 1, "adjustments": bad})
print("\n[TEST 4] adjustment kurang       ->", status)
print("         ", body["detail"])
assert status == 400

# TEST 5: frame_id tidak cocok -> 400
status, body = call(f"/api/sessions/{code}/adjust-photos",
                    {"frame_id": 2, "adjustments": adj})
print("\n[TEST 5] frame_id tidak cocok    ->", status)
assert status == 400

# TEST 6: halaman /adjust & fabric CDN terjangkau
with urllib.request.urlopen(BASE + "/adjust") as r:
    print("\n[TEST 6] GET /adjust             ->", r.status)
assert r.status == 200

print("\nSEMUA TEST LULUS")
