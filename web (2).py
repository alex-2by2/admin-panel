from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# ---------- DB INIT ----------
try:
    import db
    db.init_db()
    DB_OK = True
except Exception as e:
    print("DB init failed:", e)
    DB_OK = False


# ---------- MOBILE UI ----------
def page(title, body):
    return f"""
    <html>
    <head>
      <title>{title}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{ font-family: Arial; padding: 15px; max-width: 900px; margin: auto; }}
        textarea, input, select {{ width: 100%; padding: 10px; margin: 6px 0; font-size: 16px; }}
        button {{ padding: 8px 14px; font-size: 15px; margin-top: 6px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 6px; font-size: 14px; }}
        th {{ background: #eee; }}
        a {{ margin-right: 10px; display: inline-block; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
        return page("Error", "<h3>Wrong password</h3><a href='/'>Back</a>")

    return page("Login", """
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" placeholder="Password" required>
      <button>Login</button>
    </form>
    """)


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    if not DB_OK:
        return page("DB Error", "<h3>⚠ MongoDB not connected</h3>")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"
        db.captions.update_one(
            {"type": request.form["type"], "channel_id": channel_id},
            {"$set": {"text": request.form["caption"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Dashboard", """
    <h2>Add Caption</h2>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">
      <select name="type">
        <option value="photo_caption">Photo</option>
        <option value="video_caption">Video</option>
        <option value="text_caption">Text</option>
      </select>
      <textarea name="caption" placeholder="Caption text"></textarea>
      <button>Save Caption</button>
    </form>

    <hr>
    <a href="/all">📋 View All Captions</a>
    <a href="/channels">📡 Saved Channel IDs</a>
    <a href="/buttons">🔘 Inline Buttons</a>
    <a href="/export">⬇ Export Captions</a>
    <a href="/logout">Logout</a>
    """)


# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET", "POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"
        buttons = []

        for t, u in zip(request.form.getlist("text"), request.form.getlist("url")):
            if t and u:
                buttons.append({"text": t, "url": u})

        db.captions.update_one(
            {"type": "inline_buttons", "channel_id": channel_id},
            {"$set": {"buttons": buttons}},
            upsert=True
        )
        return redirect("/buttons")

    return page("Inline Buttons", """
    <h2>Inline Buttons</h2>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">
      <input name="text" placeholder="Button Text">
      <input name="url" placeholder="Button URL (https://...)">
      <button>Save Button</button>
    </form>

    <p><b>Note:</b> URL must be FULL https link</p>
    <a href="/dashboard">Back</a>
    """)


# ---------- VIEW ALL CAPTIONS ----------
@app.route("/all")
def all_captions():
    if not session.get("admin"):
        return redirect("/")

    import db
    rows = ""
    for d in db.captions.find():
        rows += f"""
        <tr>
          <td>{d.get("channel_id")}</td>
          <td>{d.get("type")}</td>
          <td>{str(d.get("text",""))[:50]}</td>
          <td>
            <a href="/edit/{d['_id']}">Edit</a>
            <a href="/delete/{d['_id']}">Delete</a>
          </td>
        </tr>
        """

    return page("All Captions", f"""
    <h2>All Saved Captions</h2>
    <table>
      <tr><th>Channel</th><th>Type</th><th>Text</th><th>Action</th></tr>
      {rows}
    </table>
    <a href="/dashboard">Back</a>
    """)


# ---------- EDIT ----------
@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    doc = db.captions.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.captions.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"text": request.form["caption"]}}
        )
        return redirect("/all")

    return page("Edit", f"""
    <h2>Edit Caption</h2>
    <p><b>Channel:</b> {doc.get("channel_id")}</p>
    <p><b>Type:</b> {doc.get("type")}</p>

    <form method="post">
      <textarea name="caption">{doc.get("text","")}</textarea>
      <button>Save</button>
    </form>
    <a href="/all">Back</a>
    """)


# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")


# ---------- CHANNEL LIST ----------
@app.route("/channels")
def channels():
    if not session.get("admin"):
        return redirect("/")

    import db
    ch = db.captions.distinct("channel_id")
    items = "".join(f"<li>{c}</li>" for c in ch)

    return page("Channels", f"""
    <h2>Saved Channel IDs</h2>
    <ul>{items}</ul>
    <a href="/dashboard">Back</a>
    """)


# ---------- EXPORT ----------
@app.route("/export")
def export():
    if not session.get("admin"):
        return redirect("/")

    import db
    data = list(db.captions.find({}, {"_id": 0}))

    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=captions_backup.json"}
    )


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
