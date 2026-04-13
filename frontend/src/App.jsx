import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import { Toaster } from 'sonner';

import LoginPage from './pages/LoginPage';
import AnalystDashboard from './pages/AnalystDashboard';
import SupervisorDashboard from './pages/SupervisorDashboard';
import DocumentAnalysis from './pages/DocumentAnalysis';
import DocumentUpload from './pages/DocumentUpload';
import MockAnalysis from './pages/MockAnalysis';
import AnalysisResults from './pages/AnalysisResults';
import Traceability from './pages/Traceability';
import VisualizationPage from './pages/VisualizationPage';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Documents from './pages/Documents';
import UserManagement from './pages/UserManagement';
import MainLayout from './components/MainLayout';
import TestMermaid from './components/TestMermaid';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token on app load
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          setCurrentUser(decoded);
        } else {
          localStorage.removeItem('token');
        }
      } catch (error) {
        console.error('Error decoding token:', error);
        localStorage.removeItem('token');
      }
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (token) => {
    localStorage.setItem('token', token);
    const decoded = jwtDecode(token);
    setCurrentUser(decoded);
    
    // Redirect to appropriate dashboard based on user role
    let redirectPath = '/dashboard';
    if (decoded.role === 'developer' || decoded.role === 'student' || decoded.role === 'analyst') {
      redirectPath = '/analyst';
    } else if (decoded.role === 'supervisor') {
      redirectPath = '/supervisor';
    }
    
    window.location.href = redirectPath;
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  // Protected route component
  const ProtectedRoute = ({ children, allowedRoles }) => {
    if (!currentUser) {
      return <Navigate to="/login" replace />;
    }

    return children;
  };

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[var(--content-bg)] flex items-center justify-center overflow-hidden">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--primary-main)]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-screen flex flex-col bg-[var(--content-bg)]">
      <Routes>
        <Route
          path="/"
          element={<LandingPage />}
        />

        <Route
          path="/login"
          element={
            <div className="h-screen w-screen bg-[var(--content-bg)] flex items-center justify-center p-4 overflow-hidden">
              <div className="w-full max-w-md">
                <LoginPage onLogin={handleLogin} />
              </div>
            </div>}
        />

        <Route element={
          <ProtectedRoute>
            <MainLayout currentUser={currentUser} onLogout={handleLogout} />
          </ProtectedRoute>
        }>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analyst" element={<AnalystDashboard />} />
          <Route path="/supervisor" element={<SupervisorDashboard />} />
          <Route path="/analysis" element={<DocumentUpload />} />
          <Route path="/analysis-results" element={<AnalysisResults />} />
          <Route path="/analysis-results/:id" element={<AnalysisResults />} />
          <Route path="/visualization" element={<VisualizationPage />} />
          <Route path="/visualization/:id" element={<VisualizationPage />} />
          <Route path="/traceability" element={<Traceability />} />
          <Route path="/traceability/:id" element={<Traceability />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/users" element={<UserManagement />} />
        </Route>


        <Route
          path="/docs"
          element={<LandingPage />}
        />

        <Route path="/test-mermaid" element={<TestMermaid />} />
      </Routes>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;