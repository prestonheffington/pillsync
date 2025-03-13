# app.py
from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/flash_led", methods=["POST"])
def flash_led():
    try:
        subprocess.run(["python3", "functions/LEDtest.py"])  # Runs the LED script
        return jsonify({"message": "LED flashed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

