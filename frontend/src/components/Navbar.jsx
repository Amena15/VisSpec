import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { UserCircleIcon, ChartBarIcon, DocumentTextIcon, Cog6ToothIcon, ArrowLeftOnRectangleIcon } from '@heroicons/react/24/outline';

const Navbar = ({ currentUser, onLogout }) => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: currentUser.role === 'supervisor' ? '/supervisor' : '/analyst', icon: ChartBarIcon },
    { name: 'Analysis', path: '/analysis', icon: DocumentTextIcon },
    { name: 'Visualization', path: '/visualization', icon: Cog6ToothIcon },
    { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
  ];

  return (
    <nav className="bg-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-white text-xl font-bold">VisSpec</h1>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    to={item.path}
                    className={`${
                      location.pathname === item.path
                        ? 'bg-slate-900 text-white'
                        : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                    } px-3 py-2 rounded-md text-sm font-medium flex items-center`}
                  >
                    <item.icon className="h-5 w-5 mr-2" />
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              <div className="ml-3 relative">
                <div className="flex items-center space-x-3">
                  <UserCircleIcon className="h-8 w-8 text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-white">{currentUser.username}</p>
                    <p className="text-xs font-medium text-slate-400 capitalize">{currentUser.role}</p>
                  </div>
                  <button
                    onClick={onLogout}
                    className="ml-4 bg-slate-700 p-1 rounded-full text-slate-400 hover:text-white focus:outline-none"
                  >
                    <ArrowLeftOnRectangleIcon className="h-6 w-6" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className="md:hidden">
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={`${
                location.pathname === item.path
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              } block px-3 py-2 rounded-md text-base font-medium flex items-center`}
            >
              <item.icon className="h-5 w-5 mr-2" />
              {item.name}
            </Link>
          ))}
          <button
            onClick={onLogout}
            className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:bg-slate-700 hover:text-white flex items-center"
          >
            <ArrowLeftOnRectangleIcon className="h-5 w-5 mr-2" />
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;