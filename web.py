from flask import Flask, request, redirect, session, url_for
import os

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# ---------- DB INIT (SAFE) ----------
try:
    import db
    db.init_db()
    DB_OK = True
except Exception as e:
    print("DB init failed:", e)
    DB_OK = False


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
      <input type="password" name="password" required>
      <button>Login</button>
    </form>
    """


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if not DB_OK:
        return "<h3>Dashboard OK</h3><p>⚠ MongoDB not connected</p>"

    import db

    if request.method == "POST":
        db.captions.update_one(
            {"type": request.form["type"]},
            {"$set": {"text": request.form["caption"]}},
            upsert=True
        )
        return redirect(url_for("dashboard"))

    def get_caption(t):
        d = db.captions.find_one({"type": t})
        return d["text"] if d else ""

    return f"""
    <h2>Media-wise Caption Control</h2>

    <form method="post">
      <h4>📷 Photo Caption</h4>
      <textarea name="caption" rows="3" cols="60">{get_caption("photo_caption")}</textarea>
      <input type="hidden" name="type" value="photo_caption">
      <br><button>Save</button>
    </form><br>

    <form method="post">
      <h4>🎥 Video Caption</h4>
      <textarea name="caption" rows="3" cols="60">{get_caption("video_caption")}</textarea>
      <input type="hidden" name="type" value="video_caption">
      <br><button>Save</button>
    </form><br>

    <form method="post">
      <h4>📝 Text Caption</h4>
      <textarea name="caption" rows="3" cols="60">{get_caption("text_caption")}</textarea>
      <input type="hidden" name="type" value="text_caption">
      <br><button>Save</button>
    </form>

    <br>
    <a href="/buttons">Inline Buttons</a> |
    <a href="/logout">Logout</a>
    """


# ---------- INLINE BUTTON CONTROL ----------
@app.route("/buttons", methods=["GET", "POST"])
def buttons():
    if not session.get("admin"):
        return redirect(url_for("login"))

    import db

    if request.method == "POST":
        db.captions.update_one(
            {"type": "inline_button"},
            {"$set": {
                "text": request.form["btn_text"],
                "url": request.form["btn_url"]
            }},
            upsert=True
        )
        return redirect("/buttons")

    data = db.captions.find_one({"type": "inline_button"})
    text = data["text"] if data else ""
    url = data["url"] if data else ""

    return f"""
    <h2>Inline Button Control</h2>
    <form method="post">
      <input name="btn_text" placeholder="Button Text" value="{text}" required><br><br>
      <input name="btn_url" placeholder="Button URL" value="{url}" required><br><br>
      <button>Save Button</button>
    </form>
    <br><a href="/dashboard">Back</a>
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
