import subprocess
import sys
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS for deployed frontend (adjust this to your real Vercel frontend URL)
CORS(app, resources={r"/*": {"origins": "https://vitalwatchmonitor.vercel.app/"}})

@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    # Use system python (works on Render)
    subprocess.Popen([sys.executable, "read.py"])
    return jsonify({"status": "Monitoring started"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
