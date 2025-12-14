from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json
import db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()

# ------------------ UI HELPERS ------------------
def page(title, body):
    return f"""
    <html>
    <head>
      <title>{title}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{ font-family: system-ui; background:#f4f6f8; padding:15px; }}
        .card {{ background:#fff; padding:15px; border-radius:10px; margin-bottom:15px; }}
        a {{ display:block; margin:6px 0; }}
        input, textarea, select {{ width:100%; padding:10px; margin:6px 0; }}
        button {{ background:#2563eb; color:#fff; border:none; padding:10px; border-radius:8px; }}
        .danger {{ background:#dc2626; }}
        table {{ width:100%; border-collapse:collapse; }}
        th,td {{ border:1px solid #ccc; padding:6px; font-size:14px; }}
        th {{ background:#eee; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """

def back():
    return '<br><a href="/dashboard">⬅ Back to Dashboard</a>'

# ------------------ LOGIN ------------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
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

# ------------------ DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return page("Dashboard", """
    <div class="card">
      <h3>Admin Dashboard</h3>
      <a href="/add">➕ Add Caption</a>
      <a href="/buttons">🔘 Inline Buttons</a>
      <a href="/channels">📡 Channel Enable / Disable</a>
      <a href="/all">📋 View All Data</a>
      <a href="/export">⬇ Export Backup</a>
      <a href="/logout">Logout</a>
    </div>
    """)

# ------------------ ADD CAPTION ------------------
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {
                "type": request.form["type"],
                "channel_id": request.form.get("channel") or "default"
            },
            {"$set": {"text": request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption", """
    <div class="card">
      <h3>Add Caption</h3>
      <form method="post">
        <input name="channel" placeholder="Channel ID (blank = default)">
        <select name="type">
          <option value="photo_caption">Photo</option>
          <option value="video_caption">Video</option>
          <option value="text_caption">Text</option>
        </select>
        <textarea name="text" placeholder="Caption text"></textarea>
        <button>Save</button>
      </form>
      """ + back() + """
    </div>
    """)

# ------------------ INLINE BUTTONS ------------------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        rows = []
        for r in request.form.get("rows","").splitlines():
            row=[]
            for b in r.split(","):
                if "|" in b:
                    t,u=b.split("|",1)
                    row.append({"text":t.strip(),"url":u.strip()})
            if row:
                rows.append(row)

        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect("/buttons")

    return page("Inline Buttons", """
    <div class="card">
      <h3>Inline Buttons</h3>
      <form method="post">
        <input name="channel" placeholder="Channel ID (blank = default)">
        <textarea name="rows" placeholder="Example:
Google|https://google.com,YouTube|https://youtube.com
Telegram|https://t.me"></textarea>
        <button>Save Buttons</button>
      </form>
      <p>Preview in Telegram: <b>/preview_buttons</b></p>
      """ + back() + """
    </div>
    """)

# ------------------ CHANNEL ENABLE/DISABLE ------------------
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
      <h3>Channel Enable / Disable</h3>
      <form method="post">
        <input name="channel" placeholder="Channel ID">
        <label><input type="checkbox" name="enabled"> Enabled</label>
        <button>Save</button>
      </form>
      """ + back() + """
    </div>
    """)

# ------------------ VIEW ALL ------------------
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")

    rows=""
    for d in db.captions.find():
        preview = d.get("text") or str(d.get("rows",""))[:60]
        rows += f"""
        <tr>
          <td>{d.get("channel_id")}</td>
          <td>{d.get("type")}</td>
          <td>{preview}</td>
          <td><a href="/delete/{d['_id']}">❌ Delete</a></td>
        </tr>
        """

    return page("All Data", f"""
    <div class="card">
      <h3>All Saved Data</h3>
      <table>
        <tr><th>Channel</th><th>Type</th><th>Preview</th><th>Action</th></tr>
        {rows}
      </table>
      {back()}
    </div>
    """)

# ------------------ DELETE ONE ------------------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/")
    db.captions.delete_one({"_id":ObjectId(id)})
    return redirect("/all")

# ------------------ EXPORT ------------------
@app.route("/export")
def export():
    data=list(db.captions.find({},{"_id":0}))
    return Response(
        json.dumps(data,indent=2),
        mimetype="application/json",
        headers={"Content-Disposition":"attachment;filename=backup.json"}
    )

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ------------------ RUN ------------------
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
