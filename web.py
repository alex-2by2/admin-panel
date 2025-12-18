from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json
import db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()

# ================= DASHBOARD STATS =================
def dashboard_stats():
    channels = db.captions.distinct("channel_id")
    captions = db.captions.count_documents({
        "type": {"$in": [
            "header", "footer",
            "text_caption", "photo_caption", "video_caption"
        ]}
    })
    btn_doc = db.captions.find_one({"type": "inline_buttons"})
    buttons = len(btn_doc.get("buttons", [])) if btn_doc else 0
    return len(channels), captions, buttons

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
  transition: transform .15s ease, box-shadow .15s ease, opacity .15s ease;
}}
.btn:hover {{
  transform: translateY(-1px);
  box-shadow: 0 6px 14px rgba(0,0,0,.12);
  opacity: .95;
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

.stat {{
  background:#e5f0ff;
  padding:12px;
  border-radius:10px;
  text-align:center;
  flex:1;
  transition: transform .15s ease;
}}
.stat:hover {{
  transform: scale(1.04);
}}

.telegram {{
  background:#e5f0ff;
  padding:12px;
  border-radius:12px;
  white-space:pre-wrap;
}}
.tg-btn {{
  margin-top:6px;
  padding:8px;
  background:white;
  border-radius:8px;
  border:1px solid #cbd5f5;
  text-align:center;
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

    channels, captions, buttons = dashboard_stats()

    return page("Dashboard", f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:15px">
  <div class="stat">📡 Channels<br><b>{channels}</b></div>
  <div class="stat">📝 Captions<br><b>{captions}</b></div>
  <div class="stat">🔘 Buttons<br><b>{buttons}</b></div>
</div>

<h3>📝 Caption Management</h3>
<a href="/add" class="btn">➕ Add Caption / Header / Footer</a>
<a href="/all" class="btn">📋 View / Edit / Delete All</a>
<a href="/duplicate" class="btn gray">📂 Duplicate Captions</a>

<hr>

<h3>🔘 Inline Buttons</h3>
<a href="/buttons" class="btn">Manage Inline Buttons</a>

<hr>

<h3>⚙ Channel Settings</h3>
<a href="/channel-toggle" class="btn gray">🚦 Channel Enable / Disable</a>
<a href="/header-toggle" class="btn gray">🧾 Header ON / OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON / OFF</a>

<hr>

<h3>🧹 Maintenance</h3>
<a href="/bulk-delete" class="btn red">🗑 Bulk Delete</a>
<a href="/export" class="btn">⬇ Export Backup</a>

<hr>
<a href="/logout" class="btn red">Logout</a>
""")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
