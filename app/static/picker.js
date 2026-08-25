/* Photo picker logic - vanilla JS, tanpa dependency. */

const params = new URLSearchParams(window.location.search);
const sessionCode = params.get("session");
const frameId = parseInt(params.get("frame") || "1", 10);

const grid = document.getElementById("grid");
const counterEl = document.getElementById("counter");
const hintEl = document.getElementById("hint");
const btnLanjut = document.getElementById("btn-lanjut");
const errorMsg = document.getElementById("error-msg");
const sessionInfo = document.getElementById("session-info");

let minPhotos = 1;
let maxPhotos = 1;
const selected = new Set();

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

function updateCounter() {
  counterEl.textContent = `${selected.size}/${maxPhotos}`;
  btnLanjut.disabled = !(selected.size >= minPhotos && selected.size <= maxPhotos);
  if (selected.size < minPhotos) {
    hintEl.textContent = `Pilih minimal ${minPhotos} foto.`;
  } else if (selected.size > maxPhotos) {
    hintEl.textContent = `Maksimal ${maxPhotos} foto. Hapus beberapa pilihan.`;
  } else {
    hintEl.textContent = "Jumlah sudah sesuai. Tekan Lanjut untuk melanjutkan.";
  }
}

function toggleSelect(filename) {
  // Kunci maksimum: tidak boleh pilih lebih dari max slot (sesuai PRD 4.2)
  if (!selected.has(filename) && selected.size >= maxPhotos) {
    updateCounter();
    return;
  }
  if (selected.has(filename)) {
    selected.delete(filename);
  } else {
    selected.add(filename);
  }
  const card = document.querySelector(`[data-filename="${filename}"]`);
  card.classList.toggle("selected", selected.has(filename));
  updateCounter();
}

async function init() {
  if (!sessionCode) {
    showError("Session code tidak ada. Buka via /picker?session=SES-XXXX&frame=1");
    return;
  }

  // Ambil info frame untuk batas min/max
  try {
    const res = await fetch(`/api/frames/${frameId}`);
    if (!res.ok) throw new Error("frame tidak ditemukan");
    const frame = await res.json();
    minPhotos = frame.min_photos;
    maxPhotos = frame.max_photos;
    sessionInfo.textContent =
      `Session ${sessionCode} | Frame: ${frame.name} (${minPhotos}-${maxPhotos} foto)`;
  } catch {
    showError(`Frame dengan id ${frameId} tidak ditemukan.`);
    return;
  }

  // Ambil daftar foto session
  const res = await fetch(`/api/sessions/${sessionCode}/photos`);
  if (!res.ok) {
    const err = await res.json();
    showError(err.detail || "Gagal memuat foto.");
    return;
  }
  const data = await res.json();

  for (const photo of data.photos) {
    const card = document.createElement("div");
    card.className = "photo-card";
    card.dataset.filename = photo.filename;

    const img = document.createElement("img");
    img.src = photo.url;
    img.alt = photo.filename;
    img.loading = "lazy";

    const check = document.createElement("span");
    check.className = "checkmark";
    check.textContent = "\u2713";

    card.append(img, check);
    card.addEventListener("click", () => toggleSelect(photo.filename));
    grid.appendChild(card);
  }
  updateCounter();
}

btnLanjut.addEventListener("click", async () => {
  btnLanjut.disabled = true;
  const res = await fetch(`/api/sessions/${sessionCode}/select-photos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ frame_id: frameId, filenames: [...selected] }),
  });
  const body = await res.json();
  if (!res.ok) {
    showError(body.detail || "Gagal menyimpan pilihan.");
    btnLanjut.disabled = false;
    return;
  }
  alert(`Pilihan tersimpan!\n\n${body.message}`);
  // Lanjut ke tahap Preview & Adjust
  window.location.href = `/adjust?session=${encodeURIComponent(sessionCode)}&frame=${frameId}`;
});

init();
