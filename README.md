# 🏥 Hospital Patient Monitoring System

A comprehensive hospital patient monitoring system that combines computer vision-based body safety monitoring with a modern React.js frontend and Flask backend.

## ✨ Features

### 🔍 **Computer Vision Monitoring**
- **Fall Detection**: Real-time detection of potential falls using pose estimation
- **Stress Analysis**: Facial expression analysis for stress detection
- **Panic/Distress Detection**: Monitoring for signs of panic or breathing difficulties
- **Real-time Alerts**: Audio and visual alerts for critical situations

### 🖥️ **Web Dashboard**
- **User Authentication**: Secure login/signup system with role-based access
- **Patient Management**: Add, edit, and manage patient records
- **Real-time Monitoring**: Start/stop monitoring sessions for individual patients
- **Dashboard Analytics**: Live statistics and monitoring status
- **Responsive Design**: Modern UI that works on desktop and mobile

### 🔧 **Technical Stack**
- **Frontend**: React.js with Material-UI
- **Backend**: Flask with SQLAlchemy
- **Computer Vision**: OpenCV + MediaPipe
- **Database**: SQLite (can be easily migrated to PostgreSQL/MySQL)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd patient-monitor
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python3.11 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   
   # Install Python dependencies
   pip install -r requirements.txt
   pip install -r backend/requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Start the application**
   ```bash
   ./start.sh
   ```

   Or start services individually:
   ```bash
   # Terminal 1 - Backend
   cd backend
   source ../venv/bin/activate
   python app.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm start
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001

## 📋 Usage

### 1. **User Registration/Login**
- Navigate to http://localhost:3000
- Register a new account or login with existing credentials
- Choose your role: Nurse, Doctor, or Administrator

### 2. **Patient Management**
- Go to "Patients" section
- Add new patients with their details
- Search and manage existing patient records

### 3. **Start Monitoring**
- Go to "Patient Monitoring" section
- Select a patient from the dropdown
- Click "Start Monitoring" to begin real-time surveillance
- The Python script will activate your camera for monitoring

### 4. **Monitor Dashboard**
- View real-time statistics on the dashboard
- Track active monitoring sessions
- Monitor alerts and system status

## 🏗️ Project Structure

```
patient-monitor/
├── backend/
│   ├── app.py                 # Flask API server
│   └── requirements.txt       # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── contexts/          # React contexts
│   │   └── App.js            # Main app component
│   └── package.json          # Frontend dependencies
├── read.py                   # Computer vision monitoring script
├── requirements.txt          # Python dependencies
├── start.sh                  # Startup script
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:
```env
FLASK_SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///hospital_monitor.db
```

### Camera Configuration
The monitoring script uses your default camera. To use a different camera:
1. Edit `read.py`
2. Change `camera_index=0` to your desired camera index
3. Or specify a video file path for testing

## 🛡️ Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Flask session-based authentication
- **CORS Protection**: Configured for secure cross-origin requests
- **Role-based Access**: Different permissions for different user roles

## 📊 API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Patients
- `GET /api/patients` - Get all patients
- `POST /api/patients` - Add new patient
- `PUT /api/patients/<id>` - Update patient
- `DELETE /api/patients/<id>` - Delete patient

### Monitoring
- `POST /api/start-monitoring` - Start monitoring session
- `POST /api/stop-monitoring/<session_id>` - Stop monitoring session
- `GET /api/monitoring-status` - Get active sessions
- `GET /api/dashboard-stats` - Get dashboard statistics

## 🐛 Troubleshooting

### Common Issues

1. **MediaPipe Installation Error**
   - Ensure you're using Python 3.11 (not 3.13)
   - Reinstall MediaPipe: `pip install mediapipe --force-reinstall`

2. **Camera Access Issues**
   - Grant camera permissions to your terminal/IDE
   - Check if camera is being used by another application

3. **Port Already in Use**
   - Kill existing processes: `lsof -ti:3000 | xargs kill -9`
   - Or change ports in the configuration

4. **Database Issues**
   - Delete `backend/hospital_monitor.db` and restart
   - The database will be recreated automatically

### SSL Certificate Issues (macOS)
If you encounter SSL certificate errors:
```bash
/Applications/Python\ 3.11/Install\ Certificates.command
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the API documentation

---

**Note**: This system is designed for educational and development purposes. For production use in healthcare environments, additional security measures, HIPAA compliance, and medical device regulations should be considered. 