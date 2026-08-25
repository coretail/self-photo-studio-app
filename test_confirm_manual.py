"""Test manual end-to-end Task 6: session -> pilih -> adjust -> confirm.

Memverifikasi:
1. POST /confirm membuat Order + file JPEG di data/outputs/
2. Foto benar-benar ter-crop & terposisi (dicek per-piksel dengan warna
   solid dari dummy photos), bukan foto utuh asal ditempel.
"""

import json
import sqlite3
import urllib.request
from PIL import Image

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


# SETUP: dummy 4 foto -> pilih utk Strip -> adjust posisi khusus
_, b = call("/api/sessions/dummy?num_photos=4", {})
code = b["session_code"]
photos = [f"photo_{i:02d}.jpg" for i in range(1, 5)]
call(f"/api/sessions/{code}/select-photos", {"frame_id": 1, "filenames": photos})

# Strip: 600x1800, slot i => top = i*450. Foto 600x800.
# Pilih offset yang jelas: foto_01 digeser kanan-bawah penuh satu slot,
# zoom 2x supaya area terlihat jelas berbeda dari pas-fungsi cover.
adjustments = [
    {"filename": "photo_01.jpg", "x": 300 + 200, "y": 225 + 150, "scale": 2.0},
    {"filename": "photo_02.jpg", "x": 300, "y": 675, "scale": 0.75},   # cover min
    {"filename": "photo_03.jpg", "x": 300 - 250, "y": 1125 - 200, "scale": 1.5},
    {"filename": "photo_04.jpg", "x": 300, "y": 1575, "scale": 1.0},
]
status, _ = call(f"/api/sessions/{code}/adjust-photos",
                 {"frame_id": 1, "adjustments": adjustments})
print("[SETUP ] adjust-photos           ->", status)
assert status == 200

# TEST 1: confirm
status, body = call(f"/api/sessions/{code}/confirm", {})
print("\n[TEST 1] POST confirm            ->", status)
print("         ", json.dumps({k: v for k, v in body.items() if k != 'session_code'}, indent=1))
assert status == 200
ref = body["order_ref"]

import pathlib
out = pathlib.Path(body["output_file_path"])
print("\n[TEST 2] file JPEG ada           ->", out.is_file(), out.stat().st_size, "bytes")
assert out.is_file()

img = Image.open(out)
print("[TEST 3] dimensi & DPI           ->", img.size, img.info.get("dpi"))
assert img.size == (600, 1800)
dpi = img.info.get("dpi", (0,))[0]
assert abs(dpi - 300) < 1

# TEST 4: verifikasi crop/posisi per piksel.
# Warna dummy: photo_01=merah(220,60,60), dst. Slot 0 (y 0-450):
# foto merah center=(500,375) scale=2.0 -> ukuran 1200x1600.
# Foto melampaui batas slot (cover full), jadi seluruh slot berwarna merah.
px0 = img.getpixel((100, 100))
px1 = img.getpixel((500, 400))
print("\n[TEST 4] slot0 (100,100):", px0, "| slot0 (500,400):", px1)
def near(c, t, tol=12): return all(abs(a - b) <= tol for a, b in zip(c, t))
assert near(px0, (220, 60, 60)), "foto merah harus menutupi seluruh slot (scale 2x)"
assert near(px1, (220, 60, 60)), "foto merah harus menutupi seluruh slot (scale 2x)"

# Slot 1 (y 450-900): foto hijau(60,160,80) center=(300,675) scale=0.75 -> 450x600.
# topleft foto = (75, 375). Slot 1 top = 450.
# Foto mulai y=375 (75 px di ATAS slot 1). Jadi seluruh slot 1 tertutup hijau.
# Cek tepi atas slot (y=460 = 10px dari atas slot) -> photo_y = 460-375 = 85 (dalam foto)
# Cek tengah slot (y=890 = 440px dari atas slot) -> photo_y = 890-375 = 515 (dalam foto)
px_top = img.getpixel((300, 460))  # slot 1, y=10 dari atas slot
px_mid = img.getpixel((300, 890)) # slot 1, y=440 dari atas slot
print("[TEST 5] slot1 top(300,460):", px_top, "| mid(300,890):", px_mid)
assert near(px_top, (60, 160, 80)), "atas slot 1 harus hijau (foto menutupi seluruh slot)"
assert near(px_mid, (60, 160, 80)), "tengah slot 1 harus hijau"

# TEST 6: order tersimpan di DB dgn status completed
conn = sqlite3.connect("studio.db")
row = conn.execute(
    "SELECT order_ref, status FROM orders WHERE order_ref=?", (ref,)
).fetchone()
conn.close()
print("\n[TEST 6] record orders           ->", row)
assert row == (ref, "completed")

# TEST 7: confirm tanpa adjustment -> 400
_, b = call("/api/sessions/dummy?num_photos=2", {})
status, body = call(f"/api/sessions/{b['session_code']}/confirm", {})
print("\n[TEST 7] confirm tanpa adjust    ->", status)
print("         ", body["detail"])
assert status == 400

# TEST 8: preview bisa diakses via /media
with urllib.request.urlopen(BASE + f"/media/outputs/{ref}.jpg") as r:
    print("\n[TEST 8] GET /media/outputs/...  ->", r.status)
assert r.status == 200

print("\nSEMUA TEST LULUS")
