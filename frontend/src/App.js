import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Bell, 
  Camera, 
  User, 
  CheckCircle, 
  AlertTriangle,
  Stethoscope,
  Eye,
  EyeOff
} from 'lucide-react';

const VitalWatchApp = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentView, setCurrentView] = useState('monitor');
  const [userRole, setUserRole] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [monitoringData, setMonitoringData] = useState({
    patientsMonitored: 12,
    activeAlerts: 3,
    systemStatus: 'operational'
  });

  const navItems = [
    { id: 'monitor', label: 'Monitor', icon: Camera },
    { id: 'patients', label: 'Patients', icon: Users },
  ];

  // Login Component
  const LoginPage = () => {
    const [selectedRole, setSelectedRole] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = () => {
      if (selectedRole && username && password) {
        setUserRole(selectedRole);
        setIsLoggedIn(true);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="bg-blue-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <img 
                src="medical_white.png" 
                alt="VitalWatch Logo" 
                className="w-10 h-10 object-contain"
              />
            </div>
            <h1 className="text-3xl font-bold text-blue-900 mb-2">VitalWatch</h1>
            <p className="text-blue-600">Smart Monitoring System</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-blue-700 font-medium mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full px-4 py-3 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-blue-700 font-medium mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-4 py-3 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-blue-700 font-medium mb-3">Select Your Role</label>
              <div className="space-y-3">
                <div className="flex items-center">
                  <input
                    type="radio"
                    id="doctor"
                    name="role"
                    value="doctor"
                    checked={selectedRole === 'doctor'}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="w-4 h-4 text-blue-600 border-blue-300 focus:ring-blue-500"
                  />
                  <label htmlFor="doctor" className="ml-3 text-blue-700 font-medium cursor-pointer">
                    Doctor
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="radio"
                    id="nurse"
                    name="role"
                    value="nurse"
                    checked={selectedRole === 'nurse'}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="w-4 h-4 text-blue-600 border-blue-300 focus:ring-blue-500"
                  />
                  <label htmlFor="nurse" className="ml-3 text-blue-700 font-medium cursor-pointer">
                    Nurse
                  </label>
                </div>
              </div>
            </div>

            <button
              onClick={handleLogin}
              disabled={!selectedRole || !username || !password}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            >
              Login to VitalWatch
            </button>
          </div>

          <div className="mt-6 text-center text-blue-600 text-sm">
            <p>Secure healthcare monitoring platform</p>
          </div>
        </div>
      </div>
    );
  };

  // Navigation Component
  const Navbar = () => {
    return (
      <nav className="bg-white border-b-2 border-blue-100 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-blue-600 w-10 h-10 rounded-lg flex items-center justify-center">
              <img 
                src="medical_white.png" 
                alt="VitalWatch Logo" 
                className="w-6 h-6 object-contain"
              />
            </div>
            <div>
              <h1 className="text-xl font-bold text-blue-900">VitalWatch</h1>
              <p className="text-blue-600 text-sm">Smart Monitoring System</p>
            </div>
          </div>

          <div className="flex items-center space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    currentView === item.id
                      ? 'bg-blue-600 text-white'
                      : 'text-blue-700 hover:bg-blue-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative">
              <Bell className="w-6 h-6 text-blue-600" />
              {alerts.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {alerts.length}
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Stethoscope className="w-6 h-6 text-blue-600" />
              <div>
                <p className="text-blue-900 font-medium capitalize">{userRole}</p>
                <p className="text-blue-600 text-sm">Logged In</p>
              </div>
            </div>
            <button
              onClick={() => setIsLoggedIn(false)}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>
    );
  };

  // Camera Monitor Component
  const CameraMonitor = () => {
    const toggleMonitoring = () => {
      setIsMonitoring(!isMonitoring);
    };

    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-blue-900 mb-2">Patient Monitoring</h2>
          <p className="text-blue-600">Real-time AI-powered patient monitoring with motion and stress detection</p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 font-medium">Patients Monitored</p>
                <p className="text-3xl font-bold text-blue-900">{monitoringData.patientsMonitored}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 font-medium">Active Alerts</p>
                <p className="text-3xl font-bold text-blue-900">{monitoringData.activeAlerts}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-orange-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 font-medium">System Status</p>
                <p className="text-lg font-semibold text-green-600 capitalize">{monitoringData.systemStatus}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-green-500" />
            </div>
          </div>
        </div>

        {/* Camera Monitor */}
        

        {/* Patient List */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-blue-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Patient List
          </h3>
          <div className="space-y-3">
            {[
              { id: 1, name: 'John Smith', room: '301', age: 65, condition: 'Post-surgery recovery', status: 'stable' },
              { id: 2, name: 'Sarah Johnson', room: '302', age: 78, condition: 'Heart monitoring', status: 'critical' },
              { id: 3, name: 'Michael Brown', room: '215', age: 45, condition: 'Diabetes management', status: 'stable' },
              { id: 4, name: 'Emily Davis', room: '318', age: 32, condition: 'Maternity care', status: 'good' },
              { id: 5, name: 'Robert Wilson', room: '205', age: 71, condition: 'Respiratory therapy', status: 'monitoring' },
              { id: 6, name: 'Lisa Anderson', room: '412', age: 56, condition: 'Cardiac rehabilitation', status: 'stable' }
            ].map((patient) => (
              <div
                key={patient.id}
                className="p-4 rounded-lg border border-blue-100 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-blue-900">{patient.name}</h4>
                      <div className="flex items-center space-x-4 text-sm text-blue-600">
                        <span>Room {patient.room}</span>
                        <span>Age {patient.age}</span>
                        <span>{patient.condition}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <div 
                        className={`w-3 h-3 rounded-full ${
                          patient.status === 'critical' ? 'bg-red-500' :
                          patient.status === 'monitoring' ? 'bg-orange-500' :
                          patient.status === 'good' ? 'bg-green-500' : 'bg-blue-500'
                        }`}
                      ></div>
                      <span className={`text-sm font-medium capitalize ${
                        patient.status === 'critical' ? 'text-red-600' :
                        patient.status === 'monitoring' ? 'text-orange-600' :
                        patient.status === 'good' ? 'text-green-600' : 'text-blue-600'
                      }`}>
                        {patient.status}
                      </span>
                    </div>
                    <button
                      onClick={() => {
                        fetch("http://127.0.0.1:8000/start-monitoring", { method: "POST" })
                          .then(res => res.json())
                          .then(data => {
                            console.log(data);
                            alert("Monitoring Started");
                          })
                          .catch(err => {
                            console.error("Error:", err);
                          });
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
                    >
                      <Camera className="w-4 h-4" />
                      <span>Start Monitoring</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // Main App Render
  if (!isLoggedIn) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-blue-50">
      <Navbar />
      <main>
        {currentView === 'monitor' && <CameraMonitor />}
        {currentView === 'patients' && (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-blue-900">Patient Management</h2>
            <p className="text-blue-600">Comprehensive patient records and monitoring</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default VitalWatchApp;
