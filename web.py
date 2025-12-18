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


# ================= PAGE + SIDEBAR =================
def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
  margin:0;
  font-family: system-ui, Arial;
  background:#f1f5f9;
}}
.wrapper {{
  display:flex;
  min-height:100vh;
}}
.sidebar {{
  width:240px;
  background:#0f172a;
  color:white;
  padding:16px;
}}
.sidebar h2 {{
  margin-top:0;
  font-size:18px;
}}
.sidebar a {{
  display:block;
  padding:10px;
  margin:6px 0;
  text-decoration:none;
  color:#e5e7eb;
  border-radius:8px;
}}
.sidebar a:hover {{ background:#1e293b; }}
.sidebar a.red {{ background:#dc2626; color:white; }}

.content {{
  flex:1;
  padding:16px;
}}
.card {{
  background:white;
  padding:16px;
  border-radius:12px;
  box-shadow:0 8px 20px rgba(0,0,0,.06);
}}
.btn {{
  display:block;
  padding:12px;
  margin:8px 0;
  background:#2563eb;
  color:white;
  text-decoration:none;
  border-radius:10px;
  text-align:center;
  font-weight:600;
}}
.btn.red {{ background:#dc2626; }}
.btn.gray {{ background:#4b5563; }}

input, textarea, select {{
  width:100%;
  padding:10px;
  margin:8px 0;
  border-radius:8px;
  border:1px solid #cbd5f5;
}}
button {{
  width:100%;
  padding:12px;
  border:none;
  border-radius:10px;
  background:#2563eb;
  color:white;
  font-size:16px;
  font-weight:600;
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

.stat {{
  background:#e5f0ff;
  padding:12px;
  border-radius:10px;
  text-align:center;
  flex:1;
}}

@media(max-width:768px){{
  .wrapper{{flex-direction:column}}
  .sidebar{{width:100%}}
}}
</style>
</head>

<body>
<div class="wrapper">

<div class="sidebar">
<h2>🤖 Admin</h2>
<a href="/dashboard">🏠 Dashboard</a>
<a href="/add">➕ Add Caption</a>
<a href="/buttons">🔘 Inline Buttons</a>
<a href="/all">📋 View / Edit / Delete</a>
<a href="/duplicate">📂 Duplicate Captions</a>
<hr>
<a href="/channel-toggle">🚦 Channel Enable</a>
<a href="/header-toggle">🧾 Header ON / OFF</a>
<a href="/footer-toggle">📄 Footer ON / OFF</a>
<a href="/channel-stats">📊 Channel Stats</a>
<hr>
<a href="/bulk-delete">🗑 Bulk Delete</a>
<a href="/export">⬇ Export</a>
<a href="/logout" class="red">Logout</a>
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
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST" and request.form.get("password")==ADMIN_PASSWORD:
        session["admin"]=True
        return redirect("/dashboard")
    return "<form method='post' style='max-width:300px;margin:100px auto'><input type='password' name='password'><button>Login</button></form>"


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"): return redirect("/")
    ch, cap, btn = dashboard_stats()
    return page("Dashboard", f"""
<div style="display:flex;gap:10px">
<div class="stat">📡 Channels<br><b>{ch}</b></div>
<div class="stat">📝 Captions<br><b>{cap}</b></div>
<div class="stat">🔘 Buttons<br><b>{btn}</b></div>
</div>
""")


# ================= ADD + PREVIEW =================
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"): return redirect("/")
    if request.method=="POST":
        db.captions.update_one(
            {"type":request.form["type"],"channel_id":request.form.get("channel") or "default"},
            {"$set":{"text":request.form["text"]}}, upsert=True)
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

<h3>📱 Preview</h3>
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
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"): return redirect("/")
    if request.method=="POST":
        btns=[]
        for t,u in zip(request.form.getlist("text"),request.form.getlist("url")):
            if t and u: btns.append({"text":t,"url":u})
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"buttons":btns}}, upsert=True)
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
    return page("All Data", f"<table border=1 width=100%>{rows}</table>")


@app.route("/edit/<id>", methods=["GET","POST"])
def edit(id):
    doc=db.captions.find_one({"_id":ObjectId(id)})
    if request.method=="POST":
        db.captions.update_one({"_id":ObjectId(id)},{"$set":{"text":request.form["text"]}})
        return redirect("/all")
    return page("Edit", f"<form method=post><textarea name=text>{doc.get('text','')}</textarea><button>Save</button></form>")


@app.route("/delete/<id>")
def delete(id):
    db.captions.delete_one({"_id":ObjectId(id)})
    return redirect("/all")


# ================= TOGGLES =================
@app.route("/channel-toggle",methods=["GET","POST"])
def channel_toggle():
    if request.method=="POST":
        db.captions.update_one(
            {"type":"channel_status","channel_id":request.form["channel"]},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Channel Enable","<form method=post><input name=channel><label><input type=checkbox name=enabled checked> Enable</label><button>Save</button></form>")


@app.route("/header-toggle",methods=["GET","POST"])
def header_toggle():
    if request.method=="POST":
        db.captions.update_one(
            {"type":"header_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
        return redirect("/dashboard")
    return page("Header Toggle","<form method=post><input name=channel><label><input type=checkbox name=enabled checked> Enable</label><button>Save</button></form>")


@app.route("/footer-toggle",methods=["GET","POST"])
def footer_toggle():
    if request.method=="POST":
        db.captions.update_one(
            {"type":"footer_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":"enabled" in request.form}},upsert=True)
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


# ================= PER CHANNEL STATS =================
@app.route("/channel-stats")
def channel_stats():
    rows=""
    for ch in db.captions.distinct("channel_id"):
        rows+=f"<tr><td>{ch}</td><td>{db.captions.count_documents({'channel_id':ch})}</td></tr>"
    return page("Channel Stats", f"<table border=1 width=100%><tr><th>Channel</th><th>Total Items</th></tr>{rows}</table>")


# ================= EXPORT =================
@app.route("/export")
def export():
    return Response(json.dumps(list(db.captions.find({},{"_id":0})),indent=2),mimetype="application/json")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
