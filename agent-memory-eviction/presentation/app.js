// Player for the offline presentation: scales the 1280×720 stage, advances scenes on a
// timer (or after spoken narration when a Persian voice exists), and renders the heatmap.

const NARR = window.NARRATION;
const fa = n => n.toLocaleString("fa-IR");

// ---------- Table 1 of the paper as a heatmap (% of OPT at B = 10%) ----------
const HEAT = {
  cols: ["ایستا", "محلیت زمانی", "نادر-حیاتی", "رانش", "دستیار ترکیبی", "میانگین"],
  rows: [
    ["Random", [36.9, 71.5, 35.0, 36.7, 37.5, 43.5]],
    ["FIFO", [37.0, 88.2, 36.6, 35.7, 40.2, 47.6]],
    ["LFU", [48.0, 19.7, 49.1, 44.0, 34.9, 39.1]],
    ["LRU", [49.9, 90.1, 50.9, 48.6, 56.3, 59.2]],
    ["Ebbinghaus", [56.2, 82.4, 55.0, 51.1, 58.7, 60.7]],
    ["ImpDecay", [68.2, 79.0, 70.4, 64.0, 75.9, 71.5]],
    ["GenAgents", [64.1, 90.6, 67.7, 61.8, 80.6, 72.9]],
    ["GDS", [72.1, 90.6, 74.2, 68.3, 83.3, 77.7]],
    ["VRS (ما)", [76.8, 78.5, 78.6, 73.8, 82.4, 78.0], true],
    ["VRS+C (ما)", [82.5, 81.8, 82.9, 79.3, 85.3, 82.4], true],
  ],
};
(function buildHeatmap() {
  const el = document.getElementById("heatmap");
  if (!el) return;
  let h = '<table class="heat"><thead><tr><th class="p">روش</th>' + HEAT.cols.map(c => "<th>" + c + "</th>").join("") + "</tr></thead><tbody>";
  for (const [name, vals, ours] of HEAT.rows) {
    h += "<tr" + (ours ? ' class="ours"' : "") + '><th class="p">' + name + "</th>" +
      vals.map(v => '<td style="--v:' + v + '">' + v.toFixed(1) + "</td>").join("") + "</tr>";
  }
  el.innerHTML = h + "</tbody></table>";
})();

// ---------- player ----------
const scenes = [...document.querySelectorAll(".scene")];
if (scenes.length !== NARR.length) console.warn("scene/narration count mismatch", scenes.length, NARR.length);

const $ = id => document.getElementById(id);
const progress = $("progress"), playBtn = $("play"), overlay = $("overlay");
const sub = $("subtitle"), subTitle = $("subtitle-title"), timeEl = $("time");
const speedSel = $("speed"), voiceBtn = $("voice"), voiceNote = $("voicenote");

const DUR = NARR.map(t => Math.max(12, t.length / 15));   // seconds, by reading speed
const TOTAL = DUR.reduce((a, b) => a + b, 0);
let cur = 0, playing = false, elapsed = 0, last = 0, voiceOn = false, faVoice = null, speaking = false;

scenes.forEach((s, i) => {
  const b = document.createElement("button");
  b.type = "button"; b.className = "seg";
  b.setAttribute("aria-label", "صحنه " + fa(i + 1) + ": " + s.dataset.title);
  b.innerHTML = "<i></i>"; b.onclick = () => go(i);
  progress.appendChild(b);

  const c = document.createElement("button");
  c.type = "button"; c.textContent = fa(i + 1) + ". " + s.dataset.title; c.onclick = () => go(i);
  $("chapters").appendChild(c);

  const p = document.createElement("p");
  p.innerHTML = "<b>" + fa(i + 1) + ". " + s.dataset.title + "</b><br>" + NARR[i];
  $("transcript").appendChild(p);
});
const segs = [...progress.children];
const chaps = [...$("chapters").children];

function fit() {
  const vp = $("viewport");
  const k = vp.clientWidth / 1280;
  $("stage").style.transform = "scale(" + k + ")";
  vp.style.height = (720 * k) + "px";
}
addEventListener("resize", fit);
document.addEventListener("fullscreenchange", fit);
fit();

const mmss = s => fa(Math.floor(s / 60)) + ":" + fa(Math.floor(s % 60)).padStart(2, "۰");

function show(i) {
  scenes.forEach(s => s.classList.remove("active"));
  void scenes[i].offsetWidth;                 // restart CSS animations
  scenes[i].classList.add("active");
  sub.textContent = NARR[i];
  subTitle.textContent = "صحنه " + fa(i + 1) + " از " + fa(scenes.length) + " · " + scenes[i].dataset.title;
  segs.forEach((s, j) => { s.firstChild.style.width = j < i ? "100%" : "0"; });
  chaps.forEach((c, j) => c.classList.toggle("on", j === i));
  try { localStorage.setItem("amep-scene", String(i)); } catch (e) { /* storage unavailable */ }
}
function go(i) {
  cur = Math.max(0, Math.min(scenes.length - 1, i));
  elapsed = 0;
  show(cur);
  if (playing && voiceOn) speak();
}
function speak() {
  if (!faVoice) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(NARR[cur]);
  u.voice = faVoice; u.lang = faVoice.lang; u.rate = Number(speedSel.value);
  speaking = true;
  u.onend = () => {
    speaking = false;
    if (playing && voiceOn) { if (cur < scenes.length - 1) go(cur + 1); else setPlaying(false); }
  };
  speechSynthesis.speak(u);
}
function setPlaying(p) {
  playing = p;
  playBtn.textContent = p ? "⏸ توقف" : "▶ پخش";
  overlay.hidden = p;
  if (p) { last = performance.now(); if (voiceOn) speak(); requestAnimationFrame(tick); }
  else if ("speechSynthesis" in window) { speechSynthesis.cancel(); speaking = false; }
}
function tick(now) {
  if (!playing) return;
  const dt = (now - last) / 1000; last = now;
  if (!(voiceOn && speaking)) elapsed += dt * Number(speedSel.value);
  const d = DUR[cur];
  segs[cur].firstChild.style.width = Math.min(100, elapsed / d * 100) + "%";
  const done = DUR.slice(0, cur).reduce((a, b) => a + b, 0) + Math.min(elapsed, d);
  timeEl.textContent = mmss(done) + " / " + mmss(TOTAL);
  if (!voiceOn && elapsed >= d) {
    if (cur < scenes.length - 1) go(cur + 1); else { setPlaying(false); return; }
  }
  requestAnimationFrame(tick);
}

playBtn.onclick = () => setPlaying(!playing);
$("bigplay").onclick = () => setPlaying(true);
$("next").onclick = () => go(cur + 1);
$("prev").onclick = () => go(cur - 1);
$("fullscreen").onclick = () => {
  const vp = $("viewport");
  if (document.fullscreenElement) document.exitFullscreen();
  else if (vp.requestFullscreen) vp.requestFullscreen().catch(() => {});
};
addEventListener("keydown", e => {
  if (e.target.closest("select")) return;
  if (e.code === "Space") { e.preventDefault(); setPlaying(!playing); }
  if (e.key === "ArrowLeft") go(cur + 1);     // RTL: left = forward
  if (e.key === "ArrowRight") go(cur - 1);
});

function findVoice() {
  faVoice = speechSynthesis.getVoices().find(v => /^fa/i.test(v.lang)) || null;
  voiceBtn.disabled = !faVoice;
  if (!faVoice) voiceNote.textContent = "این سیستم صدای فارسی ندارد؛ زیرنویس هر صحنه زیر تصویر نمایش داده می‌شود. کلیدها: Space پخش/توقف، ← صحنه بعد، → صحنه قبل.";
}
if ("speechSynthesis" in window) { findVoice(); speechSynthesis.onvoiceschanged = findVoice; }
else voiceBtn.disabled = true;
voiceBtn.onclick = () => {
  voiceOn = !voiceOn;
  voiceBtn.textContent = voiceOn ? "روایت صوتی: روشن" : "روایت صوتی: خاموش";
  if (playing) { if (voiceOn) speak(); else { speechSynthesis.cancel(); speaking = false; } }
};

let start = 0;
try { start = Number(localStorage.getItem("amep-scene")) || 0; } catch (e) { /* storage unavailable */ }
const q = Number(new URLSearchParams(location.search).get("scene"));   // e.g. index.html?scene=14
if (q >= 1) start = q - 1;
cur = Math.min(start, scenes.length - 1);
show(cur);
timeEl.textContent = "مدت تقریبی: " + fa(Math.round(TOTAL / 60)) + " دقیقه";
