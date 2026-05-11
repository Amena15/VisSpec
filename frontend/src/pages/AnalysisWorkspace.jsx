import React, { useState } from 'react';
import { AlertTriangle, AlertOctagon, CheckCircle, FileText, Download } from 'lucide-react';

const AnalysisWorkspace = () => {
  const [selectedIssue, setSelectedIssue] = useState(null);

  // Function to get issue color based on type
  const getIssueColor = (type) => {
    switch(type) {
      case 'ambiguity':
        return 'border-l-[var(--warning-main)]'; // amber
      case 'conflict':
        return 'border-l-[var(--error-main)]'; // red
      default:
        return 'border-l-[var(--primary-main)]'; // indigo
    }
  };

  // Function to get issue badge based on type
  const getIssueBadge = (type) => {
    switch(type) {
      case 'ambiguity':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--warning-light)] text-[var(--warning-hover)]">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Ambiguity
          </span>
        );
      case 'conflict':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--error-light)] text-[var(--error-hover)]">
            <AlertOctagon className="h-3 w-3 mr-1" />
            Conflict
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--primary-50)] text-[var(--primary-hover)]">
            <CheckCircle className="h-3 w-3 mr-1" />
            Suggestion
          </span>
        );
    }
  };

  // Mock data for requirements document
  const requirements = [
    {
      id: 1,
      text: "The system shall allow users to register with a unique username and password.",
      category: "functional"
    },
    {
      id: 2,
      text: "The system shall authenticate users using their credentials.",
      category: "functional"
    },
    {
      id: 3,
      text: "The system shall provide secure access to user data.",
      category: "security",
      issue: "ambiguous"
    },
    {
      id: 4,
      text: "The system shall respond to user requests within 2 seconds.",
      category: "performance",
      issue: "ambiguous"
    },
    {
      id: 5,
      text: "The system shall store user information in a database.",
      category: "data"
    },
    {
      id: 6,
      text: "The system shall send notifications to users when their account is locked.",
      category: "notification",
      issue: "conflict"
    },
    {
      id: 7,
      text: "The system shall lock accounts after 3 failed login attempts.",
      category: "security",
      issue: "conflict"
    }
  ];

  // Mock data for AI findings
  const aiAnalysis = [
    {
      id: 1,
      type: "ambiguity",
      title: "Ambiguous Term: 'Secure'",
      description: "The term 'secure' in requirement 3 is ambiguous and lacks specific security standards.",
      suggestion: "Define specific security standards (e.g., encryption protocols, password complexity)",
      requirementId: 3
    },
    {
      id: 2,
      type: "ambiguity",
      title: "Vague Performance Requirement",
      description: "The performance requirement in requirement 4 uses 'within 2 seconds' without specifying conditions.",
      suggestion: "Specify under what conditions the 2-second response time applies",
      requirementId: 4
    },
    {
      id: 3,
      type: "conflict",
      title: "Contradictory Requirements",
      description: "Requirement 6 mentions notifications for account lock, but requirement 7 doesn't specify notification for lockout.",
      suggestion: "Clarify if notifications should be sent for all account lockouts",
      requirementId: 6
    }
  ];


  const [activeTab, setActiveTab] = useState('findings'); // Added state for active tab

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Analysis Workspace</h1>
            <p className="text-[var(--text-secondary)] mt-1">Compare raw requirements against AI-generated findings</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-6">
        <div className="border-b border-[var(--card-border)]">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('findings')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'findings'
                  ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
              }`}
            >
              Analysis Findings
            </button>
            <button
              onClick={() => setActiveTab('requirements')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'requirements'
                  ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
              }`}
            >
              Requirements
            </button>
            <button
              onClick={() => setActiveTab('report')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'report'
                  ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
              }`}
            >
              Analysis Report
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {activeTab === 'findings' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-200px)]">
            {/* Left Panel: Document Viewer */}
            <div className="bg-[var(--card-bg)] shadow-sm rounded-xl p-8 overflow-y-auto border border-[var(--card-border)]">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Requirements Document</h2>
                <p className="text-sm text-[var(--text-secondary)]">Original SRS document with highlighted issues</p>
              </div>

              <div className="space-y-4">
                {requirements.map((req) => (
                  <div
                    key={req.id}
                    onClick={() => setSelectedIssue(req.issue ? req.id : null)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedIssue === req.id
                        ? 'bg-[var(--warning-light)] border-[var(--warning-main)]'
                        : req.issue
                        ? 'bg-[var(--error-light)]/30 border-[var(--error-light)] hover:bg-[var(--error-light)]/50'
                        : 'bg-[var(--card-bg)] border-[var(--card-border)] hover:bg-[var(--content-bg)]'
                    }`}
                  >
                    <div className="flex items-start">
                      <div className="mr-3 mt-1">
                        <FileText className="h-4 w-4 text-[var(--primary-main)]" />
                      </div>
                      <div>
                        <p className="text-[var(--text-primary)]">{req.text}</p>
                        <div className="mt-2 flex items-center text-xs text-[var(--text-secondary)]">
                          <span className="px-2 py-1 bg-[var(--surface-bg)] rounded mr-2">{req.category}</span>
                          <span>Req #{req.id}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Panel: AI Findings */}
            <div className="bg-[var(--content-bg)] rounded-xl p-6 overflow-y-auto border border-[var(--card-border)]">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">AI Analysis Findings</h2>
                <p className="text-sm text-[var(--text-secondary)]">Issues detected by the AI-powered analysis engine</p>
              </div>

              <div className="space-y-4">
                {aiAnalysis.map((finding) => (
                  <div
                    key={finding.id}
                    className={`bg-[var(--card-bg)] border-l-4 ${getIssueColor(finding.type)} shadow-sm p-4 rounded-lg mb-4 transition-all hover:shadow-md`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          {getIssueBadge(finding.type)}
                        </div>
                        <h3 className="text-lg font-medium text-[var(--text-primary)]">{finding.title}</h3>
                        <p className="text-[var(--text-secondary)] mt-2">{finding.description}</p>
                        <div className="mt-3 p-3 bg-[var(--content-bg)] rounded border border-[var(--card-border)]">
                          <p className="text-sm font-medium text-[var(--primary-main)]">Suggestion:</p>
                          <p className="text-sm text-[var(--text-secondary)] mt-1">{finding.suggestion}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedIssue(finding.requirementId)}
                        className="text-[var(--primary-main)] hover:text-[var(--primary-dark)] text-sm font-medium flex items-center"
                      >
                        <span>View in Document</span>
                        <svg className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}

                {/* Empty state if no findings */}
                {aiAnalysis.length === 0 && (
                  <div className="text-center py-12">
                    <div className="mx-auto h-12 w-12 text-[var(--text-secondary)]">
                      <CheckCircle className="h-12 w-12" />
                    </div>
                    <h3 className="mt-2 text-lg font-medium text-[var(--text-primary)]">No Issues Detected</h3>
                    <p className="mt-1 text-[var(--text-secondary)]">The AI analysis found no ambiguities or conflicts in the document.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'requirements' && (
          <div className="bg-[var(--card-bg)] shadow-sm rounded-xl p-8 border border-[var(--card-border)]">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Requirements Analysis</h2>
              <p className="text-sm text-[var(--text-secondary)]">Detailed breakdown of requirements with status</p>
            </div>

            <div className="space-y-4">
              {requirements.map((req) => (
                <div
                  key={req.id}
                  className={`p-4 rounded-lg border ${
                    req.issue
                      ? 'bg-[var(--error-light)]/30 border-[var(--error-main)]'
                      : 'bg-[var(--card-bg)] border-[var(--card-border)]'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">REQ-{req.id.toString().padStart(3, '0')}</span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          req.issue === 'ambiguous' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                          req.issue === 'conflict' ? 'bg-[var(--error-light)] text-[var(--error-hover)]' :
                          'bg-[var(--success-light)] text-[var(--success-hover)]'
                        }`}>
                          {req.issue || 'valid'}
                        </span>
                        <span className="text-xs text-[var(--text-secondary)] bg-[var(--content-bg)] px-2 py-1 rounded">
                          {req.category}
                        </span>
                      </div>
                      <p className="text-[var(--text-primary)]">{req.text}</p>
                    </div>
                    {req.issue && (
                      <button className="text-[var(--primary-main)] hover:text-[var(--primary-dark)]">
                        <AlertTriangle className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'report' && (
          <div className="bg-[var(--card-bg)] shadow-sm rounded-xl p-8 border border-[var(--card-border)]">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Analysis Report</h2>
              <p className="text-sm text-[var(--text-secondary)]">Comprehensive report of the requirements analysis</p>
            </div>

            <div className="space-y-6">
              <div className="bg-[var(--content-bg)] p-6 rounded-lg border border-[var(--card-border)]">
                <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">Executive Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-[var(--card-bg)] p-4 rounded-lg border border-[var(--card-border)]">
                    <div className="text-2xl font-bold text-[var(--primary-main)]">7</div>
                    <div className="text-sm text-[var(--text-secondary)]">Total Requirements</div>
                  </div>
                  <div className="bg-[var(--card-bg)] p-4 rounded-lg border border-[var(--card-border)]">
                    <div className="text-2xl font-bold text-[var(--warning-main)]">2</div>
                    <div className="text-sm text-[var(--text-secondary)]">Ambiguities Found</div>
                  </div>
                  <div className="bg-[var(--card-bg)] p-4 rounded-lg border border-[var(--card-border)]">
                    <div className="text-2xl font-bold text-[var(--error-main)]">1</div>
                    <div className="text-sm text-[var(--text-secondary)]">Conflicts Found</div>
                  </div>
                </div>
              </div>

              <div className="bg-[var(--content-bg)] p-6 rounded-lg border border-[var(--card-border)]">
                <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">Detailed Findings</h3>
                <div className="space-y-4">
                  {aiAnalysis.map((finding) => (
                    <div key={finding.id} className={`border-l-4 ${getIssueColor(finding.type)} bg-[var(--card-bg)] p-4 rounded-r-lg`}>
                      <div className="flex items-center space-x-2 mb-2">
                        {getIssueBadge(finding.type)}
                      </div>
                      <h4 className="font-medium text-[var(--text-primary)]">{finding.title}</h4>
                      <p className="text-[var(--text-secondary)] mt-2">{finding.description}</p>
                      <div className="mt-3 p-3 bg-[var(--content-bg)] rounded border border-[var(--card-border)]">
                        <p className="text-sm font-medium text-[var(--primary-main)]">Recommendation:</p>
                        <p className="text-sm text-[var(--text-secondary)] mt-1">{finding.suggestion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-[var(--content-bg)] p-6 rounded-lg border border-[var(--card-border)]">
                <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">Quality Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Completeness</span>
                      <span className="font-medium text-[var(--text-primary)]">78%</span>
                    </div>
                    <div className="w-full bg-[var(--card-border)] rounded-full h-2">
                      <div className="bg-[var(--primary-main)] h-2 rounded-full" style={{ width: '78%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Consistency</span>
                      <span className="font-medium text-[var(--text-primary)]">85%</span>
                    </div>
                    <div className="w-full bg-[var(--card-border)] rounded-full h-2">
                      <div className="bg-[var(--success-main)] h-2 rounded-full" style={{ width: '85%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Clarity</span>
                      <span className="font-medium text-[var(--text-primary)]">72%</span>
                    </div>
                    <div className="w-full bg-[var(--card-border)] rounded-full h-2">
                      <div className="bg-[var(--warning-main)] h-2 rounded-full" style={{ width: '72%' }}></div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-secondary)]">Verifiability</span>
                      <span className="font-medium text-[var(--text-primary)]">90%</span>
                    </div>
                    <div className="w-full bg-[var(--card-border)] rounded-full h-2">
                      <div className="bg-[var(--accent-main)] h-2 rounded-full" style={{ width: '90%' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <button className="bg-[var(--primary-main)] text-white px-6 py-3 rounded-lg font-medium hover:bg-[var(--primary-hover)] transition-colors flex items-center">
                  <Download className="h-4 w-4 mr-2" />
                  Export Full Report
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisWorkspace;