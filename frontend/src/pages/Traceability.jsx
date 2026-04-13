import React, { useState, useMemo } from 'react';
import { Search, Filter, Plus, Star, MessageSquare, Clock, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

const Traceability = () => {
  const { id } = useParams(); // Get the ID parameter from the URL
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState(null);

  // Log the ID when the component loads (for debugging)
  React.useEffect(() => {
    if (id) {
      console.log(`Navigated to traceability page for ID: ${id}`);
    }
  }, [id]);

  // Mock traceability data
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
    },
    {
      id: 6,
      text: "The system shall send notifications to users when their account is locked.",
      category: "notification",
      status: "conflict",
      findingId: 3,
      originalText: "The system shall send notifications to users when their account is locked."
    },
    {
      id: 7,
      text: "The system shall lock accounts after 3 failed login attempts.",
      category: "security",
      status: "conflict",
      findingId: 3,
      originalText: "The system shall lock accounts after 3 failed login attempts."
    }
  ];

  const defects = [
    {
      id: 1,
      type: 'ambiguity',
      title: 'Ambiguous Term: "Secure"',
      description: 'The term "secure" in requirement 3 is ambiguous and lacks specific security standards.',
      suggestion: 'Define specific security standards (e.g., encryption protocols, password complexity)',
      requirementId: 'REQ-003',
      severity: 'high',
      confidence: 0.85
    },
    {
      id: 2,
      type: 'ambiguity',
      title: 'Vague Performance Requirement',
      description: 'The performance requirement in requirement 4 uses "within 2 seconds" without specifying conditions.',
      suggestion: 'Specify under what conditions the 2-second response time applies',
      requirementId: 'REQ-004',
      severity: 'medium',
      confidence: 0.78
    },
    {
      id: 3,
      type: 'conflict',
      title: 'Contradictory Requirements',
      description: 'Requirement 6 mentions notifications for account lock, but requirement 7 doesn\'t specify notification for lockout.',
      suggestion: 'Clarify if notifications should be sent for all account lockouts',
      requirementId: 'REQ-006',
      severity: 'high',
      confidence: 0.92
    }
  ];

  const traceabilityData = useMemo(() => {
    return requirements.map((req, index) => ({
      id: req.id || `req-${index + 1}`,
      requirement: req.text || `Requirement ${index + 1}`,
      status: req.status || 'valid',
      visualElement: ['Actor: User', 'Actor: Admin', 'Use Case: UC001', 'Use Case: UC002'][index % 4],
      complexity: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)],
      hasNotes: Math.random() > 0.7,
      notes: req.notes || [],
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toLocaleDateString()
    }));
  }, [requirements]);

  // Filter data based on search and status
  const filteredData = useMemo(() => {
    return traceabilityData.filter(item => {
      const matchesSearch = item.requirement.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.visualElement.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || item.status === filterStatus;
      return matchesSearch && matchesStatus;
    });
  }, [traceabilityData, searchTerm, filterStatus]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'valid': return 'text-[var(--success-hover)] bg-[var(--success-light)]';
      case 'ambiguous': return 'text-[var(--warning-hover)] bg-[var(--warning-light)]';
      case 'conflict': return 'text-[var(--error-hover)] bg-[var(--error-light)]';
      default: return 'text-[var(--neutral-500)] bg-[var(--surface-bg)]';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'valid': return <CheckCircle className="w-4 h-4" />;
      case 'ambiguous': return <AlertTriangle className="w-4 h-4" />;
      case 'conflict': return <AlertOctagon className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const handleAddNote = (requirementId) => {
    const requirement = traceabilityData.find(req => req.id === requirementId);
    setSelectedRequirement(requirement);
    setShowNotesModal(true);
  };

  const handleSaveNote = (noteText) => {
    // In a real app, this would save to the backend
    console.log(`Added note to ${selectedRequirement.id}: ${noteText}`);
    setShowNotesModal(false);
    setSelectedRequirement(null);
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-[var(--text-primary)]">Inspect Requirements Traceability</h1>
                <p className="text-[var(--text-secondary)] mt-2">Track relationships between requirements and visual elements</p>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--neutral-400)] w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search requirements..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)] w-64"
                />
              </div>

              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)]"
              >
                <option value="all">All Statuses</option>
                <option value="valid">Valid</option>
                <option value="ambiguous">Ambiguous</option>
                <option value="conflict">Conflict</option>
              </select>
            </div>

            <Link
              to="/analysis"
              className="inline-flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] hover:text-white transition-all duration-200"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Analysis
            </Link>
          </div>

          {/* Traceability Table */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-[var(--card-border)]">
                <thead className="bg-[var(--surface-bg)]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Requirement</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Visual Element</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Complexity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Notes</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-[var(--card-bg)] divide-y divide-[var(--card-border)]">
                  {filteredData.length > 0 ? (
                    filteredData.map((item, index) => (
                      <tr key={item.id} className="hover:bg-[var(--surface-bg)] transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--text-primary)]">
                          REQ-{String(item.id).padStart(3, '0')}
                        </td>
                        <td className="px-6 py-4 text-sm text-[var(--text-primary)] max-w-xs truncate" title={item.requirement}>
                          {item.requirement}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                            {getStatusIcon(item.status)}
                            <span className="ml-1 capitalize">{item.status}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          {item.visualElement}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            item.complexity === 'High' ? 'bg-[var(--error-light)] text-[var(--error-dark)]' :
                            item.complexity === 'Medium' ? 'bg-[var(--warning-light)] text-[var(--warning-dark)]' :
                            'bg-[var(--success-light)] text-[var(--success-dark)]'
                          }`}>
                            {item.complexity}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          {item.hasNotes && (
                            <div className="flex items-center text-[var(--primary-main)]">
                              <MessageSquare className="w-4 h-4 mr-1" />
                              {item.notes.length || 1} note(s)
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleAddNote(item.id)}
                            className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] mr-3"
                          >
                            Add Note
                          </button>
                          <span className="text-[var(--neutral-300)]">|</span>
                          <Link
                            to={`/analysis-results/${id || item.id}`}
                            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] ml-3"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="px-6 py-12 text-center text-[var(--text-secondary)]">
                        <div className="flex flex-col items-center">
                          <AlertTriangle className="w-12 h-12 text-[var(--neutral-300)] mb-4" />
                          <p className="text-lg font-medium">No requirements found</p>
                          <p className="text-sm">Try adjusting your search or filter criteria</p>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Information Notice */}
          <div className="bg-[var(--info-light)]/10 border border-[var(--info-main)] rounded-lg p-4 mt-6">
            <div className="flex items-start">
              <MessageSquare className="w-5 h-5 text-[var(--info-main)] mt-0.5 mr-2 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-[var(--info-dark)] text-sm">Traceability Matrix Information</h4>
                <p className="text-xs text-[var(--info-dark)] mt-1">
                  This matrix shows the relationship between requirements and visual elements.
                  Track how each requirement is implemented in the system design.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Notes Modal */}
      {showNotesModal && selectedRequirement && (
        <div className="fixed inset-0 bg-[var(--neutral-900)] bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Add Note</h3>
              <button
                onClick={() => setShowNotesModal(false)}
                className="text-[var(--neutral-400)] hover:text-[var(--neutral-600)] text-2xl"
              >
                &times;
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-[var(--text-secondary)] mb-2">Requirement:</p>
              <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">{selectedRequirement.requirement}</p>
            </div>

            <textarea
              placeholder="Enter your note here..."
              rows={4}
              className="w-full px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)] resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleSaveNote(e.target.value);
                }
              }}
            />

            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowNotesModal(false)}
                className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--surface-bg)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  const textarea = document.querySelector('textarea');
                  handleSaveNote(textarea.value);
                }}
                className="px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Traceability;