from flask import Flask, request, redirect, session, url_for
import os
from db import captions

app = Flask(__name__)
app.secret_key = "secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# ---------- LOGIN ----------
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
      <input type="password" name="password" placeholder="Admin Password" required>
      <button>Login</button>
    </form>
    """

# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        captions.delete_many({})
        captions.insert_one({
            "text": request.form.get("caption")
        })
        return redirect(url_for("dashboard"))

    data = captions.find_one()
    current = data["text"] if data else ""

    return f"""
    <h2>Caption Control Panel</h2>
    <form method="post">
      <textarea name="caption" rows="5" cols="40">{current}</textarea><br><br>
      <button>Save Caption</button>
    </form>
    <br>
    <a href="/logout">Logout</a>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
