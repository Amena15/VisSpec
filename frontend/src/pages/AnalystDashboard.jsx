import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  AlertTriangle,
  CheckCircle,
  FileText,
  Clock,
  TrendingUp,
  FolderOpen,
  User,
  Users,
  ClipboardCheck,
  Download,
  MessageSquare,
  X,
  Eye,
  AlertCircle,
  Check
} from 'lucide-react';
import { DocumentTextIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { handleReviewClick } from '../utils/reviewHandler';
import { toast } from 'sonner';

// Helper function to get color based on score
const getScoreColor = (score) => {
  if (score > 80) return '#10B981'; // Emerald Green
  if (score > 50) return '#F59E0B'; // Amber
  return '#EF4444'; // Red
};

const AnalystDashboard = () => {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    analyzedDocuments: 0,
    avgQualityScore: 0,
    totalDefects: 0,
    myProjects: 0,
    completedProjects: 0,
    inProgressProjects: 0
  });
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [selectedComment, setSelectedComment] = useState('');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportDocument, setReportDocument] = useState(null);

  // Mock data for demonstration - showing only analyst's own documents/projects
  useEffect(() => {
    // Simulate loading data
    const mockDocuments = [
      {
        id: 1,
        title: 'User Registration Requirements',
        uploadedAt: '2025-10-24',
        updatedAt: '2025-10-25',
        status: 'completed',
        qualityScore: 78,
        complexity: 'Medium',
        defects: 5,
        effortEstimate: '12 weeks',
        comments: 'Well-structured requirements with minor ambiguities'
      },
      {
        id: 2,
        title: 'E-Commerce Platform Specs',
        uploadedAt: '2025-10-23',
        updatedAt: '2025-10-24',
        status: 'completed',
        qualityScore: 85,
        complexity: 'High',
        defects: 3,
        effortEstimate: '10 weeks',
        comments: 'Excellent specification with clear acceptance criteria'
      },
      {
        id: 3,
        title: 'Healthcare System Requirements',
        uploadedAt: '2025-10-22',
        updatedAt: '2025-10-23',
        status: 'in-progress',
        qualityScore: 92,
        complexity: 'Low',
        defects: 1,
        effortEstimate: '8 weeks',
        comments: 'High quality requirements, almost ready for approval'
      },
      {
        id: 4,
        title: 'Financial Reporting Tool Specs',
        uploadedAt: '2025-10-21',
        updatedAt: '2025-10-22',
        status: 'completed',
        qualityScore: 65,
        complexity: 'High',
        defects: 12,
        effortEstimate: '15 weeks',
        comments: 'Multiple ambiguities and contradictions need resolution'
      }
    ];

    setDocuments(mockDocuments);

    // Calculate stats - focused on analyst's own work
    const completedDocs = mockDocuments.filter(d => d.status === 'completed').length;
    const avgQualityScore = Math.round(mockDocuments.reduce((sum, doc) => sum + doc.qualityScore, 0) / mockDocuments.length);
    const totalDefects = mockDocuments.reduce((sum, doc) => sum + doc.defects, 0);

    setStats({
      totalDocuments: mockDocuments.length,
      analyzedDocuments: completedDocs,
      avgQualityScore: avgQualityScore,
      totalDefects: totalDefects,
      myProjects: mockDocuments.length,
      completedProjects: completedDocs,
      inProgressProjects: mockDocuments.length - completedDocs
    });
  }, []);

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'bg-[var(--success-light)] text-[var(--success-hover)]';
      case 'in-progress': return 'bg-[var(--info-light)] text-[var(--primary-main)]';
      case 'failed': return 'bg-[var(--error-light)] text-[var(--error-hover)]';
      default: return 'bg-[var(--surface-bg)] text-[var(--neutral-700)]';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'in-progress': return <Clock className="w-4 h-4" />;
      case 'failed': return <AlertTriangle className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">My Workspace</h1>
            <p className="text-[var(--text-secondary)] mt-2">Manage your requirements analysis projects</p>
          </div>

          {/* Stats Cards - Focused on analyst's personal metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <FolderOpen className="w-6 h-6 text-[var(--primary-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">My Projects</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.myProjects}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <DocumentTextIcon className="w-6 h-6 text-[var(--success-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Completed</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.completedProjects}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <Clock className="w-6 h-6 text-[var(--warning-main)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">In Progress</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.inProgressProjects}</p>
                </div>
              </div>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-[var(--surface-bg)] mr-4">
                  <TrendingUp className="w-6 h-6 text-[var(--metric-quality-icon)]" />
                </div>
                <div>
                  <p className="text-sm text-[var(--text-secondary)]">Avg. Quality</p>
                  <p className="text-2xl font-bold text-[var(--text-primary)]">{stats.avgQualityScore}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* My Documents Section - Analyst's personal work */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-8">
            <div className="px-6 py-4 border-b border-[var(--card-border)]">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">My Requirements Documents</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[var(--card-border)]">
                <thead className="bg-[var(--surface-bg)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Document</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Uploaded</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Quality</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Complexity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Defects</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Effort</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Comments</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-[var(--surface-bg)] transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 mr-3 text-[var(--text-secondary)]" />
                          <div>
                            <div className="text-sm font-medium text-[var(--text-primary)]">{doc.title}</div>
                            <div className="text-xs text-[var(--text-secondary)]">Last Updated: {doc.updatedAt || doc.uploadedAt}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        {doc.uploadedAt}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                          {getStatusIcon(doc.status)}
                          <span className="ml-1 capitalize">{doc.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <TrendingUp className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="text-sm font-medium text-[var(--text-primary)]">{doc.qualityScore}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <BarChart3 className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="text-sm font-medium text-[var(--text-primary)]">{doc.complexity || 'Medium'}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <AlertTriangle className="w-4 h-4 mr-1 text-[var(--warning-main)]" />
                          <span className="text-sm text-[var(--text-primary)]">{doc.defects}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-primary)]">
                        {doc.effortEstimate}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                        <button 
                          onClick={() => {
                            setSelectedComment(doc.comments || 'No comments available');
                            setSelectedDocument(doc);
                            setShowCommentModal(true);
                          }}
                          className="flex items-center hover:text-[var(--primary-main)] transition-colors"
                        >
                          <MessageSquare className="w-4 h-4 mr-1 text-[var(--text-secondary)]" />
                          <span className="truncate max-w-[80px]" title={doc.comments || 'No comments'}>{doc.comments || 'None'}</span>
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-3">
                          <Link
                            to={`/analysis-results/${doc.id}`}
                            className="text-[var(--success-main)] hover:text-[var(--success-hover)] flex items-center"
                            title="View Analysis Results"
                          >
                            <BarChart3 className="w-4 h-4 mr-1" />
                            Analysis
                          </Link>
                          <Link
                            to={`/traceability/${doc.id}`}
                            className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] flex items-center"
                            title="Inspect Traceability"
                          >
                            <ClipboardCheck className="w-4 h-4 mr-1" />
                            Trace
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Comment Modal */}
          {showCommentModal && selectedDocument && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-[var(--card-bg)] rounded-xl shadow-lg max-w-md w-full border border-[var(--card-border)]">
                <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">Document Comments</h3>
                  <button 
                    onClick={() => setShowCommentModal(false)}
                    className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="p-6">
                  <div className="mb-4">
                    <h4 className="font-medium text-[var(--text-primary)] mb-1">{selectedDocument.title}</h4>
                    <p className="text-sm text-[var(--text-secondary)]">Uploaded: {selectedDocument.uploadedAt}</p>
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

          {/* Professional Navigation Tabs */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-10">
            <div className="border-b border-[var(--card-border)]">
              <nav className="flex flex-wrap">
                <Link
                  to="/analysis"
                  className="flex-1 min-w-[200px] px-6 py-5 text-center border-r border-[var(--card-border)] hover:bg-[var(--surface-bg)] transition-colors"
                >
                  <div className="flex flex-col items-center">
                    <DocumentTextIcon className="w-8 h-8 text-[var(--primary-main)] mb-3" />
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">New Analysis</h3>
                    <p className="text-sm text-[var(--text-secondary)]">Upload requirements document</p>
                  </div>
                </Link>
                <Link
                  to="/analysis-results"
                  className="flex-1 min-w-[200px] px-6 py-5 text-center border-r border-[var(--card-border)] hover:bg-[var(--surface-bg)] transition-colors"
                >
                  <div className="flex flex-col items-center">
                    <BarChart3 className="w-8 h-8 text-[var(--success-main)] mb-3" />
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">My Performance</h3>
                    <p className="text-sm text-[var(--text-secondary)]">View analysis metrics</p>
                  </div>
                </Link>
                <Link
                  to="/traceability"
                  className="flex-1 min-w-[200px] px-6 py-5 text-center hover:bg-[var(--surface-bg)] transition-colors"
                >
                  <div className="flex flex-col items-center">
                    <ClipboardCheck className="w-8 h-8 text-[var(--primary-main)] mb-3" />
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">Traceability</h3>
                    <p className="text-sm text-[var(--text-secondary)]">Manage requirements links</p>
                  </div>
                </Link>
              </nav>
            </div>
          </div>

          {/* Spacer between table and prediction card */}
          <div className="h-10"></div>

          {/* Prediction Analysis Card */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-12">
            <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
              <h2 className="text-lg font-semibold text-[var(--text-primary)]">Prediction Analysis</h2>
              <button 
                onClick={() => {
                  // Show success message when export is clicked
                  toast.success('PDF exported successfully!', {
                    duration: 3000,
                    position: 'top-right'
                  });
                }}
                className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] hover:text-white transition-all duration-200 hover:shadow-lg hover:scale-[1.02]"
              >
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
                        stroke={getScoreColor(85)} 
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

          {/* Differentiation Notice */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <ClipboardCheck className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-blue-900 text-sm">Analyst Workspace</h4>
                <p className="text-xs text-blue-700 mt-1">
                  This dashboard shows YOUR personal projects and analysis results.
                  For organization-wide oversight, contact your supervisor.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Report Modal */}
      {showReportModal && reportDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-[var(--card-border)]">
            <div className="px-6 py-4 border-b border-[var(--card-border)] flex justify-between items-center">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Report: {reportDocument.title}</h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="bg-[var(--surface-bg)] p-4 rounded-lg">
                  <h4 className="font-medium text-[var(--text-primary)] mb-2">Document Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Uploaded:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.uploadedAt}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Status:</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        reportDocument.status === 'completed' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                        reportDocument.status === 'in-progress' ? 'bg-[var(--info-light)] text-[var(--primary-main)]' :
                        'bg-[var(--error-light)] text-[var(--error-hover)]'
                      }`}>
                        {reportDocument.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Quality Score:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.qualityScore}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Defects:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.defects}</span>
                    </div>
                  </div>
                </div>
                <div className="bg-[var(--surface-bg)] p-4 rounded-lg">
                  <h4 className="font-medium text-[var(--text-primary)] mb-2">Analysis Summary</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Complexity:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.complexity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Effort Estimate:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.effortEstimate}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Comments:</span>
                      <span className="text-[var(--text-primary)]">{reportDocument.comments}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-medium text-[var(--text-primary)] mb-3">Requirements Analysis</h4>
                <div className="space-y-3">
                  <div className="flex items-center p-3 bg-[var(--content-bg)] rounded-lg border border-[var(--card-border)]">
                    <Check className="w-4 h-4 text-[var(--success-main)] mr-3" />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">Valid Requirements</p>
                      <p className="text-xs text-[var(--text-secondary)]">All requirements properly defined and unambiguous</p>
                    </div>
                  </div>
                  <div className="flex items-center p-3 bg-[var(--content-bg)] rounded-lg border border-[var(--card-border)]">
                    <AlertCircle className="w-4 h-4 text-[var(--warning-main)] mr-3" />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">Requirements with Issues</p>
                      <p className="text-xs text-[var(--text-secondary)]">Some requirements need clarification</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowReportModal(false)}
                  className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--surface-bg)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    toast.success('Report exported successfully!');
                    setShowReportModal(false);
                  }}
                  className="px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export Report
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalystDashboard;