/* Confirmation page: render ringkasan order dari query params. */

const params = new URLSearchParams(window.location.search);

document.getElementById("order-ref").textContent = params.get("order") || "-";
document.getElementById("sum-session").textContent = params.get("session") || "-";

// Nama frame diambil dari API agar akurat
const frameId = params.get("frame");
if (frameId) {
  fetch(`/api/frames/${frameId}`)
    .then((r) => (r.ok ? r.json() : null))
    .then((f) => {
      if (f) document.getElementById("sum-frame").textContent = f.name;
    });
}

document.getElementById("sum-time").textContent = new Date().toLocaleString("id-ID");
document.getElementById("sum-status").textContent = "COMPLETED";

const previewUrl = params.get("preview");
if (previewUrl) {
  const img = document.getElementById("preview-img");
  img.src = previewUrl;
}
