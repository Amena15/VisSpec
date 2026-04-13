import React, { useState } from 'react';
import { Search, Filter, Plus, User, Shield, XCircle, CheckCircle, Eye, Edit, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

const UserManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [users, setUsers] = useState([
    {
      id: 1,
      username: 'john_doe',
      email: 'john@example.com',
      role: 'analyst',
      status: 'active',
      lastLogin: '2023-11-15',
      projects: 12
    },
    {
      id: 2,
      username: 'jane_smith',
      email: 'jane@example.com',
      role: 'supervisor',
      status: 'active',
      lastLogin: '2023-11-14',
      projects: 8
    },
    {
      id: 3,
      username: 'bob_johnson',
      email: 'bob@example.com',
      role: 'analyst',
      status: 'inactive',
      lastLogin: '2023-10-20',
      projects: 5
    },
    {
      id: 4,
      username: 'alice_williams',
      email: 'alice@example.com',
      role: 'analyst',
      status: 'active',
      lastLogin: '2023-11-15',
      projects: 15
    }
  ]);

  // Filter users based on search and role
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    return matchesSearch && matchesRole;
  });

  const getUserRoleBadge = (role) => {
    if (role === 'supervisor') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--surface-bg)] text-[var(--primary-main)]"><Shield className="w-3 h-3 mr-1" /> Supervisor</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--primary-50)] text-[var(--primary-main)]"><User className="w-3 h-3 mr-1" /> Analyst</span>;
  };

  const getUserStatusBadge = (status) => {
    if (status === 'active') {
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--success-light)] text-[var(--success-hover)]"><CheckCircle className="w-3 h-3 mr-1" /> Active</span>;
    }
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--error-light)] text-[var(--error-hover)]"><XCircle className="w-3 h-3 mr-1" /> Inactive</span>;
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">User Management</h1>
            <p className="text-[var(--text-secondary)] mt-1">Manage all system users and their permissions</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
            <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)]"
                />
              </div>

              <select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className="w-full sm:w-auto px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)]"
              >
                <option value="all">All Roles</option>
                <option value="analyst">Analyst</option>
                <option value="supervisor">Supervisor</option>
              </select>
            </div>

            <button className="mt-4 sm:mt-0 bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg flex items-center hover:bg-[var(--primary-hover)] transition-colors">
              <Plus className="h-4 w-4 mr-2" />
              Add User
            </button>
          </div>

          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[var(--card-border)]">
                <thead className="bg-[var(--surface-bg)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Last Login</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Projects</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-[var(--surface-bg)] transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="bg-[var(--surface-bg)] p-2 rounded-full mr-3">
                            <User className="w-5 h-5 text-[var(--text-secondary)]" />
                          </div>
                          <div>
                            <div className="text-sm font-medium text-[var(--text-primary)]">{user.username}</div>
                            <div className="text-sm text-[var(--text-secondary)]">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getUserRoleBadge(user.role)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getUserStatusBadge(user.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        {new Date(user.lastLogin).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-primary)]">
                        {user.projects}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] mr-3">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button className="text-[var(--warning-main)] hover:text-[var(--warning-hover)] mr-3">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button className="text-[var(--error-main)] hover:text-[var(--error-hover)]">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserManagement;