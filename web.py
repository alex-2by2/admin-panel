from flask import Flask, request, redirect, session, Response
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
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")

    return page("Admin Login", """
<div class="bg-white p-6 rounded shadow max-w-sm mx-auto">
  <form method="post" class="space-y-4">
    <input type="password" name="password" placeholder="Admin password"
      class="w-full border p-2 rounded">
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
            {
                "type": request.form["type"],
                "channel_id": request.form.get("channel") or "default"
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
  <textarea name="text" rows="4" class="w-full border p-2 rounded"
    placeholder="Caption text"></textarea>
  <button class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
</form>
</div>
""")

# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    channel = request.form.get("channel") or "default"

    if request.method == "POST":
        buttons = []
        texts = request.form.getlist("text")
        urls = request.form.getlist("url")
        for t,u in zip(texts, urls):
            if t and u:
                buttons.append({"text": t, "url": u})

        db.captions.update_one(
            {"type":"inline_buttons","channel_id":channel},
            {"$set":{"buttons":buttons}},
            upsert=True
        )
        return redirect("/buttons")

    return page("Inline Buttons", """
<div class="bg-white p-6 rounded shadow">
<form method="post" class="space-y-3">
  <input name="channel" placeholder="Channel ID (blank = default)"
    class="w-full border p-2 rounded">

  <input name="text" placeholder="Button Text" class="w-full border p-2 rounded">
  <input name="url" placeholder="Button URL (https://...)" class="w-full border p-2 rounded">

  <button class="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
</form>
</div>
""")

# ---------- VIEW ALL ----------
@app.route("/all")
def all_items():
    if not session.get("admin"):
        return redirect("/")

    rows = ""
    for d in db.captions.find():
        rows += f"<tr><td>{d.get('channel_id')}</td><td>{d.get('type')}</td></tr>"

    return page("All Captions", f"""
<div class="bg-white p-4 rounded shadow">
<table class="w-full border">
<tr><th>Channel</th><th>Type</th></tr>
{rows}
</table>
</div>
""")

# ---------- EXPORT ----------
@app.route("/export")
def export():
    data = list(db.captions.find({}, {"_id":0}))
    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition":"attachment;filename=backup.json"}
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))
