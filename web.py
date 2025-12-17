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


# ---------- MODERN PAGE ----------
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
      background: #f4f6f8;
      margin: 0;
    }}
    .header {{
      background: #1f2937;
      color: white;
      padding: 14px;
      font-size: 18px;
      font-weight: bold;
    }}
    .box {{
      max-width: 900px;
      margin: auto;
      padding: 15px;
    }}
    .card {{
      background: white;
      border-radius: 10px;
      padding: 15px;
      box-shadow: 0 2px 6px rgba(0,0,0,.1);
    }}
    .btn {{
      display: block;
      padding: 12px;
      margin-bottom: 10px;
      text-align: center;
      border-radius: 8px;
      background: #2563eb;
      color: white;
      text-decoration: none;
      font-weight: 500;
    }}
    .btn.red {{ background: #dc2626; }}
    .btn.gray {{ background: #4b5563; }}
    input, textarea, select {{
      width: 100%;
      padding: 10px;
      margin-top: 8px;
      margin-bottom: 12px;
    }}
    button {{
      width: 100%;
      padding: 12px;
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
    }}
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


# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")

    return page("Login", """
<form method="post">
<input type="password" name="password" placeholder="Admin password">
<button>Login</button>
</form>
""")


# ---------- DASHBOARD (FIXED) ----------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    return page("Dashboard", """
<a href="/add" class="btn">➕ Add Caption / Header / Footer</a>
<a href="/buttons" class="btn">🔘 Inline Buttons</a>
<a href="/header-toggle" class="btn gray">🧾 Header ON / OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON / OFF</a>
<a href="/channel-toggle" class="btn gray">🚦 Channel Enable</a>
<a href="/all" class="btn">📋 View / Edit All</a>
<a href="/bulk-delete" class="btn red">🗑 Bulk Delete</a>
<a href="/export" class="btn">⬇ Export</a>
<a href="/logout" class="btn red">Logout</a>
""")


# ---------- ADD ----------
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
<input name="channel" placeholder="Channel ID (blank = default)">

<select name="type">
  <option value="header">Header</option>
  <option value="footer">Footer</option>
  <option value="text_caption">Text</option>
  <option value="photo_caption">Photo</option>
  <option value="video_caption">Video</option>
</select>

<textarea name="text" rows="4"></textarea>
<button>Save</button>
</form>
""")


# ---------- VIEW ALL ----------
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")

    import db
    rows = ""

    for d in db.captions.find():
        rows += f"""
<tr>
<td>{d.get("channel_id")}</td>
<td>{d.get("type")}</td>
<td>{str(d.get("text",""))[:40]}</td>
<td>
<a href="/edit/{d['_id']}">Edit</a> |
<a href="/delete/{d['_id']}">Delete</a>
</td>
</tr>
"""

    return page("All Saved Data", f"""
<table border="1" width="100%">
<tr><th>Channel</th><th>Type</th><th>Text</th><th>Action</th></tr>
{rows}
</table>
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

    return page("Edit", f"""
<form method="post">
<textarea name="text" rows="4">{doc.get("text","")}</textarea>
<button>Save</button>
</form>
""")


# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    import db
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")


# ---------- HEADER TOGGLE ----------
@app.route("/header-toggle", methods=["GET","POST"])
def header_toggle():
    if not session.get("admin"):
        return redirect("/")

    import db
    if request.method == "POST":
        db.captions.update_one(
            {"type":"header_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Header Toggle", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)">
<label><input type="checkbox" name="enabled" checked> Enable Header</label>
<button>Save</button>
</form>
""")


# ---------- FOOTER TOGGLE ----------
@app.route("/footer-toggle", methods=["GET","POST"])
def footer_toggle():
    if not session.get("admin"):
        return redirect("/")

    import db
    if request.method == "POST":
        db.captions.update_one(
            {"type":"footer_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Footer Toggle", """
<form method="post">
<input name="channel" placeholder="Channel ID (blank = default)">
<label><input type="checkbox" name="enabled" checked> Enable Footer</label>
<button>Save</button>
</form>
""")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
