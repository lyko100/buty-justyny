// Shared helpers.

function getVoter() {
  const p = new URLSearchParams(location.search).get("kto");
  if (p) { try { localStorage.setItem("buty_voter", p); } catch (e) {} return p; }
  try { return localStorage.getItem("buty_voter") || ""; } catch (e) { return ""; }
}

function setVoter(name) {
  try { localStorage.setItem("buty_voter", name); } catch (e) {}
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error("API " + res.status);
  return res.json();
}

async function loadShoes() {
  const data = await api("/api/shoes");
  return data.shoes || [];
}
