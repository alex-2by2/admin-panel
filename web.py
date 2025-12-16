from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>✅ ADMIN PANEL ALIVE</h1>
    <p>If you can see this, Flask is running correctly.</p>
    <a href="/buttons">Go to Buttons Test</a>
    """

@app.route("/buttons")
def buttons():
    return "<h2>✅ BUTTONS PAGE OK</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
