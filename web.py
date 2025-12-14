from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json, db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()


def page(title, body):
    return f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{title}</title>
      <style>
        body {{ font-family: Arial; padding: 15px; }}
        .card {{ background:#fff; padding:15px; border-radius:10px; margin-bottom:15px; }}
        input, textarea {{ width:100%; padding:10px; margin:6px 0; }}
        button {{ padding:10px; background:#2563eb; color:white; border:none; }}
        a {{ display:block; margin:8px 0; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """


@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form["password"] == ADMIN_PASSWORD:
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


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return page("Dashboard", """
    <div class="card">
      <a href="/add">➕ Add Caption</a>
      <a href="/all">📋 View All Captions</a>
      <a href="/buttons">🔘 Inline Buttons</a>
      <a href="/channels">📡 Channel Enable / Disable</a>
      <a href="/bulk">🗑 Bulk Delete</a>
      <a href="/export">⬇ Export</a>
      <a href="/logout">Logout</a>
    </div>
    """)


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
    return page("Add Caption", """
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
      <a href="/dashboard">⬅ Back</a>
    </div>
    """)


@app.route("/all")
def all_captions():
    if not session.get("admin"):
        return redirect("/")
    rows = ""
    for d in db.captions.find():
        rows += f"<li>{d.get('channel_id')} | {d.get('type')}</li>"
    return page("All Captions", f"""
    <div class="card">
      <ul>{rows}</ul>
      <a href="/dashboard">⬅ Back</a>
    </div>
    """)


@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        rows=[]
        for line in request.form["rows"].splitlines():
            row=[]
            for b in line.split(","):
                t,u=b.split("|")
                row.append({"text":t.strip(),"url":u.strip()})
            rows.append(row)
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form["channel"] or "default"},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect("/dashboard")
    return page("Buttons", """
    <div class="card">
      <form method="post">
        <input name="channel" placeholder="Channel ID">
        <textarea name="rows"
        placeholder="Row example:
Google|https://google.com,YouTube|https://youtube.com"></textarea>
        <button>Save</button>
      </form>
      <a href="/dashboard">⬅ Back</a>
    </div>
    """)


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
      <a href="/dashboard">⬅ Back</a>
    </div>
    """)


@app.route("/bulk", methods=["GET","POST"])
def bulk():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        db.captions.delete_many({"channel_id":request.form["channel"]})
        return redirect("/dashboard")
    return page("Bulk Delete", """
    <div class="card">
      <form method="post">
        <input name="channel" placeholder="Channel ID">
        <button>Delete All</button>
      </form>
      <a href="/dashboard">⬅ Back</a>
    </div>
    """)


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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
