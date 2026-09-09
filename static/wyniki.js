(async function () {
  const app = document.getElementById("app");

  let shoes = [], voters = [], allVotes = [];
  try {
    [shoes, { voters }, { votes: allVotes }] = await Promise.all([
      loadShoes(),
      api("/api/voters"),
      api("/api/votes"),
    ]);
  } catch (e) {
    app.innerHTML = '<p class="empty">Nie udało się wczytać danych.</p>';
    return;
  }

  if (!shoes.length) {
    app.innerHTML = '<p class="empty">Nie dodano jeszcze żadnych butów.</p>';
    return;
  }

  const isTest = (name) => /test/i.test(name);
  let showTest = false;
  let filter = "all";
  let currentVoter = (voters.find((v) => !isTest(v.voter)) || voters[0] || {}).voter || "";

  render();

  function visibleVoters() {
    return voters.filter((v) => showTest || !isTest(v.voter));
  }

  function render() {
    const vv = visibleVoters();
    if (!vv.length) {
      app.innerHTML = voterPicker() + '<p class="empty">Nikt jeszcze nie ocenił butów.</p>';
      wirePicker();
      return;
    }
    if (!vv.find((v) => v.voter === currentVoter)) currentVoter = vv[0].voter;

    const mine = {};
    allVotes.filter((r) => r.voter === currentVoter).forEach((r) => { mine[r.shoe_id] = r.decision; });

    const keep = shoes.filter((s) => mine[s.id] === "keep").length;
    const toss = shoes.filter((s) => mine[s.id] === "toss").length;
    const none = shoes.length - keep - toss;

    const list = shoes.filter((s) => {
      const d = mine[s.id] || "none";
      return filter === "all" ? true : filter === d;
    });

    app.innerHTML = `
      ${voterPicker()}
      <div class="stats">
        <div class="stat keep"><b>${keep}</b><small>zostają</small></div>
        <div class="stat toss"><b>${toss}</b><small>do wyrzucenia</small></div>
        <div class="stat"><b>${none}</b><small>bez decyzji</small></div>
      </div>
      <div class="chips">
        ${chip("all", "Wszystkie")}
        ${chip("keep", "Zostają")}
        ${chip("toss", "Do wyrzucenia")}
        ${chip("none", "Bez decyzji")}
      </div>
      <div class="grid">
        ${list.map((s) => shoeCard(s, mine[s.id])).join("") || '<p class="empty" style="grid-column:1/-1">Nic w tej kategorii.</p>'}
      </div>
    `;

    wirePicker();
    app.querySelectorAll(".chip").forEach((c) => {
      c.addEventListener("click", () => { filter = c.dataset.f; render(); });
    });
    app.querySelectorAll(".shoe").forEach((el) => {
      el.addEventListener("click", () => openLightbox(shoes.find((s) => s.id === el.dataset.id), mine[el.dataset.id]));
    });
  }

  function voterPicker() {
    const opts = visibleVoters()
      .map((v) => `<option value="${esc(v.voter)}" ${v.voter === currentVoter ? "selected" : ""}>${esc(v.voter)} (${v.count})</option>`)
      .join("");
    const hasTest = voters.some((v) => isTest(v.voter));
    return `
      <div class="res-head">
        <div>
          <label for="voter">Czyje odpowiedzi</label>
          <select id="voter">${opts || '<option>—</option>'}</select>
        </div>
        ${hasTest ? `<label class="checkbox"><input type="checkbox" id="showTest" ${showTest ? "checked" : ""} /> pokaż odpowiedzi testowe</label>` : ""}
      </div>
    `;
  }

  function wirePicker() {
    const sel = document.getElementById("voter");
    if (sel) sel.addEventListener("change", () => { currentVoter = sel.value; render(); });
    const st = document.getElementById("showTest");
    if (st) st.addEventListener("change", () => { showTest = st.checked; render(); });
  }

  function chip(f, label) {
    return `<button class="chip ${filter === f ? "on" : ""}" data-f="${f}">${label}</button>`;
  }

  function shoeCard(s, decision) {
    const d = decision || "none";
    const txt = d === "keep" ? "ZOSTAJĄ" : d === "toss" ? "DO WYRZUCENIA" : "bez decyzji";
    return `
      <div class="shoe" data-id="${esc(s.id)}">
        <img class="thumb" src="${esc(s.photos[0])}" alt="" loading="lazy" />
        <div class="meta">
          <div class="name">${esc(s.label)}</div>
          <span class="badge ${d}">${txt}</span>
        </div>
      </div>
    `;
  }

  function openLightbox(shoe, decision) {
    if (!shoe) return;
    let i = 0;
    const box = document.createElement("div");
    box.className = "lb";
    document.body.appendChild(box);

    function draw() {
      const d = decision || "none";
      const txt = d === "keep" ? "✓ ZOSTAJĄ" : d === "toss" ? "✗ DO WYRZUCENIA" : "bez decyzji";
      box.innerHTML = `
        <div class="cap">${esc(shoe.label)} — ${txt} &nbsp; (${i + 1}/${shoe.photos.length})</div>
        <img src="${esc(shoe.photos[i])}" alt="" />
        <div class="lb-row">
          ${shoe.photos.length > 1 ? '<button data-a="prev">‹ poprzednie</button><button data-a="next">następne ›</button>' : ""}
          <button data-a="close">Zamknij</button>
        </div>
      `;
      box.querySelectorAll("button").forEach((b) => b.addEventListener("click", (e) => {
        e.stopPropagation();
        const a = b.dataset.a;
        if (a === "close") { box.remove(); return; }
        i = (i + (a === "next" ? 1 : -1) + shoe.photos.length) % shoe.photos.length;
        draw();
      }));
    }
    box.addEventListener("click", (e) => { if (e.target === box) box.remove(); });
    draw();
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
})();
