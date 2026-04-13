import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  Download,
  TrendingUp,
  XCircle,
  AlertOctagon,
  BarChart3,
  ClipboardCheck
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { handleReviewClick } from '../utils/reviewHandler';
import { toast } from 'sonner';

const AnalysisResults = () => {
  const { id } = useParams(); // Get document ID from URL
  const [activeTab, setActiveTab] = useState('findings'); // Default to findings tab
  const [expandedFinding, setExpandedFinding] = useState(null); // Track which finding is expanded

  // Log the ID when the component loads (for debugging)
  React.useEffect(() => {
    console.log(`Analysis results page loaded for ID: ${id}`);
  }, [id]);
  
  // Mock document info
  const documentInfo = {
    id: 1,
    name: 'Student Registration System Requirements.pdf',
    size: '2.4 MB',
    uploaded: '2025-10-24',
    status: 'completed',
    qualityScore: 78,
    defectCount: 5,
    estimatedEffort: '12 weeks',
    author: 'John Doe',
    lastModified: '2025-10-25'
  };

  // Mock findings data
  const findings = [
    {
      id: 1,
      title: 'Ambiguous Term Identified',
      description: 'The term "secure access" in requirement 3 is ambiguous and lacks specific security standards.',
      severity: 'high',
      confidence: 0.85,
      requirementId: 'REQ-003'
    },
    {
      id: 2,
      title: 'Missing Validation Rule',
      description: 'Requirement 7 lacks specific validation rules for user input fields.',
      severity: 'medium',
      confidence: 0.72,
      requirementId: 'REQ-007'
    },
    {
      id: 3,
      title: 'Performance Concern',
      description: 'Requirement 4 specifies response time without defining conditions.',
      severity: 'medium',
      confidence: 0.68,
      requirementId: 'REQ-004'
    },
    {
      id: 4,
      title: 'Inconsistent Terminology',
      description: 'Multiple terms used for same concept: "user", "customer", "client".',
      severity: 'low',
      confidence: 0.91,
      requirementId: 'VARIOUS'
    }
  ];

  // Mock requirements data
  const requirements = [
    {
      id: 1,
      text: "The system shall allow users to register with a unique username and password.",
      category: "functional",
      status: "valid",
      originalText: "The system shall allow users to register with a unique username and password."
    },
    {
      id: 2,
      text: "The system shall authenticate users using their credentials.",
      category: "functional",
      status: "valid",
      originalText: "The system shall authenticate users using their credentials."
    },
    {
      id: 3,
      text: "The system shall provide secure access to user data.",
      category: "security",
      status: "ambiguous",
      findingId: 1,
      originalText: "The system shall provide secure access to user data."
    },
    {
      id: 4,
      text: "The system shall respond to user requests within 2 seconds.",
      category: "performance",
      status: "ambiguous",
      findingId: 2,
      originalText: "The system shall respond to user requests within 2 seconds."
    },
    {
      id: 5,
      text: "The system shall store user information in a database.",
      category: "data",
      status: "valid",
      originalText: "The system shall store user information in a database."
    }
  ];

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with Professional Navigation */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Link to="/documents" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] mr-4">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">Analysis Results</h1>
                <p className="text-[var(--text-secondary)]">{documentInfo.name} • {documentInfo.size}</p>
              </div>
            </div>
            <button className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </button>
          </div>
        </div>

        {/* Document Info Card */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                <FileText className="h-6 w-6 text-[var(--text-secondary)]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">{documentInfo.name}</h2>
                <div className="flex items-center text-sm text-[var(--text-secondary)] mt-1">
                  <span>Size: {documentInfo.size}</span>
                  <span className="mx-2">•</span>
                  <span>Uploaded: {new Date(documentInfo.uploaded).toLocaleDateString()}</span>
                  <span className="mx-2">•</span>
                  <span>Author: {documentInfo.author || 'Unknown'}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="text-center">
                <div className="flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-[var(--text-secondary)] mr-1" />
                  <span className="text-2xl font-bold text-[var(--text-primary)]">{documentInfo.qualityScore}%</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)]">Quality Score</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-1" />
                  <span className="text-2xl font-bold text-[var(--text-primary)]">{documentInfo.defectCount}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)]">Defects Found</p>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center">
                  <Clock className="h-5 w-5 text-[var(--text-secondary)] mr-1" />
                  <span className="text-2xl font-bold text-[var(--text-primary)]">{documentInfo.estimatedEffort}</span>
                </div>
                <p className="text-xs text-[var(--text-secondary)]">Est. Effort</p>
              </div>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                documentInfo.status === 'completed' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                documentInfo.status === 'in-progress' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                'bg-[var(--error-light)] text-[var(--error-hover)]'
              }`}>
                {documentInfo.status === 'completed' ? <CheckCircle className="h-4 w-4 mr-1" /> :
                 documentInfo.status === 'in-progress' ? <Clock className="h-4 w-4 mr-1" /> :
                 <XCircle className="h-4 w-4 mr-1" />}
                <span className="capitalize">{documentInfo.status}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-6">
          <div className="border-b border-[var(--card-border)]">
            <nav className="flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('findings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'findings'
                    ? 'border-[var(--primary-main)] text-[var(--text-primary)]'
                    : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                }`}
              >
                Analysis Findings
              </button>
              <button
                onClick={() => setActiveTab('requirements')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'requirements'
                    ? 'border-[var(--primary-main)] text-[var(--text-primary)]'
                    : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                }`}
              >
                Requirements
              </button>
              <Link
                to={`/traceability/${id}`}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'traceability'
                    ? 'border-[var(--primary-main)] text-[var(--text-primary)]'
                    : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                }`}
              >
                Traceability
              </Link>
              <Link
                to={`/visualization/${id}`}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'visualization'
                    ? 'border-[var(--primary-main)] text-[var(--text-primary)]'
                    : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                }`}
              >
                Visualization
              </Link>
            </nav>
          </div>
        </div>

        {/* Content based on active tab */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden">
          <div className="p-6">
            {activeTab === 'findings' && (
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Analysis Findings</h3>
                <div className="space-y-4">
                  {findings.map((finding) => (
                    <div 
                      key={finding.id} 
                      className={`border-l-4 p-4 rounded-r ${
                        finding.severity === 'high' ? 'border-[var(--error-main)] bg-[var(--error-light)]/20' :
                        finding.severity === 'medium' ? 'border-[var(--warning-main)] bg-[var(--warning-light)]/20' :
                        'border-[var(--success-main)] bg-[var(--success-light)]/20'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium text-[var(--text-primary)]">{finding.title}</h4>
                          <p className="text-[var(--text-secondary)] mt-1">{finding.description}</p>
                          <div className="mt-2 flex items-center text-sm">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                              finding.severity === 'high' ? 'bg-[var(--error-light)] text-[var(--error-main)]' :
                              finding.severity === 'medium' ? 'bg-[var(--warning-light)] text-[var(--warning-main)]' :
                              'bg-[var(--success-light)] text-[var(--success-main)]'
                            }`}>
                              {finding.severity === 'high' ? <AlertOctagon className="h-3 w-3 mr-1" /> :
                               finding.severity === 'medium' ? <AlertTriangle className="h-3 w-3 mr-1" /> :
                               <CheckCircle className="h-3 w-3 mr-1" />}
                              {finding.severity}
                            </span>
                            <span className="mx-2">•</span>
                            <span>Confidence: {(finding.confidence * 100).toFixed(0)}%</span>
                            <span className="mx-2">•</span>
                            <span>Requirement: {finding.requirementId}</span>
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            setExpandedFinding(expandedFinding === finding.id ? null : finding.id);
                          }}
                          className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors"
                        >
                          <Eye className="h-5 w-5" />
                        </button>
                      </div>
                      
                      {/* Expanded view for finding details */}
                      {expandedFinding === finding.id && (
                        <div className="mt-4 pt-4 border-t border-[var(--card-border)]">
                          <div className="bg-[var(--surface-bg)] p-4 rounded-lg">
                            <h5 className="font-medium text-[var(--text-primary)] mb-2">Details</h5>
                            <p className="text-sm text-[var(--text-secondary)] mb-3">{finding.description}</p>
                            
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="font-medium text-[var(--text-secondary)]">Severity:</span>
                                <span className="ml-2">{finding.severity}</span>
                              </div>
                              <div>
                                <span className="font-medium text-[var(--text-secondary)]">Confidence:</span>
                                <span className="ml-2">{(finding.confidence * 100).toFixed(0)}%</span>
                              </div>
                              <div>
                                <span className="font-medium text-[var(--text-secondary)]">Requirement:</span>
                                <span className="ml-2">{finding.requirementId}</span>
                              </div>
                              <div>
                                <span className="font-medium text-[var(--text-secondary)]">Type:</span>
                                <span className="ml-2 capitalize">{finding.title.toLowerCase().includes('ambiguity') ? 'Ambiguity' : 
                                  finding.title.toLowerCase().includes('contradiction') ? 'Contradiction' : 
                                  finding.title.toLowerCase().includes('conflict') ? 'Conflict' : 'Other'}</span>
                              </div>
                            </div>
                            
                            <div className="mt-3">
                              <span className="font-medium text-[var(--text-secondary)]">Suggestion:</span>
                              <p className="text-sm text-[var(--text-primary)] mt-1">
                                {finding.title.includes('Ambiguous') ? 'Consider defining specific security standards or protocols to eliminate ambiguity.' :
                                 finding.title.includes('Missing') ? 'Add the missing validation rules to ensure data integrity.' :
                                 finding.title.includes('Performance') ? 'Specify the conditions under which the performance requirement applies.' :
                                 finding.title.includes('Inconsistent') ? 'Standardize terminology to use a single term for the same concept throughout the document.' :
                                 'Review and clarify this requirement to improve its precision and testability.'}
                              </p>
                            </div>
                            
                            <div className="mt-4 flex space-x-3">
                              <button
                                onClick={() => {
                                  toast.success('Suggestion applied successfully!');
                                  setExpandedFinding(null);
                                }}
                                className="px-3 py-1.5 bg-[var(--success-main)] text-white rounded-lg hover:bg-[var(--success-hover)] transition-colors text-sm"
                              >
                                Apply
                              </button>
                              <button
                                onClick={() => {
                                  toast.info('Finding ignored');
                                  setExpandedFinding(null);
                                }}
                                className="px-3 py-1.5 bg-[var(--surface-bg)] text-[var(--text-primary)] rounded-lg hover:bg-[var(--card-border)] transition-colors text-sm"
                              >
                                Ignore
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {activeTab === 'requirements' && (
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Requirements Analysis</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-[var(--card-border)]">
                    <thead className="bg-[var(--surface-bg)]">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Requirement</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Category</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                      {requirements.map((req) => (
                        <tr key={req.id} className="hover:bg-[var(--surface-bg)] transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--text-primary)]">
                            REQ-{req.id.toString().padStart(3, '0')}
                          </td>
                          <td className="px-6 py-4 text-sm text-[var(--text-primary)] max-w-md">
                            {req.text}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-[var(--surface-bg)] text-[var(--text-secondary)]">
                              {req.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              req.status === 'valid' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                              req.status === 'ambiguous' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                              'bg-[var(--error-light)] text-[var(--error-hover)]'
                            }`}>
                              {req.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] transition-colors">
                              <Eye className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults;