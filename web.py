from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json, db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()


# ---------- MODERN PAGE ----------
def page(title, body):
    return f"""
    <html>
    <head>
      <title>{title}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{ font-family: system-ui; background:#f4f6f8; padding:15px; }}
        .card {{ background:#fff; padding:15px; border-radius:10px; margin-bottom:15px; }}
        input, textarea {{ width:100%; padding:10px; margin:6px 0; }}
        button {{ background:#2563eb; color:#fff; border:none; padding:10px; border-radius:8px; }}
        .danger {{ background:#dc2626; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return page("Login", """
    <div class="card">
    <form method="post">
      <input type="password" name="password" placeholder="Admin password">
      <button>Login</button>
    </form>
    </div>
    """)


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return page("Dashboard", """
    <div class="card">
      <a href="/add">➕ Add Caption</a><br>
      <a href="/buttons">🔘 Inline Buttons</a><br>
      <a href="/channels">📡 Channel Status</a><br>
      <a href="/all">📋 View All</a><br>
      <a href="/export">⬇ Export</a><br>
      <a href="/logout">Logout</a>
    </div>
    """)


# ---------- ADD CAPTION ----------
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type": request.form["type"], "channel_id": request.form["channel"] or "default"},
            {"$set": {"text": request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")
    return page("Add", """
    <div class="card">
    <form method="post">
      <input name="channel" placeholder="Channel ID (blank = default)">
      <select name="type">
        <option value="photo_caption">Photo</option>
        <option value="video_caption">Video</option>
        <option value="text_caption">Text</option>
      </select>
      <textarea name="text"></textarea>
      <button>Save</button>
    </form>
    </div>
    """)


# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        rows = []
        for r in request.form.get("rows","").split("\n"):
            row=[]
            for b in r.split(","):
                t,u=b.split("|")
                row.append({"text":t.strip(),"url":u.strip()})
            rows.append(row)
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect("/buttons")
    return page("Buttons", """
    <div class="card">
    <form method="post">
      <input name="channel" placeholder="Channel ID (blank = default)">
      <textarea name="rows"
      placeholder="Row example:
Google|https://google.com,YouTube|https://youtube.com
Telegram|https://t.me"></textarea>
      <button>Save Buttons</button>
    </form>
    <p>Use /preview_buttons in Telegram to preview</p>
    </div>
    """)


# ---------- CHANNEL ENABLE/DISABLE ----------
@app.route("/channels", methods=["GET","POST"])
def channels():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":"channel_status","channel_id":request.form["channel"]},
            {"$set":{"enabled":bool(request.form.get("enabled"))}},
            upsert=True
        )
    return page("Channels", """
    <div class="card">
    <form method="post">
      <input name="channel" placeholder="Channel ID">
      <label><input type="checkbox" name="enabled"> Enabled</label>
      <button>Save</button>
    </form>
    </div>
    """)


# ---------- BULK DELETE ----------
@app.route("/bulk", methods=["POST"])
def bulk():
    if not session.get("admin"):
        return redirect("/")
    db.captions.delete_many({"channel_id":request.form["channel"]})
    return redirect("/dashboard")


# ---------- EXPORT ----------
@app.route("/export")
def export():
    data=list(db.captions.find({},{"_id":0}))
    return Response(json.dumps(data,indent=2),
        mimetype="application/json",
        headers={"Content-Disposition":"attachment;filename=backup.json"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
