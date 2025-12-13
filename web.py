from flask import Flask, request, redirect, session, url_for
import os

app = Flask(__name__)

# 🔐 REQUIRED for session (VERY IMPORTANT)
app.secret_key = "THIS_IS_A_SECRET_KEY_123"

# 🔑 Admin password from environment
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

@app.route("/", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            password = request.form.get("password")

            if ADMIN_PASSWORD is None:
                return "❌ ADMIN_PASSWORD not set in Railway Variables"

            if password == ADMIN_PASSWORD:
                session["admin"] = True
                return redirect(url_for("dashboard"))
            else:
                return "<h3>Wrong Password</h3><a href='/'>Back</a>"

        return """
        <h2>Admin Login</h2>
        <form method="post">
            <input type="password" name="password" placeholder="Admin Password" required>
            <br><br>
            <button type="submit">Login</button>
        </form>
        """

    except Exception as e:
        return f"<pre>LOGIN ERROR: {e}</pre>", 500


@app.route("/dashboard")
def dashboard():
    try:
        if not session.get("admin"):
            return redirect(url_for("login"))

        return """
        <h2>Dashboard ✅</h2>
        <p>Login successful</p>
        <a href="/logout">Logout</a>
        """

    except Exception as e:
        return f"<pre>DASHBOARD ERROR: {e}</pre>", 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
