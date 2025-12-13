from flask import Flask, request, redirect, session, url_for
import os
import db   # IMPORTANT: module import (not variable)

app = Flask(__name__)
app.secret_key = "super-secret-key-123"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Initialize MongoDB safely
db.init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if ADMIN_PASSWORD is None:
            return "ADMIN_PASSWORD not set in Railway variables"

        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return "<h3>Wrong Password</h3><a href='/'>Back</a>"

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input type="password" name="password"
               placeholder="Admin Password" required>
        <br><br>
        <button type="submit">Login</button>
    </form>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    # If DB not connected (safe fallback)
    if db.captions is None:
        return "<h3>Dashboard OK</h3><p>⚠ MongoDB not connected</p>"

    # Save / Update channel caption
    if request.method == "POST":
        db.captions.update_one(
            {"type": "channel_caption"},
            {"$set": {"text": request.form.get("caption")}},
            upsert=True
        )
        return redirect(url_for("dashboard"))

    # Load existing caption
    data = db.captions.find_one({"type": "channel_caption"})
    current = data["text"] if data else ""

    return f"""
    <h2>Channel Auto Caption Panel</h2>
    <p>This caption will be automatically added/edited on channel posts.</p>

    <form method="post">
        <textarea name="caption" rows="6" cols="60"
          placeholder="Enter channel caption here">{current}</textarea>
        <br><br>
        <button type="submit">Save Channel Caption</button>
    </form>

    <br>
    <a href="/logout">Logout</a>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
