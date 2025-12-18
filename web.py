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
  --muted:#94a3b8;
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
  width:250px;
  background:var(--bg);
  color:white;
  padding:18px;
}}
.sidebar h2 {{
  margin:0 0 15px;
  font-size:20px;
}}
.sidebar a {{
  display:flex;
  align-items:center;
  gap:8px;
  padding:11px 12px;
  margin:6px 0;
  color:#e5e7eb;
  text-decoration:none;
  border-radius:10px;
  transition:.2s;
}}
.sidebar a:hover {{ background:#1e293b; }}
.sidebar .danger {{ background:var(--danger); }}

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

h2 {{ margin-top:0; }}

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
  font-size:15px;
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

table {{
  width:100%;
  border-collapse:collapse;
  margin-top:12px;
}}
th,td {{
  padding:10px;
  border-bottom:1px solid #e5e7eb;
  font-size:14px;
}}
th {{ background:#f8fafc; }}

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
  font-size:14px;
}}

@media(max-width:900px){{
  .wrapper{{flex-direction:column}}
  .sidebar{{width:100%}}
}}
</style>
</head>

<body>
<div class="wrapper">

<div class="sidebar">
<h2>🤖 Auto Caption</h2>
<a href="/dashboard">🏠 Dashboard</a>
<a href="/add">➕ Add Caption</a>
<a href="/buttons">🔘 Inline Buttons</a>
<a href="/all">📋 View / Edit</a>
<a href="/duplicate">📂 Duplicate</a>
<hr>
<a href="/channel-toggle">🚦 Channel Enable</a>
<a href="/header-toggle">🧾 Header ON/OFF</a>
<a href="/footer-toggle">📄 Footer ON/OFF</a>
<a href="/channel-stats">📊 Channel Stats</a>
<hr>
<a href="/bulk-delete">🗑 Bulk Delete</a>
<a href="/export">⬇ Export</a>
<a href="/logout" class="danger">Logout</a>
</div>

<div class="content">
<div class="card">
<h2>{title}</h2>
{body}
</div>
</div>

</div>
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

# ================= ADD =================
@app.route("/add",methods=["GET","POST"])
def add():
    if not session.get("admin"): return redirect("/")
    if request.method=="POST":
        db.captions.update_one(
            {"type":request.form["type"],"channel_id":request.form.get("channel") or "default"},
            {"$set":{"text":request.form["text"]}},upsert=True)
        return redirect("/dashboard")
    return page("Add Caption", """
<form method="post" oninput="preview()">
<input name="channel" placeholder="Channel ID">
<select id="type" name="type">
<option value="header">Header</option>
<option value="footer">Footer</option>
<option value="text_caption">Text</option>
<option value="photo_caption">Photo</option>
<option value="video_caption">Video</option>
</select>
<textarea id="text" name="text"></textarea>
<button>Save</button>
</form>

<h3>Preview</h3>
<div class="telegram" id="preview">Nothing to preview…</div>

<script>
function preview(){
 let t=text.value.trim();
 let type=document.getElementById("type").value;
 if(!t){preview.innerText="Nothing to preview…";return;}
 if(type==="header"||type==="footer"){preview.innerText=t;}
 else preview.innerText="[HEADER]\\n\\n"+t+"\\n\\n[FOOTER]";
}
</script>
""")

# ================= INLINE BUTTONS =================
@app.route("/buttons",methods=["GET","POST"])
def buttons():
    if not session.get("admin"): return redirect("/")
    if request.method=="POST":
        btns=[]
        for t,u in zip(request.form.getlist("text"),request.form.getlist("url")):
            if t and u: btns.append({"text":t,"url":u})
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"buttons":btns}},upsert=True)
        return redirect("/dashboard")
    return page("Inline Buttons", """
<form method="post">
<input name="channel">
<input name="text">
<input name="url">
<button>Save</button>
</form>
<div class="telegram"><div class="tg-btn">Button</div></div>
""")

# ================= VIEW / EDIT / DELETE =================
@app.route("/all")
def all_items():
    if not session.get("admin"): return redirect("/")
    rows=""
    for d in db.captions.find():
        rows+=f"<tr><td>{d.get('channel_id')}</td><td>{d.get('type')}</td><td>{str(d.get('text',''))[:30]}</td><td><a href='/edit/{d['_id']}'>Edit</a> | <a href='/delete/{d['_id']}'>Delete</a></td></tr>"
    return page("All Data",f"<table><tr><th>Channel</th><th>Type</th><th>Text</th><th>Action</th></tr>{rows}</table>")

@app.route("/edit/<id>",methods=["GET","POST"])
def edit(id):
    doc=db.captions.find_one({"_id":ObjectId(id)})
    if request.method=="POST":
        db.captions.update_one({"_id":ObjectId(id)},{"$set":{"text":request.form["text"]}})
        return redirect("/all")
    return page("Edit",f"<form method=post><textarea name=text>{doc.get('text','')}</textarea><button>Save</button></form>")

@app.route("/delete/<id>")
def delete(id):
    db.captions.delete_one({"_id":ObjectId(id)})
    return redirect("/all")

# ================= TOGGLES =================
@app.route("/channel-toggle",methods=["GET","POST"])
def channel_toggle():
    if request.method=="POST":
        db.captions.update_one({"type":"channel_status","channel_id":request.form["channel"]},
                               {"$set":{"enabled":"enabled"in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Channel Enable","<form method=post><input name=channel><label><input type=checkbox name=enabled checked> Enable</label><button>Save</button></form>")

@app.route("/header-toggle",methods=["GET","POST"])
def header_toggle():
    if request.method=="POST":
        db.captions.update_one({"type":"header_status","channel_id":request.form.get("channel") or "default"},
                               {"$set":{"enabled":"enabled"in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Header Toggle","<form method=post><input name=channel><label><input type=checkbox name=enabled checked> Enable</label><button>Save</button></form>")

@app.route("/footer-toggle",methods=["GET","POST"])
def footer_toggle():
    if request.method=="POST":
        db.captions.update_one({"type":"footer_status","channel_id":request.form.get("channel") or "default"},
                               {"$set":{"enabled":"enabled"in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Footer Toggle","<form method=post><input name=channel><label><input type=checkbox name=enabled checked> Enable</label><button>Save</button></form>")

# ================= BULK DELETE =================
@app.route("/bulk-delete",methods=["GET","POST"])
def bulk_delete():
    if request.method=="POST":
        db.captions.delete_many({"channel_id":request.form["channel"]})
        return redirect("/dashboard")
    return page("Bulk Delete","<form method=post><input name=channel><button class='btn red'>DELETE ALL</button></form>")

# ================= DUPLICATE =================
@app.route("/duplicate",methods=["GET","POST"])
def duplicate():
    if request.method=="POST":
        src=request.form["source"]; tgt=request.form["target"]
        db.captions.delete_many({"channel_id":tgt})
        for d in db.captions.find({"channel_id":src}):
            d.pop("_id"); d["channel_id"]=tgt; db.captions.insert_one(d)
        return redirect("/dashboard")
    return page("Duplicate","<form method=post><input name=source><input name=target><button>Duplicate</button></form>")

# ================= STATS =================
@app.route("/channel-stats")
def channel_stats():
    rows=""
    for ch in db.captions.distinct("channel_id"):
        rows+=f"<tr><td>{ch}</td><td>{db.captions.count_documents({'channel_id':ch})}</td></tr>"
    return page("Channel Stats",f"<table><tr><th>Channel</th><th>Total</th></tr>{rows}</table>")

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
