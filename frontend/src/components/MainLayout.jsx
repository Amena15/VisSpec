import React, { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Sun, Moon, Brain } from 'lucide-react';

const MainLayout = ({ currentUser, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Navigation items for all users
  // Navigation items differ based on user role
  const navItems = currentUser.role === 'supervisor'
    ? [
        { name: 'Dashboard', href: '/supervisor', icon: 'dashboard' },
        { name: 'Document Analysis', href: '/analysis', icon: 'analysis' },
        { name: 'Visualization', href: '/visualization', icon: 'visualization' },
        { name: 'Traceability', href: '/traceability', icon: 'traceability' },
        { name: 'Documents', href: '/documents', icon: 'documents' },
        { name: 'User Management', href: '/users', icon: 'users' },
        { name: 'Settings', href: '/settings', icon: 'settings' },
      ]
    : [
        { name: 'Dashboard', href: '/analyst', icon: 'dashboard' },
        { name: 'Document Analysis', href: '/analysis', icon: 'analysis' },
        { name: 'Visualization', href: '/visualization', icon: 'visualization' },
        { name: 'Traceability', href: '/traceability', icon: 'traceability' },
        { name: 'My Documents', href: '/documents', icon: 'documents' },
        { name: 'Settings', href: '/settings', icon: 'settings' },
      ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--content-bg)] text-[var(--neutral-900)]">
      {/* Sidebar - Clean Enterprise Design */}
      <div className="fixed md:relative md:translate-x-0 z-50 h-full bg-[var(--card-bg)] border-r border-[var(--card-border)] transition-transform duration-300 ease-in-out w-60 md:flex md:w-60 md:flex-shrink-0">
        <div className="flex flex-col w-60 h-full">
          <div className="h-16 flex items-center px-4 border-b border-[var(--card-border)]">
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-[var(--primary-main)]/10 flex items-center justify-center mr-3">
                <Brain className="h-5 w-5 text-[var(--primary-main)]" />
              </div>
              <h1 
                onClick={() => navigate(currentUser?.role === 'supervisor' ? '/supervisor' : '/analyst')}
                className="text-xl font-bold text-[var(--text-primary)] hover:text-[var(--primary-main)] transition-colors cursor-pointer"
              >
                VisSpec
              </h1>
            </div>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto py-5">
            <nav className="flex-1 px-2 space-y-1">
              {navItems.map((item) => (
                <button
                  key={item.name}
                  onClick={() => navigate(item.href)}
                  className={`${
                    location.pathname === item.href
                      ? `flex items-center gap-3 px-4 py-3 bg-blue-50 text-blue-700 font-medium rounded-lg`  // Active item with pill-shaped highlight
                      : `flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg`  // Inactive item
                  } group w-full transition-colors`}
                >
                  <span className="mr-3">
                    {item.icon === 'dashboard' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v0a2 2 0 01-2 2H10a2 2 0 01-2-2V5z" />
                      </svg>
                    )}
                    {item.icon === 'analysis' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    )}
                    {item.icon === 'visualization' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                    {item.icon === 'documents' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                    {item.icon === 'review' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                    )}
                    {item.icon === 'metrics' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    )}
                    {item.icon === 'users' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    )}
                    {item.icon === 'traceability' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 13.828l-4.242 4.242a1 1 0 01-1.414 0l-4.242-4.242a1 1 0 010-1.414l4.242-4.242a1 1 0 011.414 0l4.242 4.242a1 1 0 010 1.414z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12a9 9 0 1118 0 9 9 0 01-18 0z" />
                      </svg>
                    )}
                    {item.icon === 'settings' && (
                      <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </span>
                  {item.name}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Main Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Navigation Bar - Professional Enterprise Design */}
        <header className="flex items-center justify-between h-16 px-8 bg-white border-b border-[var(--card-border)] shadow-sm">
          <div className="flex items-center space-x-4">
            <button
              type="button"
              className="md:hidden text-[var(--text-secondary)]"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <span className="sr-only">Open sidebar</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-[var(--primary-main)]/10 flex items-center justify-center mr-3">
                <Brain className="h-5 w-5 text-[var(--primary-main)]" />
              </div>
              <h1 className="text-[var(--text-secondary)] font-medium text-sm uppercase tracking-wide">
                {location.pathname.includes('supervisor') ? 'Supervisor Dashboard' :
                 location.pathname.includes('analyst') ? 'Analyst Dashboard' :
                 location.pathname.includes('analysis') ? 'Document Analysis' :
                 location.pathname.includes('visualization') ? 'Visualization' :
                 location.pathname.includes('traceability') ? 'Traceability Matrix' :
                 location.pathname.includes('documents') ? (currentUser.role === 'supervisor' ? 'Documents' : 'My Documents') :
                 location.pathname.includes('users') ? 'User Management' :
                 location.pathname.includes('settings') ? 'Settings' : 'Dashboard'}
              </h1>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {/* Removed Dark Mode Toggle for consistency with new design */}
            <div className="relative">
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <div className="w-8 h-8 bg-gray-700 text-white rounded-full flex items-center justify-center text-sm font-semibold">
                  {currentUser?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="text-sm font-medium capitalize">{currentUser?.username || 'User'}</span>
                <svg className={`h-4 w-4 transition-transform ${profileDropdownOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 z-50 border border-gray-200 bg-white">
                  <button
                    onClick={() => {
                      onLogout();
                      setProfileDropdownOpen(false);
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content Scroll */}
        <main className="flex-1 overflow-y-auto p-8 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;