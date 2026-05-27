/* ─────────────────────────────────────────
   VibeCut — app.js
   Upload → Process → Poll → Result
   ───────────────────────────────────────── */

// ── CONFIG ───────────────────────────────
// Change this to your backend URL when deployed
const API_BASE = "http://localhost:8000";

// ── STATE ────────────────────────────────
let selectedVideo = null;
let selectedAudio = null;
let selectedTemplate = "hype";
let currentJobId = null;
let pollInterval = null;

// ── INIT ─────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // File input listeners
  document.getElementById("video-input").addEventListener("change", (e) => {
    handleFileSelect(e.target.files[0], "video");
  });
  document.getElementById("audio-input").addEventListener("change", (e) => {
    handleFileSelect(e.target.files[0], "audio");
  });

  // Template selection
  document.querySelectorAll(".template-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll(".template-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      selectedTemplate = card.dataset.template;
    });
  });

  // Drag-and-drop on upload zones
  setupDragDrop("video-zone", "video");
  setupDragDrop("audio-zone", "audio");
});

// ── FILE HANDLING ─────────────────────────
function handleFileSelect(file, type) {
  if (!file) return;

  if (type === "video") {
    selectedVideo = file;
    document.getElementById("video-name").textContent = truncate(file.name, 30);
    document.getElementById("video-name").classList.add("selected");
    document.getElementById("video-zone").classList.add("has-file");
  } else {
    selectedAudio = file;
    document.getElementById("audio-name").textContent = truncate(file.name, 30);
    document.getElementById("audio-name").classList.add("selected");
    document.getElementById("audio-zone").classList.add("has-file");
  }
}

function setupDragDrop(zoneId, type) {
  const zone = document.getElementById(zoneId);

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.style.borderColor = "var(--purple)";
  });

  zone.addEventListener("dragleave", () => {
    zone.style.borderColor = "";
  });

  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.style.borderColor = "";
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file, type);
      // Sync to the hidden input
      const dt = new DataTransfer();
      dt.items.add(file);
      document.getElementById(`${type}-input`).files = dt.files;
    }
  });
}

// ── PROCESS ──────────────────────────────
async function startProcessing() {
  if (!selectedVideo) {
    shake("video-zone");
    showToast("Please select a video file first");
    return;
  }
  if (!selectedAudio) {
    shake("audio-zone");
    showToast("Please select a music track first");
    return;
  }

  // Disable button
  const btn = document.getElementById("process-btn");
  btn.disabled = true;
  btn.querySelector(".btn-text").textContent = "⏳ UPLOADING…";

  // Show progress panel
  showSection("progress-section");
  setProgress(0, "Uploading files…");

  try {
    const formData = new FormData();
    formData.append("video", selectedVideo);
    formData.append("audio", selectedAudio);
    formData.append("template", selectedTemplate);

    const res = await fetch(`${API_BASE}/process`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }

    const data = await res.json();
    currentJobId = data.job_id;

    // Start polling
    btn.querySelector(".btn-text").textContent = "⏳ PROCESSING…";
    startPolling(currentJobId);
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.querySelector(".btn-text").textContent = "⚡ CREATE MY EDIT";
  }
}

// ── POLLING ───────────────────────────────
function startPolling(jobId) {
  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/status/${jobId}`);
      const data = await res.json();
      handleStatusUpdate(data);
    } catch (err) {
      console.error("Poll error:", err);
    }
  }, 2000);
}

function handleStatusUpdate(data) {
  const { status, progress, message, output_url, error } = data;

  setProgress(progress || 0, message || "Processing…");
  updateProgressSteps(progress || 0);

  if (status === "done") {
    clearInterval(pollInterval);
    showResult(output_url);
  } else if (status === "error") {
    clearInterval(pollInterval);
    showError(error || "Unknown error occurred");
  }
}

// ── PROGRESS UI ───────────────────────────
function setProgress(pct, message) {
  document.getElementById("progress-fill").style.width = `${pct}%`;
  document.getElementById("progress-pct").textContent = `${pct}%`;
  document.getElementById("progress-message").textContent = message;

  // Move glow dot
  const track = document.querySelector(".progress-track");
  const glow = document.getElementById("progress-glow");
  const trackWidth = track.offsetWidth;
  glow.style.left = `${(pct / 100) * trackWidth - 15}px`;
}

function updateProgressSteps(pct) {
  const steps = [
    { id: "pstep-beats",  threshold: 5,  done: 30 },
    { id: "pstep-scenes", threshold: 35, done: 48 },
    { id: "pstep-render", threshold: 50, done: 85 },
    { id: "pstep-grade",  threshold: 85, done: 99 },
  ];

  steps.forEach(({ id, threshold, done }) => {
    const el = document.getElementById(id);
    if (pct >= done) {
      el.classList.add("done");
      el.classList.remove("active");
    } else if (pct >= threshold) {
      el.classList.add("active");
      el.classList.remove("done");
    }
  });
}

// ── RESULT ───────────────────────────────
function showResult(outputUrl) {
  const videoEl = document.getElementById("result-video");
  const downloadBtn = document.getElementById("download-btn");

  const fullUrl = `${API_BASE}${outputUrl}`;
  videoEl.src = fullUrl;
  downloadBtn.href = `${API_BASE}/download/${currentJobId}`;

  showSection("result-section");
  document.getElementById("process-btn").disabled = false;
  document.getElementById("process-btn").querySelector(".btn-text").textContent = "⚡ CREATE MY EDIT";
}

// ── ERROR ────────────────────────────────
function showError(msg) {
  document.getElementById("error-message").textContent = msg;
  showSection("error-section");
  document.getElementById("process-btn").disabled = false;
  document.getElementById("process-btn").querySelector(".btn-text").textContent = "⚡ CREATE MY EDIT";
}

// ── RESET ────────────────────────────────
function resetApp() {
  selectedVideo = null;
  selectedAudio = null;
  currentJobId = null;

  if (pollInterval) clearInterval(pollInterval);

  // Reset file inputs
  document.getElementById("video-input").value = "";
  document.getElementById("audio-input").value = "";
  document.getElementById("video-name").textContent = "No file selected";
  document.getElementById("audio-name").textContent = "No file selected";
  document.getElementById("video-name").classList.remove("selected");
  document.getElementById("audio-name").classList.remove("selected");
  document.getElementById("video-zone").classList.remove("has-file");
  document.getElementById("audio-zone").classList.remove("has-file");

  // Reset progress
  setProgress(0, "Processing…");
  document.querySelectorAll(".pstep").forEach((s) => {
    s.classList.remove("active", "done");
  });

  // Hide result / error / progress
  hideSection("result-section");
  hideSection("error-section");
  hideSection("progress-section");

  document.getElementById("process-btn").disabled = false;
  document.getElementById("process-btn").querySelector(".btn-text").textContent = "⚡ CREATE MY EDIT";
}

// ── HELPERS ───────────────────────────────
function showSection(id) {
  const el = document.getElementById(id);
  el.style.display = "block";
  el.style.animation = "fadeSlideIn 0.4s ease";
}

function hideSection(id) {
  document.getElementById(id).style.display = "none";
}

function truncate(str, len) {
  return str.length > len ? str.slice(0, len - 3) + "…" : str;
}

function shake(id) {
  const el = document.getElementById(id);
  el.style.animation = "none";
  el.offsetHeight; // reflow
  el.style.animation = "shake 0.4s ease";
}

function showToast(msg) {
  let toast = document.createElement("div");
  toast.textContent = msg;
  Object.assign(toast.style, {
    position: "fixed", bottom: "32px", left: "50%",
    transform: "translateX(-50%)",
    background: "rgba(168,85,247,0.15)",
    border: "1px solid rgba(168,85,247,0.4)",
    color: "#fff",
    padding: "12px 24px",
    borderRadius: "10px",
    fontFamily: "'DM Sans', sans-serif",
    fontSize: "0.88rem",
    backdropFilter: "blur(10px)",
    zIndex: "999",
    animation: "fadeSlideIn 0.3s ease",
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ── KEYFRAMES (injected) ──────────────────
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes shake {
    0%,100% { transform: translateX(0); }
    25%      { transform: translateX(-8px); }
    75%      { transform: translateX(8px); }
  }
`;
document.head.appendChild(style);
