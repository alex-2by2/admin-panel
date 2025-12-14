from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json, db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()

# ---------- TAILWIND PAGE ----------
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

# ---------- RENDER BUTTON ROW (FIX) ----------
def render_row(row):
    inputs = ""
    for b in row:
        inputs += f'''
        <input value="{b["text"]}|{b["url"]}"
          class="w-full border p-2 mb-1 rounded">
        '''

    return f'''
    <div class="border p-2 rounded mb-2 row bg-gray-50" draggable="true">
      {inputs}
      <button type="button"
        onclick="this.parentElement.remove()"
        class="text-red-600 text-sm mt-1">
        ❌ Remove Row
      </button>
    </div>
    '''

# ---------- LOGIN ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")

    return page("Admin Login", """
    <div class="bg-white p-6 rounded shadow max-w-sm mx-auto">
      <form method="post" class="space-y-4">
        <input type="password" name="password"
          placeholder="Admin password"
          class="w-full border p-2 rounded">
        <button class="w-full bg-blue-600 text-white p-2 rounded">
          Login
        </button>
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

      <a href="/add" class="bg-white p-4 rounded shadow hover:bg-blue-50">
        ➕ Add Caption
      </a>

      <a href="/buttons" class="bg-white p-4 rounded shadow hover:bg-blue-50">
        🔘 Inline Buttons (Drag & Drop)
      </a>

      <a href="/all" class="bg-white p-4 rounded shadow hover:bg-blue-50">
        📋 View All Captions
      </a>

      <a href="/export" class="bg-white p-4 rounded shadow hover:bg-blue-50">
        ⬇ Export Backup
      </a>

      <a href="/logout" class="bg-red-500 text-white p-4 rounded shadow">
        Logout
      </a>

    </div>
    """)

# ---------- ADD CAPTION ----------
@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.update_one(
            {
                "type": request.form["type"],
                "channel_id": request.form["channel"] or "default"
            },
            {"$set": {"text": request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption", """
    <div class="bg-white p-6 rounded shadow">
      <form method="post" class="space-y-4">
        <input name="channel"
          placeholder="Channel ID (blank = default)"
          class="w-full border p-2 rounded">

        <select name="type" class="w-full border p-2 rounded">
          <option value="photo_caption">Photo</option>
          <option value="video_caption">Video</option>
          <option value="text_caption">Text</option>
        </select>

        <textarea name="text" rows="4"
          class="w-full border p-2 rounded"
          placeholder="Caption text"></textarea>

        <button class="bg-blue-600 text-white px-4 py-2 rounded">
          Save Caption
        </button>
      </form>
    </div>
    """)

# ---------- INLINE BUTTONS (DRAG & DROP) ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    channel = request.form.get("channel") or request.args.get("channel") or "default"

    if request.method == "POST":
        rows = json.loads(request.form["data"])
        db.captions.update_one(
            {"type":"inline_buttons","channel_id":channel},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect(f"/buttons?channel={channel}")

    data = db.captions.find_one(
        {"type":"inline_buttons","channel_id":channel}
    )
    rows = data["rows"] if data else []

    return page("Inline Buttons (Drag & Drop)", f"""
<div class="bg-white p-4 rounded shadow">
  <form method="post" onsubmit="saveData()">
    <input type="hidden" name="channel" value="{channel}">
    <input type="hidden" name="data" id="data">

    <input value="{channel}" disabled
      class="w-full border p-2 rounded mb-3">

    <div id="rows">
      {"".join(render_row(r) for r in rows)}
    </div>

    <button type="button"
      onclick="addRow()"
      class="bg-gray-200 px-3 py-1 rounded mt-2">
      ➕ Add Row
    </button>

    <br><br>
    <button class="bg-blue-600 text-white px-4 py-2 rounded">
      💾 Save Order
    </button>
  </form>
</div>

<script>
function addRow(){
  const rows=document.getElementById("rows");
  rows.insertAdjacentHTML("beforeend",`
    <div class="border p-2 rounded mb-2 row bg-gray-50" draggable="true">
      <input placeholder="Text|URL"
        class="w-full border p-2 mb-1 rounded">
      <button type="button"
        onclick="this.parentElement.remove()"
        class="text-red-600 text-sm">
        ❌ Remove Row
      </button>
    </div>
  `);
  enableDrag();
}

function saveData(){
  let rows=[];
  document.querySelectorAll(".row").forEach(r=>{
    let row=[];
    r.querySelectorAll("input").forEach(i=>{
      if(i.value.includes("|")){
        let [t,u]=i.value.split("|");
        row.push({text:t.trim(),url:u.trim()});
      }
    });
    if(row.length) rows.push(row);
  });
  document.getElementById("data").value=JSON.stringify(rows);
}

function enableDrag(){
  let dragSrc;
  document.querySelectorAll(".row").forEach(r=>{
    r.ondragstart=e=>dragSrc=r;
    r.ondragover=e=>e.preventDefault();
    r.ondrop=e=>{
      e.preventDefault();
      if(dragSrc!==r){
        r.parentNode.insertBefore(dragSrc,r);
      }
    }
  });
}
enableDrag();
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
        <tr class="border-b">
          <td class="p-2">{d.get("channel_id")}</td>
          <td class="p-2">{d.get("type")}</td>
          <td class="p-2">{str(d.get("text",""))[:40]}</td>
        </tr>
        """

    return page("All Captions", f"""
    <div class="bg-white p-4 rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <tr class="bg-gray-200">
          <th class="p-2">Channel</th>
          <th class="p-2">Type</th>
          <th class="p-2">Text</th>
        </tr>
        {rows}
      </table>
    </div>
    """)

# ---------- EXPORT ----------
@app.route("/export")
def export():
    data=list(db.captions.find({},{"_id":0}))
    return Response(
        json.dumps(data,indent=2),
        mimetype="application/json",
        headers={"Content-Disposition":"attachment;filename=backup.json"}
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
