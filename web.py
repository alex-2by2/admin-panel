from flask import Flask, request, redirect, session, url_for
import os

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# Try DB init safely (never crash app)
try:
    import db
    db.init_db()
    DB_OK = True
except Exception as e:
    print("DB init failed:", e)
    DB_OK = False

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

    if not DB_OK or not hasattr(__import__("db"), "captions"):
        return "<h3>Dashboard OK</h3><p>⚠ MongoDB not connected</p>"

    import db

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
      <textarea name="caption" rows="5" cols="50">{current}</textarea><br><br>
      <button>Save</button>
    </form>
    <br><a href="/logout">Logout</a>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
