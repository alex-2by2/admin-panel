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
except Exception as e:
    print("DB ERROR:", e)


# ---------- BASIC PAGE ----------
def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family:Arial;max-width:900px;margin:auto;padding:15px;">
<h2>{title}</h2>
{body}
</body>
</html>
"""


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
    return page("Admin Login", """
<form method="post">
<input type="password" name="password" placeholder="Admin password">
<button>Login</button>
</form>
""")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    return page("Dashboard", """
<ul>
<li><a href="/add">➕ Add Caption / Header / Footer</a></li>
<li><a href="/buttons">🔘 Inline Buttons</a></li>
<li><a href="/all">📋 View All Saved Data</a></li>
<li><a href="/channel-toggle">🚦 Channel Enable / Disable</a></li>
<li><a href="/bulk-delete">🗑 Bulk Delete Per Channel</a></li>
<li><a href="/header-toggle">🧾 Header ON / OFF</a></li>
<li><a href="/export">⬇ Export Backup</a></li>
<li><a href="/logout">Logout</a></li>
</ul>
""")


# ---------- ADD CAPTION / HEADER / FOOTER ----------
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")

    import db

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

    return page("Add Caption / Header / Footer", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)"><br><br>

<select name="type">
  <option value="header">Header</option>
  <option value="footer">Footer</option>
  <option value="text_caption">Text Caption</option>
  <option value="photo_caption">Photo Caption</option>
  <option value="video_caption">Video Caption</option>
</select><br><br>

<textarea name="text" rows="4" placeholder="Text"></textarea><br><br>
<button>Save</button>
</form>
""")


# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        buttons = []
        for t, u in zip(request.form.getlist("text"), request.form.getlist("url")):
            if t and u:
                buttons.append({"text": t, "url": u})

        db.captions.update_one(
            {
                "type": "inline_buttons",
                "channel_id": request.form.get("channel") or "default"
            },
            {"$set": {"buttons": buttons}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Inline Buttons", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)"><br><br>

<input name="text" placeholder="Button Text">
<input name="url" placeholder="https://example.com"><br><br>

<button>Save Buttons</button>
</form>
""")


# ---------- VIEW ALL (EDIT / DELETE EVERYTHING) ----------
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")

    import db

    rows = ""
    for d in db.captions.find():
        value = d.get("text") or str(d.get("buttons",""))
        rows += f"""
        <tr>
          <td>{d.get("channel_id")}</td>
          <td>{d.get("type")}</td>
          <td>{value[:50]}</td>
          <td>
            <a href="/edit/{d['_id']}">Edit</a> |
            <a href="/delete/{d['_id']}">Delete</a>
          </td>
        </tr>
        """

    return page("All Saved Data", f"""
<table border="1" width="100%" cellpadding="6">
<tr>
<th>Channel</th>
<th>Type</th>
<th>Content</th>
<th>Action</th>
</tr>
{rows}
</table>

<br>
<a href="/dashboard">← Back</a>
""")


# ---------- EDIT ----------
@app.route("/edit/<id>", methods=["GET","POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    doc = db.captions.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.captions.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"text": request.form["text"]}}
        )
        return redirect("/all")

    return page("Edit Item", f"""
<form method="post">
<p>Channel: {doc.get("channel_id")}</p>
<p>Type: {doc.get("type")}</p>
<textarea name="text" rows="4">{doc.get("text","")}</textarea><br><br>
<button>Save</button>
</form>

<br>
<a href="/all">← Back</a>
""")


# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")


# ---------- CHANNEL ENABLE ----------
@app.route("/channel-toggle", methods=["GET","POST"])
def channel_toggle():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        enabled = True if request.form.get("enabled") == "on" else False

        db.captions.update_one(
            {
                "type": "channel_status",
                "channel_id": request.form["channel"]
            },
            {"$set": {"enabled": enabled}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Channel Enable / Disable", """
<form method="post">
<input name="channel" placeholder="Channel ID"><br><br>
<label><input type="checkbox" name="enabled" checked> Enable Bot</label><br><br>
<button>Save</button>
</form>
""")


# ---------- BULK DELETE ----------
@app.route("/bulk-delete", methods=["GET","POST"])
def bulk_delete():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        db.captions.delete_many({"channel_id": request.form["channel"]})
        return redirect("/dashboard")

    return page("Bulk Delete", """
<form method="post">
<input name="channel" placeholder="Channel ID"><br><br>
<button>DELETE ALL</button>
</form>
""")


# ---------- EXPORT ----------
@app.route("/export")
def export():
    import db
    data = list(db.captions.find({}, {"_id": 0}))
    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json"
    )
@app.route("/header-toggle", methods=["GET","POST"])
def header_toggle():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        channel = request.form.get("channel") or "default"
        enabled = True if request.form.get("enabled") == "on" else False

        db.captions.update_one(
            {
                "type": "header_status",
                "channel_id": channel
            },
            {"$set": {"enabled": enabled}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Header ON / OFF", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)"><br><br>

<label>
  <input type="checkbox" name="enabled" checked>
  Enable Header
</label><br><br>

<button>Save</button>
</form>
<a href="/dashboard">← Back</a>
""")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
