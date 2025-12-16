from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "ADMIN PANEL ALIVE"

@app.route("/buttons")
def buttons():
    return "BUTTONS PAGE OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
