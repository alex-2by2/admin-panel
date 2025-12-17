from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json
import db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()

# ---------- PAGE ----------
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
  font-size: 15px;
  white-space: pre-wrap;
}}

.tg-btn {{
  display: block;
  margin-top: 6px;
  padding: 8px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #cbd5f5;
  text-align: center;
  font-size: 14px;
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

# ---------- LOGIN ----------
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

# ---------- DASHBOARD ----------
return page("Dashboard", """
<a href="/add" class="btn">➕ Add Caption / Header / Footer</a>
<a href="/buttons" class="btn">🔘 Inline Buttons</a>
<a href="/all" class="btn">📋 View / Edit / Delete</a>

<hr>

<a href="/channel-toggle" class="btn gray">🚦 Channel Enable / Disable</a>
<a href="/header-toggle" class="btn gray">🧾 Header ON / OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON / OFF</a>

<hr>

<a href="/bulk-delete" class="btn red">🗑 Bulk Delete</a>
<a href="/export" class="btn">⬇ Export Backup</a>

<a href="/logout" class="btn red">Logout</a>
""")
# ---------- ADD + TELEGRAM PREVIEW ----------
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

<textarea id="text" name="text" rows="4" placeholder="Write caption..." oninput="preview()"></textarea>

<button>Save</button>
</form>

<h3>📱 Telegram Preview</h3>
<div class="telegram" id="preview">
Nothing to preview…
</div>

<div id="buttons"></div>

<script>
function preview() {{
  let text = document.getElementById("text").value;
  let type = document.getElementById("type").value;

  if (!text.trim()) {{
    document.getElementById("preview").innerText = "Nothing to preview…";
    return;
  }}

  let result = "";
  if (type.includes("caption")) {{
    result = text;
  }} else {{
    result = text;
  }}

  document.getElementById("preview").innerText = result;
}}
</script>
""")

# ---------- INLINE BUTTONS + PREVIEW ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        btns=[]
        for t,u in zip(request.form.getlist("text"), request.form.getlist("url")):
            if t and u:
                btns.append({"text":t,"url":u})

        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"buttons":btns}}, upsert=True
        )
        return redirect("/dashboard")

    return page("Inline Buttons", """
<form method="post" oninput="previewButtons()">
<input name="channel" placeholder="Channel ID (blank = default)">
<input id="bt1" name="text" placeholder="Button Text">
<input id="bu1" name="url" placeholder="https://example.com">
<button>Save</button>
</form>

<h3>📱 Button Preview</h3>
<div class="telegram">
  <div class="tg-btn" id="pbtn">Button Preview</div>
</div>

<script>
function previewButtons() {{
  let t = document.getElementById("bt1").value;
  document.getElementById("pbtn").innerText = t || "Button Preview";
}}
</script>
""")

# ---------- VIEW ALL ----------
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")
    rows=""
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

# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    db.captions.delete_one({"_id":ObjectId(id)})
    return redirect("/all")

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
