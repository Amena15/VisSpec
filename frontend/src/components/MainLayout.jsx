import React, { useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { Sun, Moon, Brain, Menu, User, ChevronDown, LogOut, Settings, ChevronRight, Home, BarChart3, FileText, ClipboardCheck, FolderOpen } from 'lucide-react';

const MainLayout = ({ currentUser, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // 1. Handle dark mode (unchanged)
  useEffect(() => {
    const saved = localStorage.theme;
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const nextDark = saved === 'dark' || (!saved && prefersDark);
    setIsDarkMode(nextDark);
    if (nextDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, []);

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) document.documentElement.classList.add('dark');
      else document.documentElement.classList.remove('dark');
      localStorage.theme = next ? 'dark' : 'light';
      return next;
    });
  };

  // 2. Guard: if currentUser is not yet loaded, show loading spinner
  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-screen w-screen bg-gray-50 dark:bg-gray-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // 3. Navigation items – now safe because currentUser is guaranteed to exist
  const navItems = currentUser.role === 'supervisor'
    ? [
        { name: 'Dashboard', href: '/supervisor', icon: Home },
        { name: 'Reports', href: '/supervisor/reports', icon: BarChart3 },
        { name: 'Review Queue', href: '/supervisor/review-queue', icon: ClipboardCheck },
        { name: 'Settings', href: '/settings', icon: Settings },
      ]
    : [
        { name: 'Dashboard', href: '/analyst', icon: Home },
        { name: 'Document Analysis', href: '/analysis', icon: FileText },
        { name: 'Visualization', href: '/visualization', icon: BarChart3 },
        { name: 'Traceability', href: '/traceability', icon: ClipboardCheck },
        { name: 'My Documents', href: '/documents', icon: FolderOpen },
        { name: 'Settings', href: '/settings', icon: Settings },
      ];

  // Helper to get page title (uses location)
  const getPageTitle = () => {
    if (location.pathname.includes('supervisor')) return 'Supervisor Dashboard';
    if (location.pathname.includes('analyst')) return 'Analyst Dashboard';
    if (location.pathname.includes('analysis')) return 'Document Analysis';
    if (location.pathname.includes('visualization')) return 'Visualization';
    if (location.pathname.includes('traceability')) return 'Traceability Matrix';
    if (location.pathname.includes('documents')) return currentUser.role === 'supervisor' ? 'Documents' : 'My Documents';
    if (location.pathname.includes('users')) return 'User Management';
    if (location.pathname.includes('settings')) return 'Settings';
    return 'Dashboard';
  };

  return (
    <div className={`flex h-screen w-screen overflow-hidden ${isDarkMode ? 'bg-gray-950 text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      {/* Sidebar (unchanged except using navItems) */}
      <div className={`fixed md:relative z-50 h-full ${isDarkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'} transition-all duration-300 ease-in-out ${sidebarOpen ? 'w-60 translate-x-0' : 'w-0 -translate-x-full'} md:${sidebarOpen ? 'w-60' : 'w-0'} md:${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} ${sidebarOpen ? 'flex' : 'hidden'} md:flex md:flex-shrink-0 overflow-hidden`}>
        <div className="flex flex-col w-60 h-full">
          <div className={`h-16 flex items-center px-4 border-b ${isDarkMode ? 'border-gray-800' : 'border-gray-200'}`}>
            <div className="flex items-center">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mr-3 ${isDarkMode ? 'bg-gradient-to-br from-blue-600 to-blue-700' : 'bg-gradient-to-br from-blue-500 to-blue-600'}`}>
                <Brain className="h-5 w-5 text-white" />
              </div>
              <h1 
                onClick={() => navigate(currentUser.role === 'supervisor' ? '/supervisor' : '/analyst')}
                className={`text-xl font-bold transition-colors cursor-pointer ${isDarkMode ? 'text-gray-100 hover:text-blue-400' : 'text-gray-900 hover:text-blue-600'}`}
              >
                VisSpec
              </h1>
            </div>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto py-5">
            <nav className="flex-1 px-2 space-y-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.href || 
                                 (item.href !== '/' && location.pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <button
                    key={item.name}
                    onClick={() => navigate(item.href)}
                    className={`flex items-center px-3 py-2 rounded-lg transition-all duration-200 ${
                      isActive 
                        ? (isDarkMode ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30' : 'bg-blue-50 text-blue-700 border border-blue-200')
                        : (isDarkMode ? 'hover:bg-gray-800 text-gray-300 border border-transparent' : 'hover:bg-gray-100 text-gray-700 border border-transparent')
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0 mr-3" />
                    <span className="truncate">{item.name}</span>
                    {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Overlay for sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Main Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <header className={`h-16 flex-shrink-0 border-b flex items-center justify-between px-6 ${isDarkMode ? 'border-gray-800 bg-gray-900/50 backdrop-blur-sm' : 'border-gray-200 bg-white/95 backdrop-blur-sm'}`}>
          {/* Left Side - Hamburger and Brain Logo */}
          <div className="flex items-center flex-1 min-w-0">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`p-2 rounded-lg transition-all duration-200 flex-shrink-0 ${isDarkMode ? 'hover:bg-gray-800 text-gray-300 active:bg-gray-700' : 'hover:bg-gray-100 text-gray-600 active:bg-gray-200'} ${sidebarOpen ? 'bg-blue-500/10 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400 border border-blue-200/50 dark:border-blue-700/50' : ''}`}
              title="Toggle sidebar"
            >
              <Menu className={`w-5 h-5 transition-transform duration-200 ${sidebarOpen ? 'rotate-90' : ''}`} />
            </button>
            
            <div className="flex items-center ml-4 flex-1 min-w-0">
              <div className={`flex items-center space-x-3 ${sidebarOpen ? 'hidden' : 'flex'}`}>
                <Brain className={`w-7 h-7 flex-shrink-0 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                <span className={`text-xl font-bold transition-colors cursor-pointer whitespace-nowrap ${isDarkMode ? 'text-gray-100 hover:text-blue-400' : 'text-gray-900 hover:text-blue-600'}`}
                      onClick={() => navigate(currentUser.role === 'supervisor' ? '/supervisor' : '/analyst')}>
                  VisSpec
                </span>
              </div>
              <div className="hidden lg:flex items-center ml-8">
                <div className="h-6 w-px bg-gray-300 dark:bg-slate-600 mr-4"></div>
                <h1 className="text-lg font-medium text-gray-700 dark:text-gray-300 truncate">
                  {getPageTitle()}
                </h1>
              </div>
            </div>
          </div>

          {/* Right Side */}
          <div className="flex items-center space-x-3 flex-shrink-0">
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? <Sun className="w-5 h-5 text-amber-500" /> : <Moon className="w-5 h-5 text-slate-600" />}
            </button>

            {/* User Profile Dropdown */}
            <div className="relative">
              <button 
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="hidden md:block text-left">
                  <div className="text-sm font-medium text-gray-900 dark:text-white capitalize">{currentUser.username || 'User'}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">{currentUser.role}</div>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 dark:text-gray-500 transition-transform ${profileDropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              
              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-gray-200 dark:border-slate-700 z-50">
                  <div className="p-2">
                    <button 
                      onClick={() => {
                        navigate('/profile');
                        setProfileDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm rounded-lg flex items-center transition-colors ${isDarkMode ? 'text-gray-300 hover:bg-slate-700' : 'text-gray-700 hover:bg-gray-100'}`}
                    >
                      <User className={`w-4 h-4 mr-3 ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`} />
                      Profile
                    </button>
                    <button 
                      onClick={() => {
                        navigate('/settings');
                        setProfileDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-sm rounded-lg flex items-center transition-colors ${isDarkMode ? 'text-gray-300 hover:bg-slate-700' : 'text-gray-700 hover:bg-gray-100'}`}
                    >
                      <Settings className={`w-4 h-4 mr-3 ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`} />
                      Settings
                    </button>
                    <div className="border-t border-gray-200 dark:border-slate-700 my-1"></div>
                    <button 
                      onClick={() => {
                        onLogout();
                        setProfileDropdownOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg flex items-center transition-colors"
                    >
                      <LogOut className="w-4 h-4 mr-3" />
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className={`flex-1 overflow-y-auto p-8 ${isDarkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;