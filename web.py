from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json, db

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
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
<div class="max-w-5xl mx-auto p-4">
  <h1 class="text-2xl font-bold mb-4">{title}</h1>
  {body}
</div>
</body>
</html>
"""

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")

    return page("Admin Login", """
<div class="bg-white p-6 rounded shadow max-w-sm mx-auto">
<form method="post">
<input type="password" name="password" placeholder="Admin password"
 class="w-full border p-2 rounded mb-3">
<button class="w-full bg-blue-600 text-white p-2 rounded">Login</button>
</form>
</div>
""")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return page("Dashboard", """
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
<a href="/add" class="bg-white p-4 rounded shadow">➕ Add Caption</a>
<a href="/buttons" class="bg-white p-4 rounded shadow">🔘 Inline Buttons</a>
<a href="/all" class="bg-white p-4 rounded shadow">📋 View All</a>
<a href="/export" class="bg-white p-4 rounded shadow">⬇ Export</a>
<a href="/logout" class="bg-red-500 text-white p-4 rounded shadow">Logout</a>
</div>
""")

# ---------- ADD CAPTION ----------
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")
    if request.method == "POST":
        db.captions.update_one(
            {"type":request.form["type"],
             "channel_id":request.form["channel"] or "default"},
            {"$set":{"text":request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption", """
<div class="bg-white p-6 rounded shadow">
<form method="post">
<input name="channel" placeholder="Channel ID (default)"
 class="w-full border p-2 rounded mb-2">
<select name="type" class="w-full border p-2 rounded mb-2">
<option value="photo_caption">Photo</option>
<option value="video_caption">Video</option>
<option value="text_caption">Text</option>
</select>
<textarea name="text" class="w-full border p-2 rounded mb-2"
 placeholder="Caption text"></textarea>
<button class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
</form>
</div>
""")

# ---------- INLINE BUTTONS (SAFE JS) ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    channel = request.form.get("channel") or "default"

    if request.method == "POST":
        rows = json.loads(request.form["data"])
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":channel},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect("/buttons")

    data = db.captions.find_one({"type":"inline_buttons","channel_id":channel})
    rows = data["rows"] if data else []

    rows_html = ""
    for r in rows:
        inputs=""
        for b in r:
            inputs += f'<input value="{b["text"]}|{b["url"]}" class="w-full border p-2 mb-1">'
        rows_html += f'''
<div class="row border p-2 rounded mb-2" draggable="true">
{inputs}
<button type="button" onclick="this.parentElement.remove()">❌</button>
</div>
'''

    return page("Inline Buttons", f"""
<div class="bg-white p-4 rounded shadow">
<form method="post" onsubmit="saveData()">
<input type="hidden" name="channel" value="{channel}">
<input type="hidden" name="data" id="data">

<div id="rows">
{rows_html}
</div>

<button type="button" onclick="addRow()"
 class="bg-gray-200 px-3 py-1 rounded">➕ Add Row</button>

<br><br>
<button class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
</form>
</div>

<script>
function addRow(){{
  document.getElementById("rows").insertAdjacentHTML("beforeend",
    '<div class="row border p-2 rounded mb-2" draggable="true">' +
    '<input placeholder="Text|URL" class="w-full border p-2 mb-1">' +
    '<button type="button" onclick="this.parentElement.remove()">❌</button>' +
    '</div>'
  );
}}

function saveData(){{
  let rows=[];
  document.querySelectorAll(".row").forEach(r=>{
    let row=[];
    r.querySelectorAll("input").forEach(i=>{
      if(i.value.includes("|")){{
        let p=i.value.split("|");
        row.push({{text:p[0],url:p[1]}});
      }}
    });
    if(row.length) rows.push(row);
  });
  document.getElementById("data").value=JSON.stringify(rows);
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
        rows+=f"<tr><td>{d.get('channel_id')}</td><td>{d.get('type')}</td></tr>"
    return page("All", f"<table class='bg-white'>{rows}</table>")

# ---------- EXPORT ----------
@app.route("/export")
def export():
    data=list(db.captions.find({},{"_id":0}))
    return Response(json.dumps(data,indent=2),
        mimetype="application/json",
        headers={"Content-Disposition":"attachment;filename=backup.json"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
