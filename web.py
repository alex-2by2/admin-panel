from flask import Flask, request, redirect, session
import os

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


# ---------- MOBILE UI ----------
def page(title, body):
    return f"""
    <html>
    <head>
      <title>{title}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{ font-family: Arial; padding: 15px; max-width: 600px; margin: auto; }}
        textarea, input {{ width: 100%; padding: 10px; margin: 6px 0; font-size: 16px; }}
        button {{ width: 100%; padding: 12px; font-size: 18px; background: #2b7cff;
                  color: white; border: none; border-radius: 6px; }}
        h2 {{ text-align: center; }}
        a {{ display: block; text-align: center; margin-top: 15px; }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
        return page("Error", "<h3>Wrong password</h3><a href='/'>Back</a>")

    return page("Login", """
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" placeholder="Password" required>
      <button>Login</button>
    </form>
    """)


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect("/")

    if not DB_OK:
        return page("DB Error", "<h3>⚠ MongoDB not connected</h3>")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"

        db.captions.update_one(
            {
                "type": request.form["type"],
                "channel_id": channel_id
            },
            {"$set": {"text": request.form["caption"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Dashboard", """
    <h2>Caption Control</h2>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">

      <h4>📷 Photo Caption</h4>
      <textarea name="caption"></textarea>
      <input type="hidden" name="type" value="photo_caption">
      <button>Save Photo Caption</button>
    </form><br>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">

      <h4>🎥 Video Caption</h4>
      <textarea name="caption"></textarea>
      <input type="hidden" name="type" value="video_caption">
      <button>Save Video Caption</button>
    </form><br>

    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">

      <h4>📝 Text Caption</h4>
      <textarea name="caption"></textarea>
      <input type="hidden" name="type" value="text_caption">
      <button>Save Text Caption</button>
    </form>

    <a href="/buttons">Inline Buttons</a>
    <a href="/logout">Logout</a>
    """)


# ---------- INLINE BUTTONS ----------
@app.route("/buttons", methods=["GET", "POST"])
def buttons():
    if not session.get("admin"):
        return redirect("/")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"
        buttons = []

        for t, u in zip(request.form.getlist("text"), request.form.getlist("url")):
            if t and u:
                buttons.append({"text": t, "url": u})

        db.captions.update_one(
            {"type": "inline_buttons", "channel_id": channel_id},
            {"$set": {"buttons": buttons}},
            upsert=True
        )
        return redirect("/buttons")

    return page("Buttons", """
    <h2>Inline Buttons</h2>
    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">
      <input name="text" placeholder="Button Text">
      <input name="url" placeholder="Button URL">
      <button>Save Button</button>
    </form>
    <a href="/dashboard">Back</a>
    """)


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
