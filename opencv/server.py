import subprocess
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS for React frontend
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    
    subprocess.Popen(["venv\\Scripts\\python.exe", "read.py"])


    return jsonify({"status": "Monitoring started"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
