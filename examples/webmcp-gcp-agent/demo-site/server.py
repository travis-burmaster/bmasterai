"""
Demo Store Server
Serves the WebMCP demo website on localhost:8080.
In production, deploy this as a static site (GCS bucket, Firebase Hosting, etc.)
"""
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[Demo Store] Serving at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
