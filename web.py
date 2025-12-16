from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = "admin"   # change later

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
        return "<h3>Wrong password</h3><a href='/'>Back</a>"

    return """
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" placeholder="Password" required>
      <button>Login</button>
    </form>
    """

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/")
    return """
    <h1>✅ DASHBOARD WORKING</h1>
    <ul>
      <li><a href="/test">Test Page</a></li>
      <li><a href="/logout">Logout</a></li>
    </ul>
    """

@app.route("/test")
def test():
    if not session.get("admin"):
        return redirect("/")
    return "<h2>Test page OK</h2>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
