import os
import io
import csv
import json
import uuid

from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder="static")

HERE = os.path.dirname(__file__)
MANIFEST_PATH = os.path.join(HERE, "static", "shoes", "manifest.json")

# Vercel Postgres wstrzykuje różne nazwy zmiennych zależnie od integracji —
# bierzemy pierwszą, która jest ustawiona.
DATABASE_URL = next(
    (os.environ[k] for k in (
        "DATABASE_URL", "POSTGRES_URL", "POSTGRES_URL_NON_POOLING",
        "DATABASE_URL_UNPOOLED", "POSTGRES_PRISMA_URL",
    ) if os.environ.get(k)),
    None,
)
IS_PG = bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))

if IS_PG:
    import psycopg2
    import psycopg2.extras

_initialised = False


# ─────────────────────────────  Database  ─────────────────────────────

def get_db():
    if IS_PG:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    import sqlite3
    conn = sqlite3.connect(os.path.join(HERE, "shoes.db"))
    conn.row_factory = sqlite3.Row
    return conn


def ph(sql):
    """Postgres uses %s placeholders, sqlite uses ?."""
    return sql if IS_PG else sql.replace("%s", "?")


def init_db():
    global _initialised
    if _initialised:
        return
    conn = get_db()
    cur = conn.cursor()
    now_default = "TIMESTAMP DEFAULT NOW()" if IS_PG else "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS shoe_votes (
            id         TEXT PRIMARY KEY,
            shoe_id    TEXT NOT NULL,
            voter      TEXT NOT NULL,
            decision   TEXT NOT NULL,
            created_at {now_default},
            UNIQUE (shoe_id, voter)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    _initialised = True


@app.before_request
def _setup():
    init_db()


# ─────────────────────────────  Pages  ─────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/oceniaj")
def rate_page():
    return send_from_directory("static", "oceniaj.html")


@app.route("/wyniki")
def results_page():
    return send_from_directory("static", "wyniki.html")


# ─────────────────────────────  API  ─────────────────────────────

def load_manifest():
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"shoes": []}


@app.route("/api/shoes")
def api_shoes():
    return jsonify(load_manifest())


@app.route("/api/vote", methods=["POST"])
def api_vote():
    data = request.get_json(force=True)
    shoe_id = (data.get("shoe_id") or "").strip()
    voter = (data.get("voter") or "").strip()
    decision = (data.get("decision") or "").strip()
    if not shoe_id or not voter or decision not in ("keep", "toss"):
        return jsonify({"error": "bad request"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(ph("DELETE FROM shoe_votes WHERE shoe_id=%s AND voter=%s"), (shoe_id, voter))
    cur.execute(
        ph("INSERT INTO shoe_votes (id, shoe_id, voter, decision) VALUES (%s,%s,%s,%s)"),
        (str(uuid.uuid4())[:12], shoe_id, voter, decision),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/undo", methods=["POST"])
def api_undo():
    data = request.get_json(force=True)
    shoe_id = (data.get("shoe_id") or "").strip()
    voter = (data.get("voter") or "").strip()
    if not shoe_id or not voter:
        return jsonify({"error": "bad request"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute(ph("DELETE FROM shoe_votes WHERE shoe_id=%s AND voter=%s"), (shoe_id, voter))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/votes")
def api_votes():
    voter = request.args.get("voter", "").strip()
    conn = get_db()
    cur = conn.cursor()
    if voter:
        cur.execute(ph("SELECT shoe_id, voter, decision FROM shoe_votes WHERE voter=%s"), (voter,))
    else:
        cur.execute("SELECT shoe_id, voter, decision FROM shoe_votes")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({"votes": rows})


@app.route("/api/voters")
def api_voters():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT voter, COUNT(*) AS n FROM shoe_votes GROUP BY voter ORDER BY voter")
    rows = [{"voter": r["voter"], "count": r["n"]} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({"voters": rows})


@app.route("/api/export.csv")
def api_export():
    manifest = load_manifest()
    labels = {s["id"]: s.get("label", s["id"]) for s in manifest.get("shoes", [])}
    order = {s["id"]: i for i, s in enumerate(manifest.get("shoes", []))}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT shoe_id, voter, decision, created_at FROM shoe_votes")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()

    rows.sort(key=lambda r: (r["voter"], order.get(r["shoe_id"], 9999)))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["para", "kto", "decyzja", "kiedy"])
    pl = {"keep": "ZOSTAJE", "toss": "WYRZUCAMY"}
    for r in rows:
        w.writerow([labels.get(r["shoe_id"], r["shoe_id"]), r["voter"],
                    pl.get(r["decision"], r["decision"]), r["created_at"]])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=buty-wyniki.csv"})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, port=port)
