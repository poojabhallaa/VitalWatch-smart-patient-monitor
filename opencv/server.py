import subprocess
import os
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///hospital_monitor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)

# Simple CORS Configuration - Let flask-cors handle everything
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='nurse')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MonitoringSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    notes = db.Column(db.Text)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('monitoring_session.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # fall, stress, panic, etc.
    severity = db.Column(db.String(20), nullable=False)    # low, medium, high, critical
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    acknowledged = db.Column(db.Boolean, default=False)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Your existing monitoring route (kept exactly the same)
@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
        
    # Use os.path.join for cross-platform path handling
    venv_python = os.path.join("venv", "bin", "python")  # Mac/Linux path
    
    # Check if virtual environment exists, fallback to system python
    if not os.path.exists(venv_python):
        venv_python = "python3"  # or just "python" depending on your setup
    
    # Correct path to read.py in opencv folder
    read_py_path = os.path.join("opencv", "read.py")
    
    try:
        subprocess.Popen([venv_python, read_py_path])
        return jsonify({"status": "Monitoring started"})
    except FileNotFoundError as e:
        return jsonify({"status": f"Error: File not found - {str(e)}", "error": True}), 500
    except Exception as e:
        return jsonify({"status": f"Error: {str(e)}", "error": True}), 500

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not all(k in data for k in ('username', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data.get('role', 'nurse')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user = User.query.filter_by(username=data.get('username')).first()
        
        if user and check_password_hash(user.password_hash, data.get('password')):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role
                }
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
        
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# Patient Management Routes
@app.route('/api/patients', methods=['GET'])
def get_patients():
        
    try:
        patients = Patient.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender,
            'room_number': p.room_number,
            'condition': p.condition,
            'emergency_contact': p.emergency_contact,
            'created_at': p.created_at.isoformat()
        } for p in patients])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients', methods=['POST'])
def add_patient():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'age', 'gender', 'room_number']
        if not all(k in data for k in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        patient = Patient(
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            room_number=data['room_number'],
            condition=data.get('condition', ''),
            emergency_contact=data.get('emergency_contact', '')
        )
        
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'message': 'Patient added successfully',
            'patient_id': patient.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
        
    try:
        patient = Patient.query.get_or_404(patient_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'name' in data:
            patient.name = data['name']
        if 'age' in data:
            patient.age = data['age']
        if 'gender' in data:
            patient.gender = data['gender']
        if 'room_number' in data:
            patient.room_number = data['room_number']
        if 'condition' in data:
            patient.condition = data['condition']
        if 'emergency_contact' in data:
            patient.emergency_contact = data['emergency_contact']
        
        db.session.commit()
        return jsonify({'message': 'Patient updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
        
    try:
        patient = Patient.query.get_or_404(patient_id)
        db.session.delete(patient)
        db.session.commit()
        return jsonify({'message': 'Patient deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Enhanced Monitoring Routes
@app.route('/api/monitoring/start', methods=['POST'])
def api_start_monitoring():
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        patient_id = data.get('patient_id')
        
        if not patient_id:
            return jsonify({'error': 'Patient ID is required'}), 400
        
        # Verify patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Create monitoring session
        session_record = MonitoringSession(
            patient_id=patient_id,
            user_id=session.get('user_id'),
            status='active'
        )
        
        db.session.add(session_record)
        db.session.commit()
        
        # Start the monitoring process (your existing logic)
        venv_python = os.path.join("venv", "bin", "python")
        if not os.path.exists(venv_python):
            venv_python = "python3"
        
        read_py_path = os.path.join("opencv", "read.py")
        
        try:
            subprocess.Popen([venv_python, read_py_path])
            return jsonify({
                "status": "Monitoring started",
                "session_id": session_record.id,
                "patient_name": patient.name
            })
        except Exception as e:
            # If monitoring fails, clean up the session
            db.session.delete(session_record)
            db.session.commit()
            return jsonify({"status": f"Error: {str(e)}", "error": True}), 500
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/stop/<int:session_id>', methods=['POST'])
def stop_monitoring(session_id):
        
    try:
        session_record = MonitoringSession.query.get_or_404(session_id)
        session_record.status = 'stopped'
        session_record.end_time = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Monitoring stopped successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/sessions', methods=['GET'])
def get_monitoring_sessions():
        
    try:
        sessions = db.session.query(MonitoringSession, Patient).join(Patient).all()
        return jsonify([{
            'id': s.MonitoringSession.id,
            'patient_id': s.MonitoringSession.patient_id,
            'patient_name': s.Patient.name,
            'start_time': s.MonitoringSession.start_time.isoformat(),
            'end_time': s.MonitoringSession.end_time.isoformat() if s.MonitoringSession.end_time else None,
            'status': s.MonitoringSession.status,
            'duration': str(datetime.utcnow() - s.MonitoringSession.start_time) if s.MonitoringSession.status == 'active' else None
        } for s in sessions])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard and Statistics
@app.route('/api/dashboard', methods=['GET'])
def dashboard_stats():
        
    try:
        total_patients = Patient.query.count()
        active_sessions = MonitoringSession.query.filter_by(status='active').count()
        total_users = User.query.count()
        total_alerts = Alert.query.filter_by(acknowledged=False).count()
        
        return jsonify({
            'total_patients': total_patients,
            'active_sessions': active_sessions,
            'total_users': total_users,
            'unacknowledged_alerts': total_alerts,
            'system_status': 'operational'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Alert Management
@app.route('/api/alerts', methods=['POST', 'OPTIONS'])
def create_alert():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        alert = Alert(
            session_id=data['session_id'],
            alert_type=data['alert_type'],
            severity=data['severity'],
            message=data['message']
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert created successfully',
            'alert_id': alert.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET', 'OPTIONS'])
def get_alerts():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(50).all()
        return jsonify([{
            'id': a.id,
            'session_id': a.session_id,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'message': a.message,
            'timestamp': a.timestamp.isoformat(),
            'acknowledged': a.acknowledged
        } for a in alerts])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health Check
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
        
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    # Run the server
    print("Starting Flask server on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
