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
        <input type="password" name="password" placeholder="Admin password"
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
        🔘 Inline Buttons
      </a>

      <a href="/channels" class="bg-white p-4 rounded shadow hover:bg-blue-50">
        📡 Channel Status
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
        <input name="channel" placeholder="Channel ID (blank = default)"
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

# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        rows = []
        for r in request.form.get("rows","").splitlines():
            row=[]
            for b in r.split(","):
                if "|" in b:
                    t,u = b.split("|",1)
                    row.append({"text":t.strip(),"url":u.strip()})
            if row:
                rows.append(row)

        db.captions.update_one(
            {"type":"inline_buttons","channel_id":request.form.get("channel") or "default"},
            {"$set":{"rows":rows}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Inline Buttons", """
    <div class="bg-white p-6 rounded shadow space-y-3">
      <form method="post">
        <input name="channel" placeholder="Channel ID (blank = default)"
          class="w-full border p-2 rounded">

        <textarea name="rows" rows="5"
          class="w-full border p-2 rounded"
          placeholder="Row example:
Google|https://google.com,YouTube|https://youtube.com
Telegram|https://t.me"></textarea>

        <button class="bg-blue-600 text-white px-4 py-2 rounded mt-2">
          Save Buttons
        </button>
      </form>

      <p class="text-sm text-gray-500">
        Use <b>/preview_buttons</b> in Telegram to preview.
      </p>
    </div>
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
          <td class="p-2">
            <a class="text-blue-600" href="/edit/{d['_id']}">Edit</a> |
            <a class="text-red-600" href="/delete/{d['_id']}">Delete</a>
          </td>
        </tr>
        """

    return page("All Captions", f"""
    <div class="bg-white p-4 rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <tr class="bg-gray-200">
          <th class="p-2">Channel</th>
          <th class="p-2">Type</th>
          <th class="p-2">Text</th>
          <th class="p-2">Action</th>
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
