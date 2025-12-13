from flask import Flask, request, redirect, session, url_for
import os

app = Flask(__name__)

# Session secret key
app.secret_key = "super-secret-key"

# Admin password (Railway variable se)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ---------------- LOGIN PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return "<h3>❌ Wrong Password</h3><a href='/'>Try again</a>"

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input type="password" name="password" placeholder="Admin Password" required>
        <br><br>
        <button type="submit">Login</button>
    </form>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    return """
    <h2>Dashboard ✅</h2>
    <p>You are logged in as Admin</p>
    <a href="/logout">Logout</a>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- RUN (Railway SAFE) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
