"""Test manual photo picker endpoints (Task 4).

Skenario:
1. GET /api/sessions/{code}/photos  -> 200, list foto + url
2. POST select-photos kurang dari min -> 400
3. POST select-photos sesuai jumlah   -> 200 tersimpan
4. POST select-photos lebih dari max  -> 400
5. GET /media/... foto pertama        -> 200 (static serving)
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def request(path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# Setup: buat session dummy 6 foto
status, body = request("/api/sessions/dummy?num_photos=6", {})
body = json.loads(body)
code = body["session_code"]
print(f"[SETUP ] dummy session {code} dengan {body['num_photos']} foto")

# TEST 1: list photos
status, raw = request(f"/api/sessions/{code}/photos")
data = json.loads(raw)
print("\n[TEST 1] list photos              ->", status, f"({len(data['photos'])} foto)")
print("          contoh:", json.dumps(data["photos"][0]))
assert status == 200 and len(data["photos"]) == 6

# TEST 2: Strip (id=1) butuh 4 foto, pilih 2 -> ditolak
status, body = request(
    f"/api/sessions/{code}/select-photos",
    {"frame_id": 1, "filenames": ["photo_01.jpg", "photo_02.jpg"]},
)
print("\n[TEST 2] pilih 2 foto utk Strip   ->", status)
print("         ", body["detail"])
assert status == 400 and "kurang" in body["detail"]

# TEST 3: pilih tepat 4 -> diterima
status, body = request(
    f"/api/sessions/{code}/select-photos",
    {"frame_id": 1, "filenames": ["photo_01.jpg", "photo_02.jpg",
                                   "photo_03.jpg", "photo_04.jpg"]},
)
body = json.loads(body)
print("\n[TEST 3] pilih 4 foto utk Strip   ->", status)
print("         ", body["message"])
assert status == 200

# TEST 4: 4R (id=2) hanya 1 slot, pilih 2 -> ditolak
status, body = request(
    f"/api/sessions/{code}/select-photos",
    {"frame_id": 2, "filenames": ["photo_01.jpg", "photo_02.jpg"]},
)
print("\n[TEST 4] pilih 2 foto utk 4R      ->", status)
print("         ", body["detail"])
assert status == 400 and "melebihi" in body["detail"]

# TEST 5: static file serving via /media
with urllib.request.urlopen(BASE + f"/media/sessions/{code}/photo_01.jpg") as r:
    status = r.status
print("\n[TEST 5] GET /media/...jpg        ->", status)
assert status == 200

print("\nSEMUA TEST LULUS")
