import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import { authAPI } from './services/api';
import { Toaster } from 'sonner';

import LoginPage from './pages/LoginPage';
import DebugLoginRequest from './pages/DebugLoginRequest';
import AnalystDashboard from './pages/AnalystDashboard';
import SupervisorDashboard from './pages/SupervisorDashboard';
import SupervisorReview from './pages/SupervisorReview';
import SupervisorReports from './pages/SupervisorReports';
import SupervisorReviewQueue from './pages/SupervisorReviewQueue';

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
import DashboardLayout from './components/layout/DashboardLayout';


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

          // Fetch profile to get username (JWT may omit it)
          authAPI
            .getProfile()
            .then((profileRes) => {
              const profile = profileRes?.data;
              if (profile) {
                setCurrentUser((prev) => ({
                  ...(prev || {}),
                  ...(profile.user || profile),
                }));
              }
            })
            .catch((e) => {
              console.warn('Failed to fetch profile:', e);
              // Best-effort fallback normalization
              setCurrentUser((prev) => {
                const next = { ...(prev || {}) };
                if (!next.username) {
                  if (next.email) next.username = String(next.email).split('@')[0];
                  else if (next.name) next.username = next.name;
                }
                return next;
              });
            });
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

  const handleLogin = async (token) => {
    localStorage.setItem('token', token);

    // IMPORTANT: token may be slightly different shape depending on backend.
    // We store exactly what jwtDecode reads so ProtectedRoute can work immediately.
    const decoded = jwtDecode(token);

    setCurrentUser(decoded);

    // Fetch profile from backend to ensure username is correct (JWT might not include it)
    try {
      const profileRes = await authAPI.getProfile();
      const profile = profileRes?.data;
      if (profile) {
        setCurrentUser((prev) => ({
          ...(prev || {}),
          ...(profile.user || profile),
        }));
      }
    } catch (e) {
      // Keep whatever we have from token if profile fetch fails
      console.warn('Failed to fetch profile:', e);
      // Best-effort fallback normalization
      setCurrentUser((prev) => {
        const next = { ...(prev || {}) };
        if (!next.username) {
          if (next.email) next.username = String(next.email).split('@')[0];
          else if (next.name) next.username = next.name;
        }
        return next;
      });
    }

    // Redirect to appropriate dashboard based on user role
    let redirectPath = '/dashboard';
    const role = decoded?.role;
    if (role === 'developer' || role === 'student' || role === 'analyst') {
      redirectPath = '/analyst';
    } else if (role === 'supervisor') {
      redirectPath = '/supervisor';
    }

    // Avoid full reload; keep React router state stable.
    window.history.pushState({}, '', redirectPath);
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
  };

  // Protected route component
  const ProtectedRoute = ({ children, allowedRoles }) => {
    // If currentUser isn't set yet, try to recover from token.
    if (!currentUser) {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const decoded = jwtDecode(token);
          if (decoded?.exp && decoded.exp * 1000 > Date.now()) {
            // Keep it local; App-level state update is async so just render children.
            return children;
          }
        } catch (e) {
          // ignore, fall through to redirect
        }
      }
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
      <Routes future={{ 
        v7_startTransition: true,
        v7_relativeSplatPath: true 
      }}>
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
        <Route
          path="/debug-login"
          element={<div className="h-screen w-screen bg-[var(--content-bg)] overflow-hidden"><DebugLoginRequest /></div>}
        />

        <Route
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MainLayout currentUser={currentUser} onLogout={handleLogout} />
              </DashboardLayout>
            </ProtectedRoute>
          }
        >

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/analyst" element={<AnalystDashboard />} />
          <Route path="/supervisor" element={<SupervisorDashboard />} />
          <Route path="/supervisor/review/:project_id" element={<SupervisorReview />} />
          <Route path="/supervisor/reports" element={<SupervisorReports />} />
          <Route path="/supervisor/review-queue" element={<SupervisorReviewQueue />} />

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