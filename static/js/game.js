// Front-end game loop: build a quest, fight through the questions, show results.

const $ = (id) => document.getElementById(id);
const screens = { start: $("screen-start"), battle: $("screen-battle"), result: $("screen-result") };
const WRONG_DAMAGE = 15;

let mode = "text";
let quest = null;
let monster = null;
let lastPlayer = { level: 1 };
let levelAtStart = 1;

function show(name) {
  for (const k in screens) screens[k].hidden = k !== name;
}

// ---------- HUD ----------
async function loadPlayer() {
  const p = await (await fetch("/api/player")).json();
  renderHud(p);
}
function renderHud(p) {
  lastPlayer = p;
  $("hud-level").textContent = p.level;
  $("hud-won").textContent = p.battles_won;
  $("hud-acc").textContent = p.accuracy + "%";
  const pct = p.xp_for_level ? Math.min(100, (p.xp_into_level / p.xp_for_level) * 100) : 0;
  $("hud-xp-fill").style.width = pct + "%";
  $("hud-xp-label").textContent = `${p.xp_into_level} / ${p.xp_for_level} XP`;
}

// ---------- mode tabs ----------
document.querySelectorAll(".mode-tab").forEach((tab) => {
  tab.onclick = () => {
    mode = tab.dataset.mode;
    document.querySelectorAll(".mode-tab").forEach((t) => t.classList.toggle("active", t === tab));
    $("pane-text").hidden = mode !== "text";
    $("pane-pdf").hidden = mode !== "pdf";
    $("pane-topic").hidden = mode !== "topic";
  };
});

$("in-pdf").onchange = () => {
  const f = $("in-pdf").files[0];
  const drop = document.querySelector(".filedrop");
  if (f) { $("pdf-label").textContent = f.name; drop.classList.add("ready"); }
};

// ---------- start a quest ----------
$("btn-start").onclick = startQuest;

function jsonPost(obj) {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) };
}
function showErr(msg) { const e = $("start-err"); e.textContent = msg; e.hidden = false; }
function overlay(on, text) { if (text) $("overlay-text").textContent = text; $("overlay").hidden = !on; }

async function startQuest() {
  $("start-err").hidden = true;
  let opts, busyText = "Summoning your quest...";

  if (mode === "pdf") {
    const f = $("in-pdf").files[0];
    if (!f) return showErr("Choose a PDF first.");
    const fd = new FormData();
    fd.append("mode", "pdf");
    fd.append("file", f);
    opts = { method: "POST", body: fd };
    busyText = "Reading your PDF...";
  } else if (mode === "topic") {
    const topic = $("in-topic").value.trim();
    if (!topic) return showErr("Type a topic to research.");
    opts = jsonPost({ mode: "topic", topic });
    busyText = "Researching the web...";
  } else {
    const text = $("in-text").value.trim();
    if (text.length < 50) return showErr("Add a few more sentences to study from.");
    opts = jsonPost({ mode: "text", text });
  }

  overlay(true, busyText);
  try {
    const res = await fetch("/api/quest", opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    beginBattle(data);
  } catch (e) {
    showErr(e.message);
  } finally {
    overlay(false);
  }
}

// ---------- battle ----------
function setSprite(id, rows, scale) {
  const wrap = $(id);
  wrap.innerHTML = "";
  wrap.appendChild(window.Sprites.draw(rows, scale));
}
function setBar(id, pct) { $(id).style.width = Math.max(0, Math.min(100, pct)) + "%"; }

function beginBattle(data) {
  quest = data.quest;
  monster = window.Sprites.randomMonster();
  levelAtStart = lastPlayer.level;
  setSprite("monster-sprite", monster.rows, 13);
  setSprite("player-sprite", window.Sprites.scholar, 11);
  $("monster-name").textContent = monster.name;
  setBar("monster-hp", 100);
  setBar("player-hp", 100);
  show("battle");
  renderQuestion(data.question);
}

function renderQuestion(q) {
  $("feedback").hidden = true;
  $("q-progress").textContent = `${q.index + 1} / ${q.total}`;
  $("q-diff").textContent = "DIFF " + "*".repeat(q.difficulty);
  $("q-text").textContent = q.question;
  const box = $("options");
  box.innerHTML = "";
  q.options.forEach((opt) => {
    const b = document.createElement("button");
    b.className = "opt";
    b.textContent = opt;
    b.onclick = () => answer(opt, b);
    box.appendChild(b);
  });
}

async function answer(choice, btn) {
  document.querySelectorAll(".opt").forEach((o) => (o.disabled = true));
  overlay(true, "Resolving turn...");
  let data;
  try {
    data = await (await fetch("/api/answer", jsonPost({ choice }))).json();
  } catch (e) {
    overlay(false);
    document.querySelectorAll(".opt").forEach((o) => (o.disabled = false));
    return;
  }
  overlay(false);

  document.querySelectorAll(".opt").forEach((o) => {
    if (o.textContent === data.answer) o.classList.add("correct");
    else if (o === btn && !data.correct) o.classList.add("wrong");
  });

  if (data.correct) {
    hit("monster-sprite");
    floater(`-${data.damage}`, "dmg");
    setBar("monster-hp", (data.monster_hp / quest.monster_hp_max) * 100);
  } else {
    flashArena();
    floater(`-${WRONG_DAMAGE}`, "ouch");
    setBar("player-hp", (data.player_hp / quest.player_hp_max) * 100);
  }
  showFeedback(data);
}

function showFeedback(data) {
  $("feedback").hidden = false;
  const v = $("verdict");
  v.textContent = data.correct ? "HIT! Critical knowledge!" : "MISS!";
  v.className = "verdict " + (data.correct ? "good" : "bad");
  $("explain").textContent = data.explanation || "";
  const tutor = $("tutor");
  if (data.tutor) { tutor.hidden = false; $("tutor-text").textContent = data.tutor; }
  else tutor.hidden = true;

  const nb = $("btn-next");
  if (data.finished) {
    nb.textContent = "SEE RESULTS";
    nb.onclick = () => showResult(data);
  } else {
    nb.textContent = "CONTINUE";
    nb.onclick = () => renderQuestion(data.question);
  }
}

// ---------- animations ----------
function replay(el, cls) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); }
function hit(id) { replay($(id), "hit"); }
function flashArena() { replay(document.querySelector(".arena"), "flash"); }
function floater(text, cls) {
  const f = $("floater");
  f.textContent = text;
  f.className = "floater " + cls;
  void f.offsetWidth;
  f.classList.add("go");
}

// ---------- result ----------
function showResult(data) {
  const win = data.victory;
  $("result-title").textContent = win ? "VICTORY" : "DEFEAT";
  $("result-title").style.color = win ? "var(--green)" : "var(--red)";
  $("result-line").textContent = win
    ? `You vanquished the ${monster.name}!`
    : `The ${monster.name} got the better of you. Regroup and try again.`;
  $("result-xp").textContent = data.xp_gained;
  $("result-correct").textContent = `${data.correct_count} / ${quest.total}`;
  $("result-level").textContent = data.player.level;
  $("result-levelup").hidden = !(data.player.level > levelAtStart);
  renderHud(data.player);
  show("result");
}

$("btn-again").onclick = () => {
  $("in-text").value = "";
  $("in-topic").value = "";
  show("start");
};

loadPlayer();
