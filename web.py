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

    return page("Dashboard", """
<!-- ===== STATS ===== -->
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:15px">
  <div class="stat">📡 Channels<br><b>{{channels}}</b></div>
  <div class="stat">📝 Captions<br><b>{{captions}}</b></div>
  <div class="stat">🔘 Buttons<br><b>{{buttons}}</b></div>
</div>

<!-- ===== CAPTION MANAGEMENT ===== -->
<h3>📝 Caption Management</h3>
<a href="/add" class="btn">➕ Add Caption / Header / Footer</a>
<a href="/all" class="btn">📋 View / Edit / Delete All</a>
<a href="/duplicate" class="btn gray">📂 Duplicate Captions</a>

<hr>

<!-- ===== BUTTONS ===== -->
<h3>🔘 Inline Buttons</h3>
<a href="/buttons" class="btn">Manage Inline Buttons</a>

<hr>

<!-- ===== SETTINGS ===== -->
<h3>⚙ Channel Settings</h3>
<a href="/channel-toggle" class="btn gray">🚦 Channel Enable / Disable</a>
<a href="/header-toggle" class="btn gray">🧾 Header ON / OFF</a>
<a href="/footer-toggle" class="btn gray">📄 Footer ON / OFF</a>

<hr>

<!-- ===== MAINTENANCE ===== -->
<h3>🧹 Maintenance</h3>
<a href="/bulk-delete" class="btn red">🗑 Bulk Delete (Per Channel)</a>
<a href="/export" class="btn">⬇ Export Backup</a>

<hr>

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
<form method="post" oninput="preview()">
<input name="channel" placeholder="Channel ID (blank = default)">
<select id="type" name="type" onchange="preview()">
  <option value="header">Header</option>
  <option value="footer">Footer</option>
  <option value="text_caption">Text Caption</option>
  <option value="photo_caption">Photo Caption</option>
  <option value="video_caption">Video Caption</option>
</select>
<textarea id="text" name="text" rows="4" placeholder="Write text..."></textarea>
<button>Save</button>
</form>

<h3>📱 Preview</h3>
<div class="telegram" id="preview">Nothing to preview…</div>

<script>
function preview(){
  let t=document.getElementById("text").value.trim();
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
            {"$set":{"buttons":btns}},upsert=True)
        return redirect("/dashboard")

    return page("Inline Buttons", """
<form method="post">
<input name="channel" placeholder="Channel ID">
<input name="text" placeholder="Button Text">
<input name="url" placeholder="https://example.com">
<button>Save</button>
</form>
<h3>Preview</h3>
<div class="telegram"><div class="tg-btn">Button</div></div>
""")

# ================= VIEW / EDIT / DELETE =================
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
<td><a href="/edit/{d['_id']}">Edit</a> | <a href="/delete/{d['_id']}">Delete</a></td>
</tr>
"""
    return page("All Data", f"<table border=1 width=100%>{rows}</table><a href='/dashboard' class='btn gray'>Back</a>")

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
    return page("Duplicate","<form method=post><input name=source placeholder='Source'><input name=target placeholder='Target'><button>Duplicate</button></form>")
# ================= PER CHANNEL STATS =================
@app.route("/channel-stats")
def channel_stats():
    if not session.get("admin"):
        return redirect("/")

    rows = ""

    channels = db.captions.distinct("channel_id")

    for ch in channels:
        total = db.captions.count_documents({"channel_id": ch})

        headers = db.captions.count_documents({
            "channel_id": ch, "type": "header"
        })
        footers = db.captions.count_documents({
            "channel_id": ch, "type": "footer"
        })
        texts = db.captions.count_documents({
            "channel_id": ch, "type": "text_caption"
        })
        photos = db.captions.count_documents({
            "channel_id": ch, "type": "photo_caption"
        })
        videos = db.captions.count_documents({
            "channel_id": ch, "type": "video_caption"
        })

        btn = db.captions.find_one({
            "channel_id": ch, "type": "inline_buttons"
        })
        buttons = len(btn.get("buttons", [])) if btn else 0

        rows += f"""
        <tr>
          <td>{ch}</td>
          <td>{total}</td>
          <td>{headers}</td>
          <td>{footers}</td>
          <td>{texts}</td>
          <td>{photos}</td>
          <td>{videos}</td>
          <td>{buttons}</td>
        </tr>
        """

    return page("📊 Per Channel Stats", f"""
<table border="1" width="100%" cellpadding="8">
<tr>
<th>Channel ID</th>
<th>Total</th>
<th>Header</th>
<th>Footer</th>
<th>Text</th>
<th>Photo</th>
<th>Video</th>
<th>Buttons</th>
</tr>
{rows}
</table>

<a href="/dashboard" class="btn gray">← Back</a>
""")
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
