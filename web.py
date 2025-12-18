from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json
import db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

db.init_db()

# ================= PAGE TEMPLATE =================
def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
  font-family: system-ui, Arial;
  background: #f1f5f9;
  margin: 0;
}}
.topbar {{
  background: #0f172a;
  color: white;
  padding: 14px;
  font-size: 18px;
  font-weight: bold;
}}
.container {{
  max-width: 900px;
  margin: auto;
  padding: 16px;
}}
.card {{
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(0,0,0,.06);
}}
.btn {{
  display: block;
  padding: 12px;
  margin: 8px 0;
  background: #2563eb;
  color: white;
  text-decoration: none;
  border-radius: 10px;
  text-align: center;
  font-weight: 600;
}}
.btn.red {{ background: #dc2626; }}
.btn.gray {{ background: #4b5563; }}

input, textarea, select {{
  width: 100%;
  padding: 10px;
  margin: 8px 0;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
}}

button {{
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #2563eb;
  color: white;
  font-size: 16px;
  font-weight: 600;
}}

.telegram {{
  background: #e5f0ff;
  border-radius: 12px;
  padding: 12px;
  white-space: pre-wrap;
}}

.tg-btn {{
  display: block;
  margin-top: 6px;
  padding: 8px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  text-align: center;
}}
</style>
</head>

<body>
<div class="topbar">🤖 Channel Auto Caption Admin</div>
<div class="container">
<div class="card">
<h2>{title}</h2>
{body}
</div>
</div>
</body>
</html>
"""

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect("/dashboard")
    return page("Login", """
<form method="post">
<input type="password" name="password" placeholder="Admin password">
<button>Login</button>
</form>
""")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return page("Dashboard", """
<a href="/add" class="btn">➕ Add Caption / Header / Footer</a>
<a href="/buttons" class="btn">🔘 Inline Buttons</a>
<a href="/all" class="btn">📋 View / Edit / Delete All</a>

<hr>

<a href="/channel-toggle" class="btn gray">🚦 Channel Enable / Disable</a>
<a href="/header-toggle" class="btn gray">🧾 Header ON / OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON / OFF</a>

<hr>

<a href="/bulk-delete" class="btn red">🗑 Bulk Delete (Per Channel)</a>
<a href="/export" class="btn">⬇ Export Backup</a>
<a href="/logout" class="btn red">Logout</a>
""")

# ================= ADD + PREVIEW =================
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.update_one(
            {"type": request.form["type"], "channel_id": request.form.get("channel") or "default"},
            {"$set": {"text": request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)">

<select name="type" id="type" onchange="preview()">
  <option value="header">Header</option>
  <option value="footer">Footer</option>
  <option value="text_caption">Text Caption</option>
  <option value="photo_caption">Photo Caption</option>
  <option value="video_caption">Video Caption</option>
</select>

<textarea id="text" name="text" rows="4" placeholder="Write text..." oninput="preview()"></textarea>
<button>Save</button>
</form>

<h3>📱 Telegram Preview</h3>
<div class="telegram" id="preview">Nothing to preview…</div>

<script>
function preview() {{
  let text = document.getElementById("text").value;
  document.getElementById("preview").innerText =
    text.trim() ? text : "Nothing to preview…";
}}
</script>
""")

# ================= INLINE BUTTONS =================
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        btns = []
        for t,u in zip(request.form.getlist("text"), request.form.getlist("url")):
            if t and u:
                btns.append({"text": t, "url": u})

        db.captions.update_one(
            {"type": "inline_buttons", "channel_id": request.form.get("channel") or "default"},
            {"$set": {"buttons": btns}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Inline Buttons", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)">
<input name="text" placeholder="Button Text">
<input name="url" placeholder="https://example.com">
<button>Save</button>
</form>

<h3>📱 Button Preview</h3>
<div class="telegram">
  <div class="tg-btn">Button</div>
</div>
""")

# ================= VIEW / EDIT / DELETE =================
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")

    rows = ""
    for d in db.captions.find():
        rows += f"""
<tr>
<td>{d.get('channel_id')}</td>
<td>{d.get('type')}</td>
<td>{str(d.get('text',''))[:30]}</td>
<td>
<a href="/edit/{d['_id']}">Edit</a> |
<a href="/delete/{d['_id']}">Delete</a>
</td>
</tr>
"""

    return page("All Saved Data", f"""
<table border="1" width="100%">
<tr><th>Channel</th><th>Type</th><th>Content</th><th>Action</th></tr>
{rows}
</table>
<a href="/dashboard" class="btn gray">← Back</a>
""")

@app.route("/edit/<id>", methods=["GET","POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/")

    doc = db.captions.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.captions.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"text": request.form["text"]}}
        )
        return redirect("/all")

    return page("Edit", f"""
<form method="post">
<p><b>Channel:</b> {doc.get('channel_id')}</p>
<p><b>Type:</b> {doc.get('type')}</p>
<textarea name="text">{doc.get('text','')}</textarea>
<button>Save</button>
</form>
<a href="/all" class="btn gray">← Back</a>
""")

@app.route("/delete/<id>")
def delete(id):
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")

# ================= TOGGLES =================
@app.route("/channel-toggle", methods=["GET","POST"])
def channel_toggle():
    if request.method == "POST":
        db.captions.update_one(
            {"type":"channel_status","channel_id":request.form["channel"]},
            {"$set":{"enabled":"enabled" in request.form}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Channel Enable", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable</label>
<button>Save</button>
</form>
""")

@app.route("/header-toggle", methods=["GET","POST"])
def header_toggle():
    if request.method == "POST":
        db.captions.update_one(
            {"type":"header_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Header ON / OFF", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable Header</label>
<button>Save</button>
</form>
""")

@app.route("/footer-toggle", methods=["GET","POST"])
def footer_toggle():
    if request.method == "POST":
        db.captions.update_one(
            {"type":"footer_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Footer ON / OFF", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable Footer</label>
<button>Save</button>
</form>
""")

# ================= BULK DELETE =================
@app.route("/bulk-delete", methods=["GET","POST"])
def bulk_delete():
    if request.method == "POST":
        db.captions.delete_many({"channel_id": request.form["channel"]})
        return redirect("/dashboard")

    return page("Bulk Delete", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<button class="btn red">DELETE ALL</button>
</form>
""")

# ================= EXPORT =================
@app.route("/export")
def export():
    return Response(
        json.dumps(list(db.captions.find({},{"_id":0})), indent=2),
        mimetype="application/json"
    )

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
