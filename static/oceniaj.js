(async function () {
  const app = document.getElementById("app");
  const voter = getVoter();

  if (!voter) { location.href = "/"; return; }

  // Lock the screen to exactly the visible area so nothing is ever clipped
  // and there is never a scrollbar — on iOS Safari CSS viewport units are
  // unreliable while the toolbar animates.
  function lockHeight() {
    const h = (window.visualViewport && window.visualViewport.height) || window.innerHeight;
    app.style.height = h + "px";
    window.scrollTo(0, 0);
  }
  lockHeight();
  window.addEventListener("resize", lockHeight);
  window.addEventListener("orientationchange", () => setTimeout(lockHeight, 200));
  if (window.visualViewport) window.visualViewport.addEventListener("resize", lockHeight);

  let shoes = [];
  try {
    shoes = await loadShoes();
  } catch (e) {
    app.innerHTML = errorBox("Nie udało się wczytać butów.");
    return;
  }

  if (!shoes.length) {
    app.innerHTML = '<div class="done"><div class="big">👟</div><h1>Brak butów</h1>'
      + '<p>Nikt jeszcze nie dodał zdjęć butów. Zajrzyj do pliku README, żeby je wgrać.</p></div>';
    return;
  }

  // Resume: skip shoes this person already voted on.
  let voted = {};
  try {
    const v = await api("/api/votes?voter=" + encodeURIComponent(voter));
    v.votes.forEach((row) => { voted[row.shoe_id] = row.decision; });
  } catch (e) {}

  let idx = shoes.findIndex((s) => !(s.id in voted));
  if (idx === -1) idx = shoes.length; // all done
  let lastVotedId = null;
  let photoIdx = 0;

  renderIntro();

  // ─────────────────────────────  Instrukcja  ─────────────────────────────

  function renderIntro() {
    const total = shoes.length;
    app.innerHTML = `
      <div class="rate-top">
        <div class="progress-text">Para 0 z ${total}</div>
        <div class="bar"><i style="width:0%"></i></div>
      </div>

      <div class="screen">
        <h2>Jak to działa</h2>

        <div class="instr-row">
          <span class="mark tap">📷</span>
          <p>Kliknij na zdjęcie, żeby obejrzeć pozostałe zdjęcia tej samej pary butów.</p>
        </div>
        <div class="instr-row">
          <span class="mark toss">✗</span>
          <p>Kliknij <b>czerwony</b> przycisk, jeśli te buty chcesz <b>wyrzucić</b>.</p>
        </div>
        <div class="instr-row">
          <span class="mark keep">✓</span>
          <p>Kliknij <b>zielony</b> przycisk, jeśli te buty chcesz <b>zostawić</b>.</p>
        </div>
        <div class="instr-row">
          <span class="mark tap">←</span>
          <p>Jeśli klikniesz coś przez pomyłkę, użyj <b>„Cofnij do poprzedniej pary"</b>.</p>
        </div>

        <p class="instr-q">Czy na pewno wszystko rozumiesz?</p>
        <button class="big-btn" id="startBtn">Tak, rozumiem — zaczynamy →</button>
      </div>
    `;
    document.getElementById("startBtn").addEventListener("click", render);
  }

  // ─────────────────────────────  Karta pary  ─────────────────────────────

  function render() {
    if (idx >= shoes.length) { renderDone(); return; }
    const shoe = shoes[idx];
    photoIdx = 0;
    const total = shoes.length;
    const pos = idx + 1;

    app.innerHTML = `
      <div class="rate-top">
        <div class="progress-text">Para ${pos} z ${total}</div>
        <div class="bar"><i style="width:${(idx / total) * 100}%"></i></div>
      </div>

      <div class="photo-stage" id="stage">
        <img id="photo" src="${shoe.photos[0]}" alt="" />
        <button class="photo-nav prev" id="prevPhoto" aria-label="poprzednie zdjęcie"></button>
        <button class="photo-nav next" id="nextPhoto" aria-label="następne zdjęcie"></button>
        <div class="dots" id="dots"></div>
      </div>
      <div class="photo-hint">${shoe.photos.length > 1 ? "dotknij zdjęcia, żeby zobaczyć kolejne" : ""}</div>

      <div class="choices">
        <button class="choice toss" id="toss"><span class="icon">✗</span>DO WYRZUCENIA</button>
        <button class="choice keep" id="keep"><span class="icon">✓</span>ZOSTAJĄ</button>
      </div>

      <div class="undo">
        <button id="undo" ${lastVotedId ? "" : "disabled"}>← Cofnij do poprzedniej pary</button>
      </div>
    `;

    drawDots();
    const photo = document.getElementById("photo");
    const stage = document.getElementById("stage");
    stage.addEventListener("click", (e) => {
      if (e.target.id === "prevPhoto") { step(-1); return; }
      step(1);
    });

    document.getElementById("keep").addEventListener("click", () => vote("keep"));
    document.getElementById("toss").addEventListener("click", () => vote("toss"));
    document.getElementById("undo").addEventListener("click", undo);

    function step(dir) {
      const n = shoe.photos.length;
      photoIdx = (photoIdx + dir + n) % n;
      photo.src = shoe.photos[photoIdx];
      drawDots();
    }
  }

  function drawDots() {
    const shoe = shoes[idx];
    const dots = document.getElementById("dots");
    if (!dots) return;
    dots.innerHTML = shoe.photos.map((_, i) => `<i class="${i === photoIdx ? "on" : ""}"></i>`).join("");
  }

  async function vote(decision) {
    const shoe = shoes[idx];
    disableChoices();
    try {
      await api("/api/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shoe_id: shoe.id, voter, decision }),
      });
      lastVotedId = shoe.id;
      idx++;
      render();
    } catch (e) {
      alert("Nie udało się zapisać. Sprawdź internet i spróbuj jeszcze raz.");
      enableChoices();
    }
  }

  async function undo() {
    if (!lastVotedId) return;
    try {
      await api("/api/undo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ shoe_id: lastVotedId, voter }),
      });
      const backTo = shoes.findIndex((s) => s.id === lastVotedId);
      if (backTo !== -1) idx = backTo;
      lastVotedId = null;
      render();
    } catch (e) {
      alert("Nie udało się cofnąć.");
    }
  }

  function disableChoices() {
    ["keep", "toss", "undo"].forEach((id) => { const el = document.getElementById(id); if (el) el.disabled = true; });
  }
  function enableChoices() {
    ["keep", "toss"].forEach((id) => { const el = document.getElementById(id); if (el) el.disabled = false; });
  }

  function renderDone() {
    let keep = 0, toss = 0;
    api("/api/votes?voter=" + encodeURIComponent(voter)).then((v) => {
      v.votes.forEach((r) => { r.decision === "keep" ? keep++ : toss++; });
      const s = document.getElementById("doneStats");
      if (s) s.textContent = `Zostają: ${keep} · Do wyrzucenia: ${toss}`;
    }).catch(() => {});

    app.innerHTML = `
      <div class="done">
        <div class="big">💛</div>
        <h1>To wszystko!</h1>
        <p>Dziękujemy. Wszystkie odpowiedzi są zapisane —<br />możesz zamknąć tę stronę.</p>
        <p id="doneStats" style="margin-top:10px;font-weight:800;color:var(--text)"></p>
      </div>
    `;
  }

  function errorBox(msg) {
    return `<div class="done"><div class="big">😕</div><h1>Ups</h1><p>${msg}</p></div>`;
  }
})();
