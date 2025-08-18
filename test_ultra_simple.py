#!/usr/bin/env python3
"""
Test ultra-simple pour identifier le problème
"""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Test ultra-simple OK"

@app.route("/test")
def test():
    return {"status": "ok", "message": "Simple test"}

if __name__ == "__main__":
    print("🚀 Test ultra-simple...")
    app.run(host="127.0.0.1", port=5002, debug=False)
