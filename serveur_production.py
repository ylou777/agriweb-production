#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur ultra-minimal SANS DEBUG
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    print("🔧 [PRODUCTION] Serveur sans debug...")
    app.run(host='127.0.0.1', port=5004, debug=False)
