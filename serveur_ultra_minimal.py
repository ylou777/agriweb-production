#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur ultra-minimal pour test isolé
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World - Serveur ultra-minimal"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    print("🔧 [ULTRA-MINIMAL] Démarrage serveur de base...")
    app.run(host='127.0.0.1', port=5003, debug=True)
