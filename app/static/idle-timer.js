/**
 * Idle Timer Module - Auto-reset session after inactivity (PRD 4.1)
 * 
 * Usage: Import this script in all kiosk pages (landing, picker, adjust, confirmation)
 * - Timer resets on any user interaction (click, tap, drag, keypress, wheel)
 * - After IDLE_TIMEOUT (3 min), shows warning modal with COUNTDOWN_SECONDS (30s)
 * - "Saya masih di sini" button cancels reset
 * - If countdown expires, redirects to landing and clears frontend state
 * - Pages with confirmed order (has order_ref in URL) are EXEMPT from auto-reset
 */

const IDLE_TIMEOUT = 3 * 60 * 1000;
const COUNTDOWN_SECONDS = 30;
const RESET_URL = "/";

let idleTimer = null;
let countdownTimer = null;
let countdownSeconds = COUNTDOWN_SECONDS;
let isWarningShown = false;

function isConfirmedPage() {
    const params = new URLSearchParams(window.location.search);
    return params.has("order") && params.get("order").trim() !== "";
}

function isLandingPage() {
    return window.location.pathname === "/" || window.location.pathname === "/index.html";
}

function showWarningModal() {
    if (isWarningShown) return;
    isWarningShown = true;
    countdownSeconds = COUNTDOWN_SECONDS;

    let modal = document.getElementById("idle-warning-modal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "idle-warning-modal";
        modal.innerHTML = "<div class=\"idle-modal-overlay\"></div><div class=\"idle-modal-box\"><h2>\u23f0 Sesi akan direset</h2><p>Tidak ada aktivitas selama 3 menit.</p><p class=\"countdown\">Redirect dalam <span id=\"idle-countdown\">" + COUNTDOWN_SECONDS + "</span> detik...</p><button id=\"idle-keep-alive\" class=\"btn-primary\">Saya masih di sini</button></div>";
        document.body.appendChild(modal);

        const style = document.createElement("style");
        style.textContent = "#idle-warning-modal{position:fixed;top:0;left:0;right:0;bottom:0;z-index:10000;display:flex;align-items:center;justify-content:center;pointer-events:none}#idle-warning-modal .idle-modal-overlay{position:absolute;inset:0;background:rgba(0,0,0,0.7);pointer-events:auto}#idle-warning-modal .idle-modal-box{position:relative;background:var(--card,#1e1e2a);border:3px solid var(--accent,#e91e63);border-radius:16px;padding:32px 40px;text-align:center;max-width:90vw;pointer-events:auto;animation:idle-pop-in 0.3s ease-out}@keyframes idle-pop-in{from{transform:scale(0.8);opacity:0}to{transform:scale(1);opacity:1}}#idle-warning-modal h2{margin:0 0 12px;font-size:1.8rem;color:var(--accent,#e91e63)}#idle-warning-modal p{margin:8px 0;font-size:1.1rem;color:var(--text,#f0f0f5)}#idle-warning-modal .countdown{font-size:1.5rem;font-weight:bold;color:#ff6b6b}#idle-countdown{font-family:monospace}#idle-keep-alive{margin-top:24px;padding:14px 40px;font-size:1.2rem;font-weight:bold;border:none;border-radius:10px;background:var(--accent,#e91e63);color:#fff;cursor:pointer}#idle-keep-alive:hover{filter:brightness(1.1)}";
        document.head.appendChild(style);

        document.getElementById("idle-keep-alive").addEventListener("click", () => {
            hideWarningModal();
            resetIdleTimer();
        });
    }

    modal.style.display = "flex";
    startCountdown();
}

function hideWarningModal() {
    const modal = document.getElementById("idle-warning-modal");
    if (modal) modal.style.display = "none";
    isWarningShown = false;
    stopCountdown();
}

function startCountdown() {
    const countdownEl = document.getElementById("idle-countdown");
    if (!countdownEl) return;

    countdownTimer = setInterval(() => {
        countdownSeconds--;
        countdownEl.textContent = countdownSeconds;
        if (countdownSeconds <= 0) {
            performReset();
        }
    }, 1000);
}

function stopCountdown() {
    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }
}

function clearFrontendState() {
    sessionStorage.clear();
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith("session_") || key.startsWith("selection_") || key.startsWith("adjustment_"))) {
            keysToRemove.push(key);
        }
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
}

function performReset() {
    stopCountdown();
    hideWarningModal();
    clearFrontendState();
    window.location.href = RESET_URL;
}

function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer);
    if (isConfirmedPage()) return;
    if (isLandingPage()) return;
    idleTimer = setTimeout(() => {
        showWarningModal();
    }, IDLE_TIMEOUT);
}

function initIdleDetection() {
    const activityEvents = ["click", "mousedown", "keydown", "touchstart", "wheel", "mousemove", "scroll", "pointerdown"];
    activityEvents.forEach(event => {
        window.addEventListener(event, resetIdleTimer, { passive: true });
    });
    resetIdleTimer();
}

window.IdleTimer = {
    reset: resetIdleTimer,
    isConfirmed: isConfirmedPage,
    isLanding: isLandingPage,
    clearState: clearFrontendState,
    IDLE_TIMEOUT,
    COUNTDOWN_SECONDS
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initIdleDetection);
} else {
    initIdleDetection();
}