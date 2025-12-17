from flask import Flask, request, redirect, session, Response
from bson import ObjectId
import os, json, db

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
db.init_db()


def page(title, body):
    return f"""
<!doctype html>
<html>
<head>
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">

<div class="max-w-4xl mx-auto p-4">
<h1 class="text-xl font-bold mb-4">{title}</h1>
{body}
</div>

</body>
</html>
"""


@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form["password"] == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect("/dashboard")

    return page("Login", """
<form method="post" class="bg-white p-6 rounded shadow max-w-sm mx-auto">
<input type="password" name="password" class="border p-2 w-full mb-3">
<button class="bg-blue-600 text-white p-2 w-full">Login</button>
</form>
""")


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    return page("Dashboard", """
<div class="grid grid-cols-1 gap-3">
<a href="/add" class="bg-white p-3 rounded shadow">➕ Add Caption / Header</a>
<a href="/buttons" class="bg-white p-3 rounded shadow">🔘 Inline Buttons</a>
<a href="/header-toggle" class="bg-white p-3 rounded shadow">🧾 Header ON / OFF</a>
<a href="/channel-toggle" class="bg-white p-3 rounded shadow">🚦 Channel Enable</a>
<a href="/bulk-delete" class="bg-red-100 p-3 rounded shadow">🗑 Bulk Delete</a>
<a href="/logout" class="bg-red-500 text-white p-3 rounded shadow">Logout</a>
</div>
""")


@app.route("/add", methods=["GET","POST"])
def add():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.update_one(
            {"type":request.form["type"],"channel_id":request.form.get("channel") or "default"},
            {"$set":{"text":request.form["text"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Add Caption/Header", """
<form method="post" class="bg-white p-6 rounded shadow">
<input name="channel" placeholder="Channel ID (blank=default)" class="border p-2 w-full mb-2">
<select name="type" class="border p-2 w-full mb-2">
<option value="header">Header</option>
<option value="text_caption">Text</option>
<option value="photo_caption">Photo</option>
<option value="video_caption">Video</option>
</select>
<textarea name="text" class="border p-2 w-full mb-2"></textarea>
<button class="bg-blue-600 text-white p-2 w-full">Save</button>
</form>
""")


@app.route("/header-toggle", methods=["GET","POST"])
def header_toggle():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.update_one(
            {"type":"header_status","channel_id":request.form.get("channel") or "default"},
            {"$set":{"enabled":bool(request.form.get("enabled"))}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Header Toggle", """
<form method="post" class="bg-white p-6 rounded shadow">
<input name="channel" placeholder="Channel ID (blank=default)" class="border p-2 w-full mb-2">
<label><input type="checkbox" name="enabled" checked> Enable Header</label>
<button class="bg-blue-600 text-white p-2 w-full mt-3">Save</button>
</form>
""")


@app.route("/channel-toggle", methods=["GET","POST"])
def channel_toggle():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.update_one(
            {"type":"channel_status","channel_id":request.form["channel"]},
            {"$set":{"enabled":bool(request.form.get("enabled"))}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Channel Enable", """
<form method="post" class="bg-white p-6 rounded shadow">
<input name="channel" class="border p-2 w-full mb-2">
<label><input type="checkbox" name="enabled" checked> Enable Bot</label>
<button class="bg-blue-600 text-white p-2 w-full mt-3">Save</button>
</form>
""")


@app.route("/bulk-delete", methods=["GET","POST"])
def bulk():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        db.captions.delete_many({"channel_id":request.form["channel"]})
        return redirect("/dashboard")

    return page("Bulk Delete", """
<form method="post" class="bg-white p-6 rounded shadow">
<input name="channel" class="border p-2 w-full mb-2">
<button class="bg-red-600 text-white p-2 w-full">Delete</button>
</form>
""")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",8080)))ard")

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
