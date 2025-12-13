from flask import Flask, request, redirect, session, url_for
import os
import db   # 🔥 IMPORT MODULE, NOT VARIABLE

app = Flask(__name__)
app.secret_key = "super-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# init DB
db.init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return "Wrong password"

    return """
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" required>
      <button>Login</button>
    </form>
    """
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if db.captions is None:
        return "<h3>Dashboard OK</h3><p>⚠ MongoDB not connected</p>"

    if request.method == "POST":
        db.captions.update_one(
            {"type": "channel_caption"},
            {"$set": {"text": request.form.get("caption")}},
            upsert=True
        )
        return redirect(url_for("dashboard"))

    data = db.captions.find_one({"type": "channel_caption"})
    current = data["text"] if data else ""

    return f"""
    <h2>Channel Auto Caption Panel</h2>
    <form method="post">
      <textarea name="caption" rows="5" cols="50"
        placeholder="Enter channel caption">{current}</textarea><br><br>
      <button>Save Channel Caption</button>
    </form>
    <br>
    <a href="/logout">Logout</a>
    """
