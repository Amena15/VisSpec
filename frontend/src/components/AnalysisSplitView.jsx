import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, Eye, DocumentText, AlertCircle, Check } from 'lucide-react';

const AnalysisSplitView = () => {
  const [activeTab, setActiveTab] = useState('ambiguities');

  // Mock data for demonstration
  const documentContent = `Software Requirements Specification (SRS) for User Authentication System

1. Introduction
The system shall provide secure user authentication.

2. Functional Requirements
REQ-001: The system shall allow users to register with a unique username and password.
REQ-002: The system shall authenticate users using their credentials.
REQ-003: The system shall lock accounts after 3 failed login attempts.
REQ-004: The system shall send a notification to users when their account is locked.
REQ-005: The system shall unlock accounts after 30 minutes automatically.`;

  const findings = {
    ambiguities: [
      {
        id: 1,
        title: "Ambiguous Term: 'Secure'",
        description: "Requirement REQ-001 uses the term 'secure' without defining security standards",
        severity: "medium",
        location: "Line 5",
        suggestion: "Define specific security standards (e.g., encryption protocols, password complexity)"
      },
      {
        id: 2,
        title: "Vague Timeframe",
        description: "Requirement REQ-005 specifies '30 minutes' without justification",
        severity: "low",
        location: "Line 9",
        suggestion: "Provide rationale for the chosen timeframe or make it configurable"
      }
    ],
    inconsistencies: [
      {
        id: 1,
        title: "Missing Notification Detail",
        description: "REQ-004 mentions notifications but doesn't specify delivery method",
        severity: "high",
        location: "Line 8",
        suggestion: "Specify whether notification is via email, SMS, or in-app message"
      }
    ],
    risks: [
      {
        id: 1,
        title: "Account Lockout Vulnerability",
        description: "Automatic unlock after fixed time may be exploited by attackers",
        severity: "high",
        location: "REQ-005",
        suggestion: "Implement exponential backoff or manual unlock requirement"
      }
    ]
  };

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'high': return 'bg-[var(--error-light)] text-[var(--error-hover)] border-[var(--error-light)]';
      case 'medium': return 'bg-[var(--warning-light)] text-[var(--warning-hover)] border-[var(--warning-light)]';
      case 'low': return 'bg-[var(--info-light)] text-[var(--primary-main)] border-[var(--info-light)]';
      default: return 'bg-[var(--surface-bg)] text-[var(--neutral-700)] border-[var(--card-border)]';
    }
  };

  const getSeverityIcon = (severity) => {
    switch(severity) {
      case 'high': return <AlertCircle className="h-4 w-4 text-[var(--error-main)]" />;
      case 'medium': return <AlertTriangle className="h-4 w-4 text-[var(--warning-main)]" />;
      case 'low': return <Check className="h-4 w-4 text-[var(--primary-main)]" />;
      default: return <AlertCircle className="h-4 w-4 text-[var(--neutral-500)]" />;
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col bg-[var(--content-bg)] rounded-xl border border-[var(--card-border)] overflow-hidden">
      <div className="flex border-b border-[var(--card-border)] bg-[var(--card-bg)]">
        <button
          className={`flex-1 py-4 px-6 text-sm font-medium ${
            activeTab === 'ambiguities'
              ? 'text-[var(--primary-main)] border-b-2 border-[var(--primary-main)]'
              : 'text-[var(--neutral-500)] hover:text-[var(--primary-main)]'
          }`}
          onClick={() => setActiveTab('ambiguities')}
        >
          <div className="flex items-center justify-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Ambiguities</span>
            <span className="ml-2 bg-[var(--primary-50)] text-[var(--primary-main)] text-xs px-2 py-1 rounded-full">
              {findings.ambiguities.length}
            </span>
          </div>
        </button>
        <button
          className={`flex-1 py-4 px-6 text-sm font-medium ${
            activeTab === 'inconsistencies'
              ? 'text-[var(--primary-main)] border-b-2 border-[var(--primary-main)]'
              : 'text-[var(--neutral-500)] hover:text-[var(--primary-main)]'
          }`}
          onClick={() => setActiveTab('inconsistencies')}
        >
          <div className="flex items-center justify-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Inconsistencies</span>
            <span className="ml-2 bg-[var(--primary-50)] text-[var(--primary-main)] text-xs px-2 py-1 rounded-full">
              {findings.inconsistencies.length}
            </span>
          </div>
        </button>
        <button
          className={`flex-1 py-4 px-6 text-sm font-medium ${
            activeTab === 'risks'
              ? 'text-[var(--primary-main)] border-b-2 border-[var(--primary-main)]'
              : 'text-[var(--neutral-500)] hover:text-[var(--primary-main)]'
          }`}
          onClick={() => setActiveTab('risks')}
        >
          <div className="flex items-center justify-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Risks</span>
            <span className="ml-2 bg-[var(--primary-50)] text-[var(--primary-main)] text-xs px-2 py-1 rounded-full">
              {findings.risks.length}
            </span>
          </div>
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Original Document Panel */}
        <div className="w-1/2 border-r border-[var(--card-border)] bg-[var(--card-bg)] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center text-sm text-[var(--neutral-500)] mb-4">
              <DocumentText className="h-4 w-4 mr-2" />
              <span>Original Requirements Document</span>
            </div>
            <div className="bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-[var(--neutral-900)] font-mono">
                {documentContent}
              </pre>
            </div>
          </div>
        </div>

        {/* AI Findings Panel */}
        <div className="w-1/2 bg-[var(--card-bg)] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center text-sm text-[var(--neutral-500)] mb-4">
              <Eye className="h-4 w-4 mr-2" />
              <span>AI Analysis Findings</span>
            </div>
            <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto">
              {findings[activeTab].map((finding) => (
                <div key={finding.id} className="border border-[var(--card-border)] rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {getSeverityIcon(finding.severity)}
                        <h4 className="text-sm font-medium text-[var(--neutral-800)]">{finding.title}</h4>
                        <span className={`text-xs px-2 py-1 rounded-full border ${getSeverityColor(finding.severity)}`}>
                          {finding.severity.toUpperCase()}
                        </span>
                        <span className="text-xs text-[var(--neutral-500)] bg-[var(--surface-bg)] px-2 py-1 rounded">
                          {finding.location}
                        </span>
                      </div>
                      <p className="text-sm text-[var(--neutral-600)] mb-2">{finding.description}</p>
                      <div className="mt-3">
                        <p className="text-xs font-medium text-[var(--primary-main)] mb-1">Suggestion:</p>
                        <p className="text-xs text-[var(--neutral-500)] bg-[var(--surface-bg)] p-2 rounded border border-[var(--card-border)]">
                          {finding.suggestion}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {findings[activeTab].length === 0 && (
                <div className="text-center py-12">
                  <CheckCircle className="h-12 w-12 text-[var(--success-hover)] mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-[var(--neutral-800)] mb-2">No Issues Found</h3>
                  <p className="text-sm text-[var(--neutral-500)]">
                    The AI analysis found no {activeTab} in the document.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisSplitView;