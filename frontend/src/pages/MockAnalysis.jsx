import React, { useState } from 'react';
import { ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock, Eye, Download, AlertCircle, ArrowRight, ArrowDown, AlertOctagon } from 'lucide-react';
import { Link } from 'react-router-dom';

const MockAnalysis = () => {
  const [activeTab, setActiveTab] = useState('findings');
  const [selectedFinding, setSelectedFinding] = useState(null);

  // Mock analysis data
  const documentInfo = {
    name: 'Sample_SRS_Document.pdf',
    size: '2.4 MB',
    uploaded: '2023-11-15',
    status: 'analyzed'
  };

  const findings = [
    {
      id: 1,
      type: 'ambiguity',
      title: 'Ambiguous Term: "Secure"',
      description: 'The term "secure" in requirement 3 is ambiguous and lacks specific security standards.',
      suggestion: 'Define specific security standards (e.g., encryption protocols, password complexity)',
      requirementId: 'REQ-003',
      severity: 'high'
    },
    {
      id: 2,
      type: 'ambiguity',
      title: 'Vague Performance Requirement',
      description: 'The performance requirement in requirement 4 uses "within 2 seconds" without specifying conditions.',
      suggestion: 'Specify under what conditions the 2-second response time applies',
      requirementId: 'REQ-004',
      severity: 'medium'
    },
    {
      id: 3,
      type: 'conflict',
      title: 'Contradictory Requirements',
      description: 'Requirement 6 mentions notifications for account lock, but requirement 7 doesn\'t specify notification for lockout.',
      suggestion: 'Clarify if notifications should be sent for all account lockouts',
      requirementId: 'REQ-006',
      severity: 'high'
    }
  ];

  const requirements = [
    {
      id: 1,
      text: "The system shall allow users to register with a unique username and password.",
      category: "functional",
      status: "valid"
    },
    {
      id: 2,
      text: "The system shall authenticate users using their credentials.",
      category: "functional",
      status: "valid"
    },
    {
      id: 3,
      text: "The system shall provide secure access to user data.",
      category: "security",
      status: "ambiguous",
      findingId: 1
    },
    {
      id: 4,
      text: "The system shall respond to user requests within 2 seconds.",
      category: "performance",
      status: "ambiguous",
      findingId: 2
    },
    {
      id: 5,
      text: "The system shall store user information in a database.",
      category: "data",
      status: "valid"
    },
    {
      id: 6,
      text: "The system shall send notifications to users when their account is locked.",
      category: "notification",
      status: "conflict",
      findingId: 3
    },
    {
      id: 7,
      text: "The system shall lock accounts after 3 failed login attempts.",
      category: "security",
      status: "conflict",
      findingId: 3
    }
  ];

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'high': return 'border-l-[var(--error-main)] bg-[var(--error-light)]';
      case 'medium': return 'border-l-[var(--warning-main)] bg-[var(--warning-light)]';
      case 'low': return 'border-l-[var(--primary-main)] bg-[var(--primary-50)]';
      default: return 'border-l-[var(--card-border)] bg-[var(--content-bg)]';
    }
  };


  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <Link to="/analysis" className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] mr-4">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-[var(--neutral-800)]">Document Analysis</h1>
                <p className="text-[var(--neutral-500)]">{documentInfo.name} • {documentInfo.size}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button className="flex items-center px-4 py-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg text-[var(--primary-main)] hover:bg-[var(--surface-bg)] transition-colors">
                <Download className="h-4 w-4 mr-2" />
                Export Report
              </button>
            </div>
          </div>

          {/* Document Info Card */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-[var(--primary-50)] p-3 rounded-lg mr-4">
                  <FileText className="h-6 w-6 text-[var(--primary-main)]" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[var(--neutral-800)]">{documentInfo.name}</h2>
                  <p className="text-sm text-[var(--neutral-500)]">Uploaded: {new Date(documentInfo.uploaded).toLocaleDateString()}</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  documentInfo.status === 'analyzed' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                  documentInfo.status === 'pending' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                  'bg-[var(--info-light)] text-[var(--info-dark)]'
                }`}>
                  {documentInfo.status.charAt(0).toUpperCase() + documentInfo.status.slice(1)}
                </span>
                <span className="text-sm text-[var(--neutral-500)]">Completed</span>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm overflow-hidden">
            <div className="border-b border-[var(--card-border)]">
              <nav className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('findings')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'findings'
                      ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                      : 'border-transparent text-[var(--neutral-500)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
                  }`}
                >
                  Analysis Findings
                </button>
                <button
                  onClick={() => setActiveTab('requirements')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'requirements'
                      ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                      : 'border-transparent text-[var(--neutral-500)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
                  }`}
                >
                  Requirements
                </button>
                <button
                  onClick={() => setActiveTab('visualization')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'visualization'
                      ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                      : 'border-transparent text-[var(--neutral-500)] hover:text-[var(--primary-main)] hover:border-[var(--card-border)]'
                  }`}
                >
                  Visualization
                </button>
              </nav>
            </div>

            <div className="p-6">
              {/* Findings Tab */}
              {activeTab === 'findings' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-[var(--neutral-800)] mb-4">Detected Issues</h3>
                  {findings.map((finding) => (
                    <div
                      key={finding.id}
                      className={`border-l-4 ${
                        finding.severity === 'high' ? 'border-[var(--error-main)]' :
                        finding.severity === 'medium' ? 'border-[var(--warning-main)]' :
                        'border-[var(--primary-main)]'
                      } bg-[var(--card-bg)] shadow-sm rounded-r-lg p-4 hover:shadow-md transition-shadow cursor-pointer ${
                        selectedFinding === finding.id ? 'ring-2 ring-[var(--primary-main)] ring-opacity-50' : ''
                      }`}
                      onClick={() => setSelectedFinding(selectedFinding === finding.id ? null : finding.id)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex items-start">
                          <div className="mr-4 mt-1">
                            {finding.type === 'ambiguity' ? (
                              <AlertTriangle className="h-5 w-5 text-[var(--warning-main)]" />
                            ) : (
                              <AlertTriangle className="h-5 w-5 text-[var(--error-main)]" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                finding.type === 'ambiguity'
                                  ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]'
                                  : 'bg-[var(--error-light)] text-[var(--error-hover)]'
                              }`}>
                                {finding.type === 'ambiguity' ? <AlertTriangle className="h-3 w-3 mr-1" /> : <AlertOctagon className="h-3 w-3 mr-1" />}
                                {finding.type.charAt(0).toUpperCase() + finding.type.slice(1)}
                              </span>
                              <span className="text-xs text-[var(--neutral-500)]">{finding.requirementId}</span>
                            </div>
                            <h4 className="text-lg font-medium text-[var(--neutral-800)]">{finding.title}</h4>
                            <p className="text-[var(--neutral-500)] mt-2">{finding.description}</p>
                            <div className="mt-3 p-3 bg-[var(--surface-bg)] rounded border border-[var(--card-border)]">
                              <p className="text-sm font-medium text-[var(--primary-main)]">Suggested Fix:</p>
                              <p className="text-sm text-[var(--neutral-500)] mt-1">{finding.suggestion}</p>
                              <div className="mt-3 flex space-x-2">
                                <button className="text-xs bg-[var(--primary-main)] text-white px-3 py-1 rounded hover:bg-[var(--primary-hover)] transition-colors flex items-center">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Apply Suggestion
                                </button>
                                <button className="text-xs border border-[var(--card-border)] text-[var(--primary-main)] px-3 py-1 rounded hover:bg-[var(--surface-bg)] transition-colors">
                                  Ignore
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                        <button className="text-[var(--primary-main)] hover:text-[var(--primary-hover)]">
                          <Eye className="h-5 w-5" />
                        </button>
                      </div>

                      {selectedFinding === finding.id && (
                        <div className="mt-4 pt-4 border-t border-[var(--card-border)]">
                          <h5 className="font-medium text-[var(--neutral-800)] mb-2">Related Requirements:</h5>
                          <div className="space-y-2">
                            {requirements.filter(req => req.findingId === finding.id).map(req => (
                              <div key={req.id} className="bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                                <div className="flex justify-between">
                                  <span className="font-medium">Requirement {req.id}</span>
                                  <span className={`text-xs px-2 py-1 rounded-full ${
                                    req.status === 'ambiguous' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                                    req.status === 'conflict' ? 'bg-[var(--error-light)] text-[var(--error-hover)]' :
                                    'bg-[var(--success-light)] text-[var(--success-hover)]'
                                  }`}>
                                    {req.status}
                                  </span>
                                </div>
                                <p className="text-sm text-[var(--neutral-500)] mt-1">{req.text}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Requirements Tab */}
              {activeTab === 'requirements' && (
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-[var(--neutral-800)] mb-4">Requirements Analysis</h3>
                  {requirements.map((req) => (
                    <div
                      key={req.id}
                      className={`bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 hover:shadow-md transition-shadow ${
                        req.status !== 'valid' ? 'border-l-4 border-l-[var(--error-main)]' : ''
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-sm font-medium text-[var(--neutral-800)]">REQ-{req.id.toString().padStart(3, '0')}</span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              req.status === 'ambiguous' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                              req.status === 'conflict' ? 'bg-[var(--error-light)] text-[var(--error-hover)]' :
                              'bg-[var(--success-light)] text-[var(--success-hover)]'
                            }`}>
                              {req.status}
                            </span>
                            <span className="text-xs text-[var(--neutral-500)] bg-[var(--surface-bg)] px-2 py-1 rounded">
                              {req.category}
                            </span>
                          </div>
                          <p className="text-[var(--neutral-800)]">{req.text}</p>
                        </div>
                        {req.status !== 'valid' && (
                          <button className="text-[var(--primary-main)] hover:text-[var(--primary-hover)]">
                            <AlertTriangle className="h-5 w-5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Visualization Tab */}
              {activeTab === 'visualization' && (
                <div className="text-center py-12">
                  <div className="mx-auto bg-[var(--primary-50)] w-16 h-16 rounded-full flex items-center justify-center mb-4">
                    <Eye className="h-8 w-8 text-[var(--primary-main)]" />
                  </div>
                  <h3 className="text-lg font-medium text-[var(--neutral-800)] mb-2">UML Diagram Preview</h3>
                  <p className="text-[var(--neutral-500)] mb-6">Generated visualization of your requirements</p>

                  <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-xl p-8 max-w-4xl mx-auto">
                    <div className="bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg p-6">
                      <div className="flex justify-center space-x-8 mb-8">
                        <div className="text-center">
                          <div className="bg-[var(--card-bg)] border-2 border-[var(--primary-main)] rounded-lg p-4 w-32">
                            <div className="font-semibold text-[var(--neutral-800)] text-sm">User</div>
                            <div className="text-xs text-[var(--neutral-500)] mt-2">+login(): boolean</div>
                            <div className="text-xs text-[var(--neutral-500)]">-validate(): boolean</div>
                          </div>
                        </div>

                        <div className="text-center">
                          <div className="bg-[var(--card-bg)] border-2 border-[var(--success-main)] rounded-lg p-4 w-32">
                            <div className="font-semibold text-[var(--neutral-800)] text-sm">Auth Service</div>
                            <div className="text-xs text-[var(--neutral-500)] mt-2">+verify(): boolean</div>
                            <div className="text-xs text-[var(--neutral-500)]">-hash(): string</div>
                          </div>
                        </div>

                        <div className="text-center">
                          <div className="bg-[var(--card-bg)] border-2 border-[var(--warning-main)] rounded-lg p-4 w-32">
                            <div className="font-semibold text-[var(--neutral-800)] text-sm">Database</div>
                            <div className="text-xs text-[var(--neutral-500)] mt-2">+query(): result</div>
                            <div className="text-xs text-[var(--neutral-500)]">-connect(): boolean</div>
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-center">
                        <div className="h-0.5 w-full bg-[var(--card-border)] relative">
                          <div className="absolute left-1/4 transform -translate-x-1/2 top-0.5">
                            <div className="bg-[var(--primary-main)] text-white text-xs px-2 py-1 rounded">authenticate()</div>
                          </div>
                          <div className="absolute left-3/4 transform -translate-x-1/2 top-0.5">
                            <div className="bg-[var(--primary-main)] text-white text-xs px-2 py-1 rounded">store()</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => window.location.href = '/visualization'}
                    className="mt-6 bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
                  >
                    Start Analysis
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MockAnalysis;