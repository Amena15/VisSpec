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
import { handleReviewClick } from '../utils/reviewHandler';

// Helper function to get color based on score
const getScoreColor = (score) => {
  if (score > 80) return '#10B981'; // Emerald Green
  if (score > 50) return '#F59E0B'; // Amber
  return '#EF4444'; // Red
};

const SupervisorDashboard = () => {
  const [projects, setProjects] = useState([]);
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

  // Mock data for demonstration
  useEffect(() => {
    // Simulate loading data
    const mockProjects = [
      {
        id: 1,
        title: 'Developer Registration System',
        developer: 'John Doe',
        submittedAt: '2025-10-24',
        lastReviewed: '2025-10-25',
        status: 'pending',
        qualityScore: 78,
        complexity: 'Medium',
        defects: 5,
        comments: 'Needs clarification on authentication flow'
      },
      {
        id: 2,
        title: 'E-Commerce Platform Requirements',
        developer: 'Jane Smith',
        submittedAt: '2025-10-23',
        lastReviewed: '2025-10-24',
        status: 'pending',
        qualityScore: 85,
        complexity: 'High',
        defects: 3,
        comments: 'Good structure, minor improvements needed'
      },
      {
        id: 3,
        title: 'Healthcare Management System',
        developer: 'Robert Johnson',
        submittedAt: '2025-10-22',
        lastReviewed: '2025-10-23',
        status: 'approved',
        qualityScore: 92,
        complexity: 'Low',
        defects: 1,
        comments: 'Excellent requirements specification'
      },
      {
        id: 4,
        title: 'Financial Reporting Tool',
        developer: 'Emily Davis',
        submittedAt: '2025-10-21',
        lastReviewed: '2025-10-22',
        status: 'rejected',
        qualityScore: 65,
        complexity: 'High',
        defects: 12,
        comments: 'Multiple ambiguities and contradictions found'
      }
    ];

    setProjects(mockProjects);

    // Calculate stats
    setStats({
      totalProjects: mockProjects.length,
      pendingReviews: mockProjects.filter(p => p.status === 'pending').length,
      approvedProjects: mockProjects.filter(p => p.status === 'approved').length,
      rejectedProjects: mockProjects.filter(p => p.status === 'rejected').length
    });
  }, []);

  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return 'bg-[var(--warning-light)] text-[var(--warning-hover)]';
      case 'approved': return 'bg-[var(--success-light)] text-[var(--success-hover)]';
      case 'rejected': return 'bg-[var(--error-light)] text-[var(--error-hover)]';
      default: return 'bg-[var(--surface-bg)] text-[var(--neutral-700)]';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'approved': return <CheckCircle className="w-4 h-4" />;
      case 'rejected': return <X className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  // Filter projects based on active tab
  const filteredProjects = projects.filter(project => {
    if (activeTab === 'all') return true;
    return project.status === activeTab;
  });

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">Supervisor Dashboard</h1>
            <p className="text-[var(--text-secondary)] mt-2">Review and validate developer projects</p>
          </div>

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

          {/* Simplified Tabs - Only essential ones */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-6">
            <div className="px-6 py-4 border-b border-[var(--card-border)]">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Projects</h2>
            </div>
            
            <div className="flex border-b border-[var(--card-border)]">
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-6 py-4 text-sm font-medium ${
                  activeTab === 'pending'
                    ? 'text-[var(--primary-main)] border-b-2 border-[var(--primary-main)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Pending Reviews ({stats.pendingReviews})
              </button>
              <button
                onClick={() => setActiveTab('all')}
                className={`px-6 py-4 text-sm font-medium ${
                  activeTab === 'all'
                    ? 'text-[var(--primary-main)] border-b-2 border-[var(--primary-main)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                All Projects
              </button>
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
                        <div className="text-xs text-[var(--text-secondary)]">Submitted: {project.submittedAt} | Last Reviewed: {project.lastReviewed || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Users className="w-4 h-4 mr-2 text-[var(--text-secondary)]" />
                          <span className="text-sm text-[var(--text-primary)]">{project.developer}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        {project.submittedAt}
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
                          to={`/traceability/${project.id}`}
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
              <button className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
                <Download className="w-4 h-4 mr-2" />
                Export PDF
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
                        stroke="#10B981" 
                        strokeWidth="8" 
                        strokeDasharray="283" 
                        strokeDashoffset={283 - (283 * 85) / 100} 
                        strokeLinecap="round"
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-3xl font-bold text-gray-900">85%</span>
                      <span className="text-sm text-gray-600">Stability Score</span>
                    </div>
                  </div>
                </div>
                
                {/* Risk Breakdown and Prediction Statement */}
                <div className="flex-1 flex flex-col justify-center">
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">System Behavior Prediction</h3>
                    <p className="text-gray-600 bg-gray-50 p-4 rounded-lg border border-gray-200">
                      System behavior is 85% deterministic. Recommended for production with minimal risk mitigation.
                    </p>
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Risk Factors</h4>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#EF4444] mr-2"></div>
                      <span className="text-sm text-gray-600">Critical:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">2 Defects</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#F59E0B] mr-2"></div>
                      <span className="text-sm text-gray-600">Warnings:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">5 Defects</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full bg-[#10B981] mr-2"></div>
                      <span className="text-sm text-gray-600">Stable:</span>
                      <span className="text-sm font-medium text-gray-900 ml-1">3 Defects</span>
                    </div>
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