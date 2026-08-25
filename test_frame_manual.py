"""Test manual katalog frame & validasi pemilihan foto.

Skenario:
1. GET /api/frames                -> 3 frame aktif
2. GET /api/frames/{id}           -> detail Strip
3. GET /api/frames/999            -> 404
4. Validate selection:
   a. Strip + 4 foto  -> valid
   b. Strip + 2 foto  -> invalid (kurang dari min)
   c. 4R    + 2 foto  -> invalid (lebih dari max)
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path: str):
    try:
        with urllib.request.urlopen(BASE + path) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def post(path: str, body: dict):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read())


# TEST 1: list frames
status, body = get("/api/frames")
print("[TEST 1] list frames              ->", status)
for f in body["frames"]:
    print(f"          {f['id']}. {f['name']}: {f['min_photos']}-{f['max_photos']} foto, "
          f"{f['print_width_px']}x{f['print_height_px']}px @{f['dpi']}DPI")
assert status == 200 and body["count"] == 3

# TEST 2: detail frame id=1
status, body = get("/api/frames/1")
print("\n[TEST 2] detail frame id=1        ->", status)
print("         ", json.dumps(body))
assert status == 200 and body["name"] == "Strip"

# TEST 3: detail frame tidak ada
status, body = get("/api/frames/999")
print("\n[TEST 3] detail frame id=999      ->", status)
print("         ", body)
assert status == 404

# TEST 4a: Strip butuh tepat 4 foto
status, body = post("/api/frames/1/validate-selection", {"selected_photo_count": 4})
print("\n[TEST 4a] Strip + 4 foto          ->", status, body["valid"])
print("         ", body["message"])
assert body["valid"] is True

# TEST 4b: Strip dengan 2 foto -> kurang dari minimum
status, body = post("/api/frames/1/validate-selection", {"selected_photo_count": 2})
print("\n[TEST 4b] Strip + 2 foto          ->", status, body["valid"])
print("         ", body["message"])
assert body["valid"] is False and "kurang" in body["message"]

# TEST 4c: 4R hanya 1 slot, diberi 2 foto -> lebih dari maksimum
status, body = post("/api/frames/2/validate-selection", {"selected_photo_count": 2})
print("\n[TEST 4c] 4R + 2 foto             ->", status, body["valid"])
print("         ", body["message"])
assert body["valid"] is False and "melebihi" in body["message"]

print("\nSEMUA TEST LULUS")
