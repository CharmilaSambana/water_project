from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        inflow = request.form.get("inflow")
        outflow = request.form.get("outflow")

        print("Inflow:", inflow)
        print("Outflow:", outflow)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
