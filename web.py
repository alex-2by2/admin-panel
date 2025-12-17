from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json
import db

# ================= APP =================
app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

db.init_db()

# ================= PAGE =================
def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{font-family:Arial;background:#f4f6f8;margin:0}}
.header {{background:#111827;color:white;padding:14px;font-size:18px}}
.box {{max-width:900px;margin:auto;padding:15px}}
.card {{background:white;padding:15px;border-radius:10px}}
a.btn {{display:block;padding:12px;margin:8px 0;background:#2563eb;color:white;text-decoration:none;border-radius:8px;text-align:center}}
a.red {{background:#dc2626}}
a.gray {{background:#4b5563}}
input,select,textarea {{width:100%;padding:10px;margin:6px 0}}
button {{width:100%;padding:12px;background:#2563eb;color:white;border:none;border-radius:8px}}
table {{width:100%;border-collapse:collapse}}
td,th {{border:1px solid #ccc;padding:6px}}
</style>
</head>
<body>
<div class="header">🤖 Auto Caption Admin</div>
<div class="box">
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
<a href="/header-toggle" class="btn gray">🧾 Header ON/OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON/OFF</a>
<a href="/channel-toggle" class="btn gray">🚦 Channel Enable</a>
<a href="/bulk-delete" class="btn red">🗑 Bulk Delete</a>
<a href="/all" class="btn">📋 View All</a>
<a href="/export" class="btn">⬇ Export</a>
<a href="/logout" class="btn red">Logout</a>
""")

# ================= ADD =================
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":request.form["type"],"channel_id":request.form.get("channel") or "default"},
            {"$set":{"text":request.form["text"]}}, upsert=True)
        return redirect("/dashboard")
    return page("Add", """
<form method="post">
<input name="channel" placeholder="Channel ID (default)">
<select name="type">
<option value="header">Header</option>
<option value="footer">Footer</option>
<option value="text_caption">Text</option>
<option value="photo_caption">Photo</option>
<option value="video_caption">Video</option>
</select>
<textarea name="text"></textarea>
<button>Save</button>
</form>
""")

# ================= INLINE BUTTONS =================
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        btns=[]
        for t,u in zip(request.form.getlist("text"),request.form.getlist("url")):
            if t and u:
                btns.append({"text":t,"url":u})
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"buttons":btns}},upsert=True)
        return redirect("/dashboard")
    return page("Inline Buttons", """
<form method="post">
<input name="channel" placeholder="Channel ID (default)">
<input name="text" placeholder="Button Text">
<input name="url" placeholder="https://example.com">
<button>Save</button>
</form>
""")

# ================= CHANNEL ENABLE =================
@app.route("/channel-toggle", methods=["GET","POST"])
def channel_toggle():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":"channel_status","channel_id":request.form["channel"]},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Channel Enable", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable</label>
<button>Save</button>
</form>
""")

# ================= HEADER TOGGLE =================
@app.route("/header-toggle", methods=["GET","POST"])
def header_toggle():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":"header_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Header Toggle", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable Header</label>
<button>Save</button>
</form>
""")

# ================= FOOTER TOGGLE =================
@app.route("/footer-toggle", methods=["GET","POST"])
def footer_toggle():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":"footer_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Footer Toggle", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<label><input type="checkbox" name="enabled" checked> Enable Footer</label>
<button>Save</button>
</form>
""")

# ================= BULK DELETE =================
@app.route("/bulk-delete", methods=["GET","POST"])
def bulk_delete():
    if not session.get("admin"): return redirect("/")
    if request.method == "POST":
        db.captions.delete_many({"channel_id":request.form["channel"]})
        return redirect("/dashboard")
    return page("Bulk Delete", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<button>DELETE ALL</button>
</form>
""")

# ================= VIEW ALL =================
@app.route("/all")
def all_items():
    if not session.get("admin"): return redirect("/")
    rows=""
    for d in db.captions.find():
        rows+=f"""
<tr>
<td>{d.get('channel_id')}</td>
<td>{d.get('type')}</td>
<td>{str(d.get('text',''))[:30]}</td>
<td><a href="/delete/{d['_id']}">Delete</a></td>
</tr>
"""
    return page("All Data", f"""
<table>
<tr><th>Channel</th><th>Type</th><th>Text</th><th>Action</th></tr>
{rows}
</table>
<a href="/dashboard">← Back</a>
""")

# ================= DELETE (FIXED) =================
@app.route("/delete/<id>")
def delete_item(id):
    if not session.get("admin"):
        return redirect("/")
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")

# ================= EXPORT =================
@app.route("/export")
def export():
    return Response(
        json.dumps(list(db.captions.find({},{"_id":0})),indent=2),
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
