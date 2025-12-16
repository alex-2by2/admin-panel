from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# ---------- DB INIT ----------
try:
    import db
    db.init_db()
    DB_OK = True
except Exception as e:
    print("DB init failed:", e)
    DB_OK = False


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
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
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

    if not DB_OK:
        return page("Error", "<p>MongoDB not connected</p>")

    return page("Dashboard", """
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">

<a href="/add" class="bg-white p-4 rounded shadow hover:bg-blue-50">
➕ Add Caption
</a>

<a href="/buttons" class="bg-white p-4 rounded shadow hover:bg-blue-50">
🔘 Inline Buttons
</a>

<a href="/all" class="bg-white p-4 rounded shadow hover:bg-blue-50">
📋 View All Captions
</a>

<a href="/channels" class="bg-white p-4 rounded shadow hover:bg-blue-50">
📡 Saved Channel IDs
</a>

<a href="/export" class="bg-white p-4 rounded shadow hover:bg-blue-50">
⬇ Export Backup
</a>
<a href="/bulk-delete" class="bg-red-100 p-4 rounded shadow hover:bg-red-200">
🗑 Bulk Delete (Per Channel)
</a>
<a href="/channel-toggle" class="bg-white p-4 rounded shadow hover:bg-blue-50">
🚦 Enable / Disable Channel
</a>


<a href="/logout" class="bg-red-500 text-white p-4 rounded shadow">
Logout
</a>

</div>
""")


# ---------- ADD CAPTION ----------
@app.route("/add", methods=["GET", "POST"])
def add():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        db.captions.update_one(
            {
                "type": request.form["type"],
                "channel_id": request.form.get("channel_id") or "default"
            },
            {"$set": {"text": request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption", """
<div class="bg-white p-6 rounded shadow">
<form method="post" class="space-y-3">

<input name="channel_id"
  placeholder="Channel ID (empty = default)"
  class="w-full border p-2 rounded">

<select name="type" class="w-full border p-2 rounded">
  <option value="photo_caption">Photo</option>
  <option value="video_caption">Video</option>
  <option value="text_caption">Text</option>
</select>

<textarea name="text"
  rows="4"
  placeholder="Caption text"
  class="w-full border p-2 rounded"></textarea>

<button class="bg-blue-600 text-white px-4 py-2 rounded">
Save Caption
</button>

</form>
</div>
""")


# ---------- INLINE BUTTONS (SAFE) ----------
@app.route("/buttons", methods=["GET", "POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    import db

    channel_id = request.form.get("channel_id") or "default"

    # ---------- SAVE ----------
    if request.method == "POST":
        buttons = []

        texts = request.form.getlist("text")
        urls = request.form.getlist("url")

        for t, u in zip(texts, urls):
            if t and u:
                buttons.append({"text": t.strip(), "url": u.strip()})

        db.captions.update_one(
            {"type": "inline_buttons", "channel_id": channel_id},
            {"$set": {"buttons": buttons}},
            upsert=True
        )
        return redirect("/buttons")

    # ---------- LOAD ----------
    doc = db.captions.find_one(
        {"type": "inline_buttons", "channel_id": channel_id}
    )
    buttons = doc["buttons"] if doc and "buttons" in doc else []

    rows = ""
    for b in buttons:
        rows += f"""
        <input name="text" value="{b['text']}" placeholder="Button Text">
        <input name="url" value="{b['url']}" placeholder="https://example.com">
        <hr>
        """

    return page("Inline Buttons", f"""
    <h2>Inline Buttons (Stable Mode)</h2>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (blank = default)">
      <hr>

      {rows}

      <input name="text" placeholder="Button Text">
      <input name="url" placeholder="https://example.com">

      <br><br>
      <button>Save Buttons</button>
    </form>

    <p><b>Note:</b> Buttons appear in one column (safe mode)</p>
    <a href="/dashboard">⬅ Back</a>
    """)
# ---------- EDIT ----------
@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    doc = db.captions.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db.captions.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"text": request.form["text"]}}
        )
        return redirect("/all")

    return page("Edit Caption", f"""
<div class="bg-white p-6 rounded shadow">
<form method="post" class="space-y-3">

<p><b>Channel:</b> {doc.get("channel_id")}</p>
<p><b>Type:</b> {doc.get("type")}</p>

<textarea name="text"
  rows="4"
  class="w-full border p-2 rounded">{doc.get("text","")}</textarea>

<button class="bg-blue-600 text-white px-4 py-2 rounded">
Save
</button>

</form>

<a href="/all" class="text-blue-600 block mt-3">← Back</a>
</div>
""")


# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/")

    import db
    db.captions.delete_one({"_id": ObjectId(id)})
    return redirect("/all")


# ---------- CHANNEL LIST ----------
@app.route("/channels")
def channels():
    if not session.get("admin"):
        return redirect("/")

    import db
    items = "".join(f"<li>{c}</li>" for c in db.captions.distinct("channel_id"))

    return page("Channels", f"""
<div class="bg-white p-4 rounded shadow">
<ul class="list-disc pl-5">
{items}
</ul>
<a href="/dashboard" class="text-blue-600 block mt-3">← Back</a>
</div>
""")
# ---------- BULK DELETE PER CHANNEL ----------
@app.route("/bulk-delete", methods=["GET", "POST"])
def bulk_delete():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id")

        if channel_id:
            db.captions.delete_many({"channel_id": channel_id})

        return redirect("/dashboard")

    return page("Bulk Delete", """
    <div class="bg-white p-6 rounded shadow max-w-md mx-auto">
      <form method="post" class="space-y-3">
        <input name="channel_id"
          placeholder="Channel ID (example: -1001234567890)"
          class="w-full border p-2 rounded">

        <button class="bg-red-600 text-white px-4 py-2 rounded w-full">
          ⚠ Delete ALL captions of this channel
        </button>
      </form>

      <p class="text-sm text-gray-500 mt-3">
        This will permanently delete:
        photo, video, text captions & inline buttons.
      </p>

      <a href="/dashboard" class="text-blue-600 block mt-4">
        ← Back
      </a>
    </div>
    """)

# ---------- CHANNEL ENABLE / DISABLE ----------
@app.route("/channel-toggle", methods=["GET", "POST"])
def channel_toggle():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id")
        enabled = True if request.form.get("enabled") == "on" else False

        db.captions.update_one(
            {"type": "channel_status", "channel_id": channel_id},
            {"$set": {"enabled": enabled}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Channel Enable / Disable", """
    <div class="bg-white p-6 rounded shadow max-w-md mx-auto">
      <form method="post" class="space-y-3">

        <input name="channel_id"
          placeholder="Channel ID (e.g. -1001234567890)"
          class="w-full border p-2 rounded">

        <label class="flex items-center gap-2">
          <input type="checkbox" name="enabled" checked>
          Enable bot for this channel
        </label>

        <button class="bg-blue-600 text-white px-4 py-2 rounded w-full">
          Save
        </button>

      </form>

      <a href="/dashboard" class="text-blue-600 block mt-4">
        ← Back
      </a>
    </div>
    """)
# ---------- EXPORT ----------
@app.route("/export")
def export():
    if not session.get("admin"):
        return redirect("/")

    import db
    data = list(db.captions.find({}, {"_id": 0}))

    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=captions_backup.json"}
    )


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
