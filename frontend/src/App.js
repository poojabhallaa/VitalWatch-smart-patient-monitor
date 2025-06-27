import React, { useState, useEffect } from 'react';
import { Users, Activity, AlertTriangle, CheckCircle, Plus, Monitor, Bell, User, LogOut } from 'lucide-react';

const VitalWatchApp = () => {
  const [currentPage, setCurrentPage] = useState('monitor');
  const [patients, setPatients] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({
    total_patients: 0,
    active_sessions: 0,
    total_users: 0,
    unacknowledged_alerts: 0,
    system_status: 'operational'
  });
  const [alerts, setAlerts] = useState([]);
  const [monitoringSessions, setMonitoringSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddPatient, setShowAddPatient] = useState(false);
  const [user, setUser] = useState({ username: 'Doctor', role: 'doctor' });
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loggingOut, setLoggingOut] = useState(false);

  // API base URL - adjust this to match your Flask server
  const API_BASE = 'http://localhost:8000/api';

  // API helper function
  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        credentials: 'include', // Include cookies for session management
        ...options
      });
      
      if (!response.ok) {
        // If 401 (unauthorized), redirect to login
        if (response.status === 401) {
          setIsLoggedIn(false);
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  };

  // Handle user login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify(loginForm)
      });

      if (response && response.user) {
        setUser(response.user);
        setIsLoggedIn(true);
        setLoginForm({ username: '', password: '' });
        // Fetch initial data after successful login
        fetchData();
      }
    } catch (error) {
      console.error('Login failed:', error);
      alert('Login failed. Please check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle user logout
  const handleLogout = async () => {
    setLoggingOut(true);
    
    try {
      await apiCall('/logout', {
        method: 'POST'
      });
      
      // Clear local state
      setUser({ username: '', role: '' });
      setIsLoggedIn(false);
      setPatients([]);
      setAlerts([]);
      setMonitoringSessions([]);
      setDashboardStats({
        total_patients: 0,
        active_sessions: 0,
        total_users: 0,
        unacknowledged_alerts: 0,
        system_status: 'operational'
      });
      
      // Redirect to login
      setCurrentPage('monitor');
      
    } catch (error) {
      console.error('Logout failed:', error);
      // Even if logout fails on server, clear local state
      setUser({ username: '', role: '' });
      setIsLoggedIn(false);
    } finally {
      setLoggingOut(false);
    }
  };

  // Check if user is logged in on component mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        // Try to fetch dashboard stats to check if user is authenticated
        const response = await apiCall('/dashboard');
        if (response) {
          setIsLoggedIn(true);
          fetchData();
        } else {
          setIsLoggedIn(false);
        }
      } catch (error) {
        setIsLoggedIn(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Fetch all data
  const fetchData = async () => {
    if (!isLoggedIn) return;
    
    setLoading(true);
    try {
      const [patientsData, statsData, alertsData, sessionsData] = await Promise.all([
        apiCall('/patients'),
        apiCall('/dashboard'),
        apiCall('/alerts'),
        apiCall('/monitoring/sessions')
      ]);

      if (patientsData) setPatients(patientsData);
      if (statsData) setDashboardStats(statsData);
      if (alertsData) setAlerts(alertsData);
      if (sessionsData) setMonitoringSessions(sessionsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      // If any API call fails with auth error, logout
      if (error.message.includes('401')) {
        setIsLoggedIn(false);
      }
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh data every 30 seconds (only when logged in)
  useEffect(() => {
    if (!isLoggedIn) return;
    
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [isLoggedIn]);

  // Add new patient
  const addPatient = async (patientData) => {
    try {
      await apiCall('/patients', {
        method: 'POST',
        body: JSON.stringify(patientData)
      });
      setShowAddPatient(false);
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to add patient:', error);
      alert('Failed to add patient. Please try again.');
    }
  };

  // Start monitoring for a patient
  const startMonitoring = async (patientId) => {
    try {
      const response = await apiCall('/monitoring/start', {
        method: 'POST',
        body: JSON.stringify({ patient_id: patientId })
      });
      
      if (response) {
        alert(`Monitoring started: ${response.status}`);
        fetchData(); // Refresh data
      }
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      alert('Failed to start monitoring. Please try again.');
    }
  };

  // Stop monitoring session
  const stopMonitoring = async (sessionId) => {
    try {
      await apiCall(`/monitoring/stop/${sessionId}`, {
        method: 'POST'
      });
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      alert('Failed to stop monitoring. Please try again.');
    }
  };

  // Get patient status based on alerts and conditions
  const getPatientStatus = (patient) => {
    const recentAlerts = alerts.filter(alert => 
      monitoringSessions.some(session => 
        session.patient_id === patient.id && session.id === alert.session_id
      )
    );
    
    if (recentAlerts.some(alert => alert.severity === 'critical')) return 'Critical';
    if (recentAlerts.some(alert => alert.severity === 'high')) return 'High';
    if (recentAlerts.length > 0) return 'Moderate';
    return 'Stable';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Critical': return 'bg-red-100 text-red-800';
      case 'High': return 'bg-orange-100 text-orange-800';
      case 'Moderate': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-green-100 text-green-800';
    }
  };

  // Login Component
  const LoginPage = () => (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <div className="flex items-center space-x-2">
              <div className="h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="h-8 w-8 text-white" />
              </div>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            VitalWatch
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Smart Patient Monitoring System
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Username"
                value={loginForm.username}
                onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const AddPatientForm = () => {
    const [formData, setFormData] = useState({
      name: '',
      age: '',
      gender: '',
      room_number: '',
      condition: '',
      emergency_contact: ''
    });

    const handleSubmit = () => {
      if (formData.name && formData.age && formData.gender && formData.room_number) {
        addPatient({
          ...formData,
          age: parseInt(formData.age)
        });
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 className="text-lg font-semibold mb-4">Add New Patient</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age *</label>
                <input
                  type="number"
                  value={formData.age}
                  onChange={(e) => setFormData({...formData, age: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({...formData, gender: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Room Number *</label>
              <input
                type="text"
                value={formData.room_number}
                onChange={(e) => setFormData({...formData, room_number: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
              <input
                type="text"
                value={formData.condition}
                onChange={(e) => setFormData({...formData, condition: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact</label>
              <input
                type="text"
                value={formData.emergency_contact}
                onChange={(e) => setFormData({...formData, emergency_contact: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2 pt-4">
              <button
                type="button"
                onClick={handleSubmit}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Add Patient
              </button>
              <button
                type="button"
                onClick={() => setShowAddPatient(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const MonitoringPage = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Patient Monitoring</h1>
        <p className="text-gray-600 mt-1">Real-time AI-powered patient monitoring with motion and stress detection</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-blue-600">Patients Monitored</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.active_sessions}</p>
            </div>
            <Users className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-orange-600">Active Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardStats.unacknowledged_alerts}</p>
            </div>
            <AlertTriangle className="h-8 w-8 text-orange-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-600">System Status</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">{dashboardStats.system_status}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </div>
      </div>

      {/* Patient List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 flex items-center gap-2">
              <Users className="h-5 w-5" />
              Patient List
            </h2>
            <button 
              onClick={() => setShowAddPatient(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Patient
            </button>
          </div>
        </div>
        
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-6 text-center">Loading patients...</div>
          ) : patients.length === 0 ? (
            <div className="p-6 text-center text-gray-500">No patients found</div>
          ) : (
            patients.map((patient) => {
              const status = getPatientStatus(patient);
              const isMonitoring = monitoringSessions.some(session => 
                session.patient_id === patient.id && session.status === 'active'
              );
              
              return (
                <div key={patient.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <User className="h-5 w-5 text-blue-600" />
                        </div>
                      </div>
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">{patient.name}</h3>
                        <p className="text-sm text-gray-500">
                          Room {patient.room_number} • Age {patient.age} • {patient.condition || 'General care'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                        {status}
                      </span>
                      {isMonitoring ? (
                        <button
                          onClick={() => {
                            const session = monitoringSessions.find(s => 
                              s.patient_id === patient.id && s.status === 'active'
                            );
                            if (session) stopMonitoring(session.id);
                          }}
                          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 flex items-center gap-2"
                        >
                          <Monitor className="h-4 w-4" />
                          Stop Monitoring
                        </button>
                      ) : (
                        <button
                          onClick={() => startMonitoring(patient.id)}
                          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2"
                        >
                          <Monitor className="h-4 w-4" />
                          Start Monitoring
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );

  const PatientsPage = () => (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Patient Management</h1>
        <p className="text-gray-600 mt-1">Comprehensive patient records and monitoring</p>
      </div>

      {/* Add Patient Button */}
      <div className="flex justify-end">
        <button 
          onClick={() => setShowAddPatient(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add New Patient
        </button>
      </div>

      {/* Patients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {patients.map((patient) => {
          const status = getPatientStatus(patient);
          const activeSession = monitoringSessions.find(session => 
            session.patient_id === patient.id && session.status === 'active'
          );
          
          return (
            <div key={patient.id} className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <User className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{patient.name}</h3>
                    <p className="text-sm text-gray-500">Room {patient.room_number}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
                  {status}
                </span>
              </div>
              
              <div className="space-y-2 mb-4">
                <p className="text-sm text-gray-600">Age: {patient.age}</p>
                <p className="text-sm text-gray-600">Gender: {patient.gender}</p>
                <p className="text-sm text-gray-600">Condition: {patient.condition || 'General care'}</p>
                {patient.emergency_contact && (
                  <p className="text-sm text-gray-600">Emergency: {patient.emergency_contact}</p>
                )}
              </div>

              {activeSession ? (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-green-600 font-medium">Monitoring Active</span>
                  <button
                    onClick={() => stopMonitoring(activeSession.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Stop
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => startMonitoring(patient.id)}
                  className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 flex items-center justify-center gap-2"
                >
                  <Monitor className="h-4 w-4" />
                  Start Monitoring
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  // If not logged in, show login page
  if (!isLoggedIn) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Activity className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">VitalWatch</h1>
                  <p className="text-xs text-gray-500">Smart Monitoring System</p>
                </div>
              </div>
            </div>

            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentPage('monitor')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium ${
                  currentPage === 'monitor'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Monitor className="h-4 w-4" />
                Monitor
              </button>
              <button
                onClick={() => setCurrentPage('patients')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium ${
                  currentPage === 'patients'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Users className="h-4 w-4" />
                Patients
              </button>
            </nav>

            <div className="flex items-center space-x-4">
              <div className="relative">
                <Bell className="h-5 w-5 text-gray-400" />
                {dashboardStats.unacknowledged_alerts > 0 && (
                  <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {dashboardStats.unacknowledged_alerts}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-gray-400" />
                <div className="text-sm">
                  <p className="font-medium text-gray-900">{user.username}</p>
                  <p className="text-gray-500 capitalize">{user.role}</p>
                </div>
              </div>
              <button 
                onClick={handleLogout}
                disabled={loggingOut}
                className="text-gray-400 hover:text-gray-600 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-gray-100 disabled:opacity-50"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
                {loggingOut && <span className="text-xs">...</span>}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === 'monitor' ? <MonitoringPage /> : <PatientsPage />}
      </main>

      {/* Add Patient Modal */}
      {showAddPatient && <AddPatientForm />}
    </div>
  );
};

export default VitalWatchApp;
