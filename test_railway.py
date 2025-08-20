#!/usr/bin/env python3
"""
Test simple pour Railway
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>🚀 AgriWeb sur Railway - TEST</h1>
    <p>L'application fonctionne !</p>
    <p>Port: ''' + str(os.environ.get("PORT", "5000")) + '''</p>
    <p>Environment: ''' + str(os.environ.get("FLASK_ENV", "development")) + '''</p>
    '''

@app.route('/health')
def health():
    return {"status": "OK", "port": os.environ.get("PORT", "5000")}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Démarrage test Railway sur port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
