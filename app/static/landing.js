// Landing: validasi session -> pilih frame -> ke photo picker.

const sessionInput = document.getElementById("session-input");
const btnStart = document.getElementById("btn-start");
const errorMsg = document.getElementById("error-msg");
const stepSession = document.getElementById("step-session");
const stepFrame = document.getElementById("step-frame");
const okCode = document.getElementById("ok-code");
const frameList = document.getElementById("frame-list");

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove("hidden");
}

async function startSession() {
  const code = sessionInput.value.trim().toUpperCase();
  if (!code) {
    showError("Masukkan Session ID terlebih dahulu.");
    return;
  }

  btnStart.disabled = true;
  try {
    const res = await fetch("/api/sessions/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_code: code }),
    });
    const body = await res.json();

    if (res.status === 404) {
      showError(
        body.detail ||
          "Session tidak ditemukan. Periksa kembali atau hubungi operator."
      );
      return;
    }
    if (res.status === 410) {
      showError(
        "Session sudah kedaluwarsa. Silakan lakukan sesi foto ulang di studio."
      );
      return;
    }
    if (!res.ok) {
      showError(body.detail || "Terjadi kesalahan. Coba lagi.");
      return;
    }

    // Valid -> tampilkan langkah pemilihan frame
    okCode.textContent = code;
    stepSession.classList.add("hidden");
    stepFrame.classList.remove("hidden");
    loadFrames();
  } finally {
    btnStart.disabled = false;
  }
}

async function loadFrames() {
  const res = await fetch("/api/frames");
  const data = await res.json();
  for (const f of data.frames) {
    const card = document.createElement("div");
    card.className = "frame-card";
    card.innerHTML = `
      <div class="name">${f.name}</div>
      <div class="slots">${f.min_photos} foto</div>
      <div class="size">${(f.print_width_px / f.dpi).toFixed(1)}x${(
      f.print_height_px / f.dpi
    ).toFixed(1)} inch @${f.dpi}DPI</div>
    `;
    card.addEventListener("click", () => {
      const code = okCode.textContent;
      window.location.href = `/picker?session=${encodeURIComponent(
        code
      )}&frame=${f.id}`;
    });
    frameList.appendChild(card);
  }
}

btnStart.addEventListener("click", startSession);
sessionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") startSession();
});
