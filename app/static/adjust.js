/* Preview & Adjust - Fabric.js canvas dengan slot frame + clipping.
   Koordinat internal = pixel cetak (print_width_px x print_height_px),
   tampilan diskalakan via CSS sehingga render tetap tajam dan cepat. */

const params = new URLSearchParams(window.location.search);
const sessionCode = params.get("session");
const frameId = parseInt(params.get("frame") || "1", 10);

const errorMsg = document.getElementById("error-msg");
const sessionInfo = document.getElementById("session-info");
const activeSlotEl = document.getElementById("active-slot");
const btnConfirm = document.getElementById("btn-confirm");

const canvas = new fabric.Canvas("frame-canvas", {
  selection: false,
  preserveObjectStacking: true,
});

// Layout slot: strip = N slot vertikal; frame 1 slot = satu area penuh.
function computeSlots(frameW, frameH, numSlots) {
  const slots = [];
  const slotH = frameH / numSlots;
  for (let i = 0; i < numSlots; i++) {
    slots.push({ left: 0, top: i * slotH, width: frameW, height: slotH });
  }
  return slots;
}

// Skala minimum agar foto selalu menutupi slot penuh (tidak ada celah).
function coverScale(img, slot) {
  return Math.max(slot.width / img.width, slot.height / img.height);
}

// Jepit posisi supaya tepi foto tidak pernah masuk ke dalam area slot.
function clampToSlot(img, slot) {
  const w = img.width * img.scaleX;
  const h = img.height * img.scaleY;
  // origin default fabric = center; konversi ke sudut kiri-atas
  const left = img.left - w / 2;
  const top = img.top - h / 2;
  const minLeft = slot.left + slot.width - w;
  const minTop = slot.top + slot.height - h;
  img.left = Math.min(Math.max(left, minLeft), slot.left) + w / 2;
  img.top = Math.min(Math.max(top, minTop), slot.top) + h / 2;
}

let slots = [];
let images = [];

function bindImageEvents(img, slot) {
  // Nonaktifkan rotate & resize handle (PRD: hanya drag & zoom)
  img.set({
    hasControls: false,
    hasBorders: false,
    lockRotation: true,
    lockScalingX: true,
    lockScalingY: true,
  });

  img.on("moving", () => clampToSlot(img, slot));
  img.on("mousedown", () => {
    activeSlotEl.textContent = `Slot ${slots.indexOf(slot) + 1}/${slots.length}`;
  });
}

function applyZoom(img, zoom, slotIdx) {
  const minScale = coverScale(img, slots[slotIdx]);
  img.scale(Math.max(minScale, Math.min(zoom, minScale * 4)));
  clampToSlot(img, slots[slotIdx]);
  canvas.requestRenderAll();
}

// Zoom via wheel (mouse) pada objek aktif
canvas.on("mouse:wheel", (opt) => {
  const idx = images.indexOf(opt.target);
  if (idx === -1) return;
  const zoom = opt.target.scaleX * (opt.e.deltaY > 0 ? 0.95 : 1.05);
  applyZoom(opt.target, zoom, idx);
  opt.e.preventDefault();
  opt.e.stopPropagation();
});

// Zoom via pinch (layar sentuh kiosk): dua jari, rasio jarak = skala
let lastPinchDist = 0;
canvas.upperCanvasEl.addEventListener(
  "touchmove",
  (e) => {
    if (e.touches.length !== 2) return;
    e.preventDefault();
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    const dist = Math.hypot(dx, dy);
    const img = canvas.getActiveObject();
    const idx = images.indexOf(img);
    if (idx !== -1 && lastPinchDist > 0) {
      applyZoom(img, img.scaleX * (dist / lastPinchDist), idx);
      lastPinchDist = dist;
    } else if (idx !== -1) {
      lastPinchDist = dist;
    }
  },
  { passive: false }
);
canvas.upperCanvasEl.addEventListener("touchend", () => (lastPinchDist = 0));

// Muat foto terpilih ke slot + tombol Konfirmasi
async function init() {
  if (!sessionCode) {
    errorMsg.textContent = "Session code tidak ada. Buka via /adjust?session=SES-XXXX&frame=1";
    errorMsg.classList.remove("hidden");
    return;
  }

  const fRes = await fetch(`/api/frames/${frameId}`);
  if (!fRes.ok) {
    errorMsg.textContent = "Frame tidak ditemukan.";
    errorMsg.classList.remove("hidden");
    return;
  }
  const frame = await fRes.json();
  const numSlots = frame.min_photos; // jumlah slot = jumlah foto wajib
  slots = computeSlots(frame.print_width_px, frame.print_height_px, numSlots);
  canvas.setWidth(frame.print_width_px);
  canvas.setHeight(frame.print_height_px);
  sessionInfo.textContent =
    `Session ${sessionCode} | ${frame.name} (${frame.print_width_px}x${frame.print_height_px}px @${frame.dpi}DPI)`;

  // Foto terpilih (urutan tersimpan di backend)
  const selRes = await fetch(`/api/sessions/${sessionCode}/selection`);
  const selectedNames = selRes.ok
    ? (await selRes.json()).selected_photos
    : [];

  // Muat semua gambar paralel agar render awal cepat (< 1 detik)
  const t0 = performance.now();
  await Promise.all(
    selectedNames.map(
      (name, idx) =>
        new Promise((resolve) => {
          fabric.Image.fromURL(
            `/media/sessions/${sessionCode}/${name}`,
            (img) => {
              img._filename = name;
              const slot = slots[idx];
              img.set({
                left: slot.left + slot.width / 2,
                top: slot.top + slot.height / 2,
              });
              img.scale(coverScale(img, slot));
              // Clip: foto hanya terlihat di dalam area slotnya
              img.clipPath = new fabric.Rect({
                left: slot.left,
                top: slot.top,
                width: slot.width,
                height: slot.height,
                absolutePositioned: true,
              });
              bindImageEvents(img, slot);
              images[idx] = img;
              resolve();
            }
          );
        })
    )
  );

  // Outline slot sebagai background (tidak interaktif)
  const bgRects = slots.map(
    (s) =>
      new fabric.Rect({
        left: s.left,
        top: s.top,
        width: s.width,
        height: s.height,
        fill: "#2a2a38",
        stroke: "#666",
        strokeWidth: 3,
        selectable: false,
        evented: false,
      })
  );

  canvas.add(...bgRects, ...images.filter(Boolean));
  canvas.requestRenderAll(); // satu kali render setelah semua siap
  console.log(`Render awal selesai dalam ${(performance.now() - t0).toFixed(0)} ms`);
}

btnConfirm.addEventListener("click", async () => {
  btnConfirm.disabled = true;
  const adjustments = images.filter(Boolean).map((img) => ({
    filename: img._filename,
    x: Math.round(img.left),
    y: Math.round(img.top),
    scale: Number(img.scaleX.toFixed(4)),
  }));
  // 1. Simpan penyesuaian posisi/zoom
  const res = await fetch(`/api/sessions/${sessionCode}/adjust-photos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ frame_id: frameId, adjustments }),
  });
  const body = await res.json();
  if (!res.ok) {
    errorMsg.textContent = body.detail || "Gagal menyimpan penyesuaian.";
    errorMsg.classList.remove("hidden");
    btnConfirm.disabled = false;
    return;
  }
  // 2. Generate file cetak final via confirm endpoint
  const confirmRes = await fetch(`/api/sessions/${sessionCode}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const confirmBody = await confirmRes.json();
  if (!confirmRes.ok) {
    errorMsg.textContent = confirmBody.detail || "Gagal membuat file cetak.";
    errorMsg.classList.remove("hidden");
    btnConfirm.disabled = false;
    return;
  }
  // 3. Redirect ke halaman konfirmasi dengan data lengkap
  window.location.href =
    `/confirmation?session=${encodeURIComponent(sessionCode)}` +
    `&order=${encodeURIComponent(confirmBody.order_ref)}` +
    `&frame=${frameId}&preview=${encodeURIComponent(confirmBody.output_url)}`;
});

init();


