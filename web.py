from flask import Flask, request, redirect, session, Response, abort
from bson import ObjectId
import os, json

app = Flask(__name__)
app.secret_key = "safe-secret-key"

ADMIN_PATH = os.environ.get("ADMIN_PATH", "/_admin")

# ---------- DB INIT ----------
try:
    import db
    db.init_db()
    DB_OK = True
except Exception as e:
    print("DB init failed:", e)
    DB_OK = False


# ---------- UI ----------
def page(title, body):
    return f"""
    <html><head>
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body {{ font-family: Arial; max-width: 900px; margin:auto; padding:15px; }}
      textarea,input,select {{ width:100%; padding:8px; margin:5px 0; }}
      button {{ padding:8px 14px; margin-top:5px; }}
      table {{ width:100%; border-collapse:collapse; }}
      th,td {{ border:1px solid #ccc; padding:6px; }}
      th {{ background:#eee; }}
      a {{ margin-right:10px; }}
    </style>
    </head><body>{body}</body></html>
    """


# ---------- AUTH ----------
def require_login():
    if not session.get("admin"):
        abort(403)

def require_role(*roles):
    if session.get("role") not in roles:
        abort(403)


# ---------- LOGIN ----------
@app.route(ADMIN_PATH, methods=["GET","POST"])
def login():
    import db
    if request.method == "POST":
        admin = db.admins.find_one({
            "username": request.form["username"],
            "password": request.form["password"]
        })
        if admin:
            session["admin"] = True
            session["role"] = admin["role"]
            return redirect("/dashboard")
        return page("Error","<h3>Invalid login</h3>")

    return page("Login","""
    <h2>Admin Login</h2>
    <form method="post">
      <input name="username" placeholder="Username" required>
      <input name="password" type="password" placeholder="Password" required>
      <button>Login</button>
    </form>
    """)


# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    require_login()
    require_role("superadmin","admin")

    import db

    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"
        db.captions.update_one(
            {"type": request.form["type"], "channel_id": channel_id},
            {"$set": {"text": request.form["caption"]}},
            upsert=True
        )
        return redirect("/dashboard")

    return page("Dashboard","""
    <h2>Add Caption</h2>
    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">
      <select name="type">
        <option value="photo_caption">Photo</option>
        <option value="video_caption">Video</option>
        <option value="text_caption">Text</option>
      </select>
      <textarea name="caption" placeholder="Caption text"></textarea>
      <button>Save Caption</button>
    </form>
    <hr>
    <a href="/buttons">Inline Buttons</a>
    <a href="/all">All Captions</a>
    <a href="/channels">Channels</a>
    <a href="/export">Export</a>
    <a href="/logout">Logout</a>
    """)


# ---------- INLINE BUTTONS (ROWS + REORDER) ----------
@app.route("/buttons", methods=["GET","POST"])
def buttons():
    require_login()
    require_role("superadmin","admin")

    import db
    if request.method == "POST":
        channel_id = request.form.get("channel_id") or "default"
        rows = []

        for line in request.form.get("rows","").splitlines():
            row=[]
            for pair in line.split(","):
                if "|" in pair:
                    t,u = pair.split("|",1)
                    row.append({"text":t.strip(),"url":u.strip()})
            if row:
                rows.append(row)

        db.captions.update_one(
            {"type":"inline_buttons","channel_id":channel_id},
            {"$set":{"buttons":rows}},
            upsert=True
        )
        return redirect("/buttons")

    return page("Buttons","""
    <h2>Inline Buttons</h2>
    <form method="post">
      <input name="channel_id" placeholder="Channel ID (empty = default)">
      <p>One row per line → text|url , text|url</p>
      <textarea name="rows" rows="6"
      placeholder="Google|https://google.com, YouTube|https://youtube.com"></textarea>
      <button>Save Buttons</button>
    </form>
    <a href="/dashboard">Back</a>
    """)


# ---------- ALL CAPTIONS ----------
@app.route("/all")
def all_caps():
    require_login()
    import db
    rows=""
    for d in db.captions.find():
        rows+=f"<tr><td>{d.get('channel_id')}</td><td>{d.get('type')}</td><td>{str(d.get('text',''))[:40]}</td><td><a href='/edit/{d['_id']}'>Edit</a> <a href='/delete/{d['_id']}'>Delete</a></td></tr>"
    return page("All",f"<table><tr><th>Channel</th><th>Type</th><th>Text</th><th>Action</th></tr>{rows}</table>")


# ---------- EDIT ----------
@app.route("/edit/<id>",methods=["GET","POST"])
def edit(id):
    require_login()
    import db
    doc=db.captions.find_one({"_id":ObjectId(id)})
    if request.method=="POST":
        db.captions.update_one({"_id":ObjectId(id)},{"$set":{"text":request.form["caption"]}})
        return redirect("/all")
    return page("Edit",f"<form method='post'><textarea name='caption'>{doc.get('text')}</textarea><button>Save</button></form>")


# ---------- DELETE ----------
@app.route("/delete/<id>")
def delete(id):
    require_login()
    import db
    db.captions.delete_one({"_id":ObjectId(id)})
    return redirect("/all")


# ---------- CHANNELS ----------
@app.route("/channels")
def channels():
    require_login()
    import db
    items="".join(f"<li>{c}</li>" for c in db.captions.distinct("channel_id"))
    return page("Channels",f"<ul>{items}</ul>")


# ---------- EXPORT ----------
@app.route("/export")
def export():
    require_login()
    import db
    data=list(db.captions.find({},{"_id":0}))
    return Response(json.dumps(data,indent=2),mimetype="application/json",
                    headers={"Content-Disposition":"attachment;filename=captions.json"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(ADMIN_PATH)


if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
