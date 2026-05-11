from flask import Flask, render_template
import os

# Create Flask app
app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Optional route (for testing)
@app.route("/test")
def test():
    return "App is working correctly!"

# Main run block (IMPORTANT for Render)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    app.run(host="0.0.0.0", port=port, debug=False)
