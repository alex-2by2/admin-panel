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
            "header","footer",
            "text_caption","photo_caption","video_caption"
        ]}
    })
    btn = db.captions.find_one({"type":"inline_buttons"})
    buttons = len(btn.get("buttons",[])) if btn else 0
    return len(channels), captions, buttons

# ================= PAGE =================
def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --bg:#0f172a;
  --card:#ffffff;
  --accent:#2563eb;
  --danger:#dc2626;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0;
  font-family:system-ui,-apple-system,Arial;
  background:#f1f5f9;
}}
.wrapper {{ display:flex; min-height:100vh; }}

.sidebar {{
  width:260px;
  background:var(--bg);
  color:white;
  padding:18px;
  transition:.25s;
}}
.sidebar.min {{ width:80px; }}

.brand {{
  display:flex;
  justify-content:space-between;
  align-items:center;
  font-size:18px;
  font-weight:700;
  margin-bottom:12px;
}}

.toggle {{
  cursor:pointer;
  font-size:20px;
}}

.sidebar a {{
  display:flex;
  align-items:center;
  gap:10px;
  padding:11px 12px;
  margin:6px 0;
  color:#e5e7eb;
  text-decoration:none;
  border-radius:10px;
  transition:.2s;
}}
.sidebar a:hover {{ background:#1e293b; }}
.sidebar a.active {{ background:var(--accent); }}
.sidebar .danger {{ background:var(--danger); }}

.sidebar.min span {{ display:none; }}

.content {{
  flex:1;
  padding:22px;
}}
.card {{
  background:var(--card);
  padding:22px;
  border-radius:16px;
  box-shadow:0 15px 30px rgba(0,0,0,.08);
}}

.stats {{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:12px;
  margin-bottom:18px;
}}
.stat {{
  background:#eef2ff;
  padding:14px;
  border-radius:12px;
  text-align:center;
  font-weight:600;
}}
.stat span {{
  display:block;
  font-size:22px;
  color:var(--accent);
}}

.btn {{
  display:block;
  padding:13px;
  margin:10px 0;
  background:var(--accent);
  color:white;
  text-decoration:none;
  border-radius:12px;
  text-align:center;
  font-weight:600;
}}
.btn.gray {{ background:#475569; }}
.btn.red {{ background:var(--danger); }}

input,select,textarea {{
  width:100%;
  padding:11px;
  margin:10px 0;
  border-radius:10px;
  border:1px solid #cbd5e1;
}}
button {{
  width:100%;
  padding:13px;
  border:none;
  border-radius:12px;
  background:var(--accent);
  color:white;
  font-size:16px;
  font-weight:600;
  cursor:pointer;
}}

.telegram {{
  background:#e5f0ff;
  border-radius:14px;
  padding:14px;
  white-space:pre-wrap;
}}
.tg-btn {{
  margin-top:6px;
  padding:9px;
  background:white;
  border-radius:10px;
  border:1px solid #cbd5e1;
  text-align:center;
}}

@media(max-width:900px){{
  .sidebar{{position:fixed;left:-260px;height:100%;z-index:99}}
  .sidebar.open{{left:0}}
}}
</style>
</head>

<body>
<div class="wrapper">

<div class="sidebar" id="sidebar">
  <div class="brand">
    🤖 <span>Auto Caption</span>
    <div class="toggle" onclick="toggleSidebar()">☰</div>
  </div>

  <a href="/dashboard" data-p="/dashboard">🏠 <span>Dashboard</span></a>
  <a href="/add" data-p="/add">➕ <span>Add</span></a>
  <a href="/buttons" data-p="/buttons">🔘 <span>Buttons</span></a>
  <a href="/all" data-p="/all">📋 <span>View/Edit</span></a>
  <a href="/duplicate" data-p="/duplicate">📂 <span>Duplicate</span></a>
  <hr>
  <a href="/channel-toggle" data-p="/channel-toggle">🚦 <span>Channel</span></a>
  <a href="/header-toggle" data-p="/header-toggle">🧾 <span>Header</span></a>
  <a href="/footer-toggle" data-p="/footer-toggle">📄 <span>Footer</span></a>
  <a href="/channel-stats" data-p="/channel-stats">📊 <span>Stats</span></a>
  <hr>
  <a href="/bulk-delete" data-p="/bulk-delete">🗑 <span>Bulk</span></a>
  <a href="/export">⬇ <span>Export</span></a>
  <a href="/logout" class="danger">🚪 <span>Logout</span></a>
</div>

<div class="content">
<div class="card">
<h2>{title}</h2>
{body}
</div>
</div>

</div>

<script>
const sb=document.getElementById("sidebar");

// highlight
document.querySelectorAll(".sidebar a[data-p]").forEach(a=>{
  if(location.pathname.startsWith(a.dataset.p)){a.classList.add("active")}
});

// toggle
function toggleSidebar(){
  if(window.innerWidth<900){sb.classList.toggle("open")}
  else{sb.classList.toggle("min")}
}
</script>

</body>
</html>
"""

# ================= LOGIN =================
@app.route("/",methods=["GET","POST"])
def login():
    if request.method=="POST" and request.form.get("password")==ADMIN_PASSWORD:
        session["admin"]=True
        return redirect("/dashboard")
    return "<form method='post' style='max-width:300px;margin:120px auto'><input type=password name=password><button>Login</button></form>"

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"): return redirect("/")
    ch,cap,btn = dashboard_stats()
    return page("Dashboard",f"""
<div class="stats">
<div class="stat">Channels<span>{ch}</span></div>
<div class="stat">Captions<span>{cap}</span></div>
<div class="stat">Buttons<span>{btn}</span></div>
</div>
""")

# ================= EXPORT =================
@app.route("/export")
def export():
    return Response(json.dumps(list(db.captions.find({},{"_id":0})),indent=2),
                    mimetype="application/json")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
