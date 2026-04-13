import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();

  // Redirect to appropriate dashboard based on user role
  useEffect(() => {
    // In a real app, we would get the user role from context or auth state
    // For now, we'll redirect to analyst dashboard by default
    // The actual role-based redirect should happen in the Navbar or MainLayout
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // Decode the token to get user role
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const userData = JSON.parse(jsonPayload);
        const userRole = userData.role;

        // Redirect based on role
        if (userRole === 'supervisor') {
          navigate('/supervisor', { replace: true });
        } else {
          navigate('/analyst', { replace: true });
        }
      } catch (error) {
        console.error('Error decoding token:', error);
        // Default to analyst dashboard if token decoding fails
        navigate('/analyst', { replace: true });
      }
    } else {
      // If not logged in, redirect to login
      navigate('/login', { replace: true });
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--primary-main)] mx-auto mb-4"></div>
        <p className="text-[var(--text-primary)]">Redirecting to your dashboard...</p>
      </div>
    </div>
  );
};

export default Dashboard;