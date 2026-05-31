import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  BarChart3,
  Users,
  Calendar,
  Filter,
  Loader2,
  TrendingUp
} from 'lucide-react';
import { apiClient } from '../services/api';

const SupervisorReviewQueue = () => {
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    loadReviewQueue();
  }, []);

  const loadReviewQueue = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/api/supervisor/review-queue');
      setProjects(response.data || []);
    } catch (error) {
      console.error('Failed to load review queue:', error);
      toast.error('Failed to load review queue');
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    switch(priority) {
      case 'high': return 'bg-[var(--error-light)] text-[var(--error-hover)]';
      case 'medium': return 'bg-[var(--warning-light)] text-[var(--warning-hover)]';
      case 'low': return 'bg-[var(--success-light)] text-[var(--success-hover)]';
      default: return 'bg-[var(--surface-bg)] text-[var(--neutral-700)]';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'not_reviewed': return 'bg-[var(--warning-light)] text-[var(--warning-hover)]';
      case 'approved': return 'bg-[var(--success-light)] text-[var(--success-hover)]';
      case 'changes_requested': return 'bg-[var(--error-light)] text-[var(--error-hover)]';
      default: return 'bg-[var(--surface-bg)] text-[var(--neutral-700)]';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'not_reviewed': return <Clock className="w-4 h-4" />;
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'changes_requested': return <XCircle className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getPriorityIcon = (priority) => {
    switch(priority) {
      case 'high': return <AlertTriangle className="w-4 h-4 text-[var(--error-main)]" />;
      case 'medium': return <Clock className="w-4 h-4 text-[var(--warning-main)]" />;
      case 'low': return <CheckCircle className="w-4 h-4 text-[var(--success-main)]" />;
      default: return <Clock className="w-4 h-4 text-[var(--text-secondary)]" />;
    }
  };

  const filteredProjects = projects.filter(project => {
    if (filterStatus === 'all') return true;
    return project.review_status === filterStatus;
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-[var(--primary-main)] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">Review Queue</h1>
            <p className="text-[var(--text-secondary)] mt-2">Projects pending supervisor review and approval</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--warning-light)] mr-4">
                  <Clock className="w-6 h-6 text-[var(--warning-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Pending Reviews</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {projects.filter(p => p.review_status === 'not_reviewed').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--error-light)] mr-4">
                  <XCircle className="w-6 h-6 text-[var(--error-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Changes Requested</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {projects.filter(p => p.review_status === 'changes_requested').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <TrendingUp className="w-6 h-6 text-[var(--primary-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">High Priority</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">
                    {projects.filter(p => p.priority === 'high').length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Filter */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Filter className="w-5 h-5 text-[var(--text-secondary)]" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg text-sm"
                >
                  <option value="all">All Projects</option>
                  <option value="not_reviewed">Not Reviewed</option>
                  <option value="changes_requested">Changes Requested</option>
                </select>
              </div>
              <div className="text-sm text-[var(--text-secondary)]">
                Showing {filteredProjects.length} of {projects.length} projects
              </div>
            </div>
          </div>

          {/* Projects Table */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[var(--card-border)]">
                <thead className="bg-[var(--surface-bg)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Project</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Owner</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Priority</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Quality</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Defects</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Last Updated</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                  {filteredProjects.map((project) => (
                    <tr key={project.project_id} className="hover:bg-[var(--surface-bg)] transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-[var(--text-primary)]">{project.name}</div>
                          <div className="text-xs text-[var(--text-secondary)]">ID: {project.project_id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-2 text-[var(--text-secondary)]" />
                          <div>
                            <div className="text-sm text-[var(--text-primary)]">{project.owner}</div>
                            <div className="text-xs text-[var(--text-secondary)]">{project.owner_email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getPriorityIcon(project.priority)}
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(project.priority)}`}>
                            {project.priority}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <BarChart3 className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="text-sm font-medium text-[var(--text-primary)]">{project.quality_score || 0}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <AlertTriangle className="w-4 h-4 mr-1 text-[var(--warning-main)]" />
                          <span className="text-sm text-[var(--text-primary)]">{project.defect_count || 0}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.review_status)}`}>
                          {getStatusIcon(project.review_status)}
                          <span className="ml-1 capitalize">{project.review_status?.replace('_', ' ')}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        {project.last_updated ? new Date(project.last_updated).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          to={`/supervisor/review/${project.project_id}`}
                          className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] flex items-center"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {filteredProjects.length === 0 && (
                <div className="text-center py-12 text-[var(--text-secondary)]">
                  {filterStatus === 'all' ? 'No projects in review queue' : `No projects with status: ${filterStatus.replace('_', ' ')}`}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupervisorReviewQueue;
