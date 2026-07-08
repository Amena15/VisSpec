import React, { useState, useEffect } from 'react';
import {
  Users,
  ClipboardCheck,
  BarChart3,
  Clock,
  CheckCircle,
  X,
  AlertTriangle,
  Eye,
  FileText,
  TrendingUp,
  Download,
  MessageSquare
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../services/api';
import { toast } from 'sonner';

// Helper function to get color based on score
const getScoreColor = (score) => {
  if (score > 80) return '#10B981'; // Emerald Green
  if (score > 50) return '#F59E0B'; // Amber
  return '#EF4444'; // Red
};

const SupervisorDashboard = () => {
  // Existing state
  const [projects, setProjects] = useState([]);
  const [isExporting, setIsExporting] = useState(false);
  const [stats, setStats] = useState({
    totalProjects: 0,
    pendingReviews: 0,
    approvedProjects: 0,
    rejectedProjects: 0
  });
  const [activeTab, setActiveTab] = useState('pending'); // Only show pending reviews by default
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [selectedComment, setSelectedComment] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);

  const formatDisplayDate = (value) => {
    if (!value) return 'Date pending';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return 'Date pending';
    return parsed.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Load real data from API
  useEffect(() => {
    const loadSupervisorData = async () => {
      try {
        // Load dashboard data
        const [projectsRes, metricsRes] = await Promise.all([
          apiClient.get('/api/supervisor/dashboard'),
          apiClient.get('/api/supervisor/metrics')
        ]);

        const projectsFromApi = projectsRes.data || [];
        const metricsData = metricsRes.data || {};

        const normalized = projectsFromApi.map((p) => ({
          id: p.project_id,
          title: p.name,
          developer: p.owner,
          ownerEmail: null,
          submittedAt: p.last_updated || p.created_at || p.updated_at || 'Date pending',
          lastReviewed: null,
          status: p.review_status || 'not_reviewed',
          qualityScore: p.quality_score ?? 0,
          complexity: p.complexity_level || 'N/A',
          defects: p.defect_count ?? 0,
          comments: null,
          priority: 'medium',
        }));

        setProjects(normalized);

        // Use metrics from API for accurate stats
        setStats({
          totalProjects: metricsData.total_projects || normalized.length,
          pendingReviews: metricsData.review_status_counts?.not_reviewed || 0,
          approvedProjects: metricsData.review_status_counts?.approved || 0,
          rejectedProjects: metricsData.review_status_counts?.changes_requested || 0,
        });
      } catch (error) {
        console.error('Failed to load supervisor data:', error);
        toast.error('Failed to load dashboard data');
      }
    };

    loadSupervisorData();
  }, []);

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
      case 'changes_requested': return <X className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  // Filter projects based on active tab
  const filteredProjects = projects.filter(project => {
    if (activeTab === 'all') return true;
    if (activeTab === 'pending') return project.status === 'not_reviewed';
    return project.status === activeTab;
  });

  const stabilityScore = projects.length
    ? Math.round(
        projects.reduce((sum, project) => sum + Number(project.qualityScore || 0), 0) / projects.length
      )
    : 0;

  const totalDefects = projects.reduce((sum, project) => sum + Number(project.defects || 0), 0);

  const exportPredictionPdf = async () => {
    try {
      setIsExporting(true);

      const traceabilityRows = projects.map((project) => ({
        req_id: project.id,
        identifier: project.title,
        validation_status: project.status,
        defect_count: project.defects || 0,
        complexity: project.complexity || 'N/A',
        source_document: `${project.developer || 'Unknown Owner'} - submitted ${formatDisplayDate(project.submittedAt)}`,
        text: `Project ${project.title} reviewed by supervisor workflow.`,
        visual_elements: [],
        defects: [],
      }));

      const reportData = {
        report_type: 'supervisor',
        project_name: 'Supervisor Dashboard',
        analysis_data: {
          total_requirements: projects.length,
          quality_score: stabilityScore,
          defect_count: totalDefects,
          review_status: 'supervisor_dashboard',
        },
        metrics: {
          validation_status: {
            passed: stats.approvedProjects,
            warning: stats.pendingReviews,
            failed: stats.rejectedProjects,
          },
          completion_rate: stats.totalProjects
            ? Math.round(((stats.approvedProjects + stats.rejectedProjects) / stats.totalProjects) * 100)
            : 0,
        },
        traceability: traceabilityRows,
        diagrams: [],
      };

      const response = await apiClient.post('/api/reports/export', reportData, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `supervisor_prediction_analysis_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Supervisor prediction report exported successfully');
    } catch (error) {
      console.error('Failed to export supervisor prediction report:', error);
      toast.error('Failed to export supervisor report');
    } finally {
      setIsExporting(false);
    }
  };

  return (
  <div className="py-8">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

      {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <FileText className="w-6 h-6 text-[var(--primary-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Total Projects</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.totalProjects}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <ClipboardCheck className="w-6 h-6 text-[var(--warning-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Pending Reviews</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.pendingReviews}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <CheckCircle className="w-6 h-6 text-[var(--success-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Approved</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.approvedProjects}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <X className="w-6 h-6 text-[var(--error-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Rejected</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.rejectedProjects}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Projects Section with Clean Filter */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-6">
            <div className="px-6 py-4 border-b border-[var(--card-border)] flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Projects</h2>
              
              {/* Filter Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('pending')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'pending'
                      ? 'bg-[var(--primary-main)] text-white'
                      : 'bg-[var(--surface-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  Pending ({stats.pendingReviews})
                </button>
                <button
                  onClick={() => setActiveTab('all')}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === 'all'
                      ? 'bg-[var(--primary-main)] text-white'
                      : 'bg-[var(--surface-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                  }`}
                >
                  All Projects
                </button>
              </div>
            </div>
          </div>

          {/* Projects Table */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-10">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[var(--card-border)]">
                <thead className="bg-[var(--surface-bg)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Project</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Developer</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Submitted</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Quality</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Complexity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Defects</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Comments</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                  {filteredProjects.map((project) => (
                    <tr key={project.id} className="hover:bg-[var(--surface-bg)] transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-[var(--text-primary)]">{project.title}</div>
                        <div className="text-xs text-[var(--text-secondary)]">Submitted: {formatDisplayDate(project.submittedAt)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-2 text-[var(--text-secondary)]" />
                          <span className="text-sm text-[var(--text-primary)]">{project.developer}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        {formatDisplayDate(project.submittedAt)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
                          {getStatusIcon(project.status)}
                          <span className="ml-1 capitalize">{project.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <TrendingUp className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="text-sm font-medium text-[var(--text-primary)]">{project.qualityScore}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <BarChart3 className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="text-sm font-medium text-[var(--text-primary)]">{project.complexity || 'Medium'}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <AlertTriangle className="w-4 h-4 mr-1 text-[var(--warning-main)]" />
                          <span className="text-sm text-[var(--text-primary)]">{project.defects}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        <button 
                          onClick={() => {
                            setSelectedComment(project.comments || 'No comments available');
                            setSelectedProject(project);
                            setShowCommentModal(true);
                          }}
                          className="flex items-center hover:text-[var(--primary-main)] transition-colors"
                        >
                          <MessageSquare className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="truncate max-w-[80px]" title={project.comments || 'No comments'}>{project.comments || 'None'}</span>
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          to={`/supervisor/review/${project.id}`}
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
                  No projects found in this category
                </div>
              )}
            </div>
          </div>

          {/* Comment Modal */}
          {showCommentModal && selectedProject && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-[var(--card-bg)] rounded-xl shadow-lg max-w-md w-full border border-[var(--card-border)]">
                <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">Project Comments</h3>
                  <button 
                    onClick={() => setShowCommentModal(false)}
                    className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="p-6">
                  <div className="mb-4">
                    <h4 className="font-medium text-[var(--text-primary)] mb-1">{selectedProject.title}</h4>
                    <p className="text-sm text-[var(--text-secondary)]">Developer: {selectedProject.developer}</p>
                  </div>
                  <div className="bg-[var(--surface-bg)] rounded-lg p-4 border border-[var(--card-border)]">
                    <p className="text-[var(--text-primary)]">{selectedComment}</p>
                  </div>
                </div>
                <div className="px-6 py-4 border-t border-[var(--card-border)] flex justify-end">
                  <button
                    onClick={() => setShowCommentModal(false)}
                    className="px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Prediction Analysis Card */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-12">
            <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Prediction Analysis</h2>
              <button
                onClick={exportPredictionPdf}
                disabled={isExporting || projects.length === 0}
                className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4 mr-2" />
                {isExporting ? 'Exporting...' : 'Export PDF'}
              </button>
            </div>
            
            <div className="p-6">
              <div className="flex flex-col lg:flex-row gap-8">
                {/* Quality Score Section */}
                <div className="flex-1 flex flex-col items-center justify-center">
                  <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-48 h-48" viewBox="0 0 100 100">
                      {/* Background circle */}
                      <circle 
                        cx="50" 
                        cy="50" 
                        r="45" 
                        fill="none" 
                        stroke="#F3F4F6" 
                        strokeWidth="8" 
                      />
                      {/* Progress circle - color based on score */}
                      <circle 
                        cx="50" 
                        cy="50" 
                        r="45" 
                        fill="none" 
                              stroke={getScoreColor(stabilityScore)} 
                        strokeWidth="8" 
                        strokeDasharray="283" 
                              strokeDashoffset={283 - (283 * stabilityScore) / 100} 
                        strokeLinecap="round"
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-3xl font-bold text-gray-900">{stabilityScore}%</span>
                      <span className="text-sm text-gray-600">Stability Score</span>
                    </div>
                  </div>
                </div>
                
                {/* Risk Breakdown and Prediction Statement */}
                <div className="flex-1 flex flex-col justify-center">
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">System Behavior Prediction</h3>
                    <p className="text-gray-600 bg-gray-50 p-4 rounded-lg border border-gray-200">
                      System behavior is {stabilityScore}% deterministic based on current supervisor portfolio metrics.
                      {stabilityScore >= 80
                        ? ' Recommended for production with minimal risk mitigation.'
                        : ' Additional quality improvements are recommended before production approval.'}
                    </p>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Risk Factors</h4>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#EF4444] mr-2"></div>
                      <span className="text-sm text-gray-600">Critical:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">{stats.rejectedProjects} Projects</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#F59E0B] mr-2"></div>
                      <span className="text-sm text-gray-600">Warnings:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">{stats.pendingReviews} Pending Reviews</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#10B981] mr-2"></div>
                      <span className="text-sm text-gray-600">Stable:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">{stats.approvedProjects} Approved Projects</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default SupervisorDashboard;