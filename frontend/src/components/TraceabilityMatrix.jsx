import React, { useState, useMemo } from 'react';
import { Search, Filter, Plus, Star, MessageSquare, Clock, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

const TraceabilityMatrix = ({ requirements = [], defects = [], onAddNote }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState(null);

  // Mock traceability data
  const traceabilityData = useMemo(() => {
    return requirements.map((req, index) => ({
      id: req.id || `req-${index + 1}`,
      requirement: req.text || `Requirement ${index + 1}`,
      status: Math.random() > 0.3 ? 'valid' : 'defective',
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
      case 'defective': return 'text-[var(--error-hover)] bg-[var(--error-light)]';
      default: return 'text-[var(--neutral-500)] bg-[var(--surface-bg)]';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'valid': return <CheckCircle className="w-4 h-4" />;
      case 'defective': return <AlertOctagon className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const handleAddNote = (requirementId) => {
    const requirement = traceabilityData.find(req => req.id === requirementId);
    setSelectedRequirement(requirement);
    setShowNotesModal(true);
  };

  const handleSaveNote = (noteText) => {
    if (onAddNote && selectedRequirement) {
      onAddNote(selectedRequirement.id, noteText);
    }
    setShowNotesModal(false);
    setSelectedRequirement(null);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--neutral-400)] w-4 h-4" />
            <input
              type="text"
              placeholder="Search requirements..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-[var(--neutral-300)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent w-64"
            />
          </div>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-[var(--neutral-300)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent"
          >
            <option value="all">All Statuses</option>
            <option value="valid">Valid</option>
            <option value="defective">Defective</option>
          </select>
        </div>

        <button className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-dark)] transition-colors">
          <Plus className="w-4 h-4 mr-2" />
          Add Note
        </button>
      </div>

      {/* Traceability Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg">
          <thead className="bg-[var(--neutral-50)]">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Requirement</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Visual Element</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Complexity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Notes</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-[var(--neutral-500)] uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--card-border)]">
            {filteredData.length > 0 ? (
              filteredData.map((item, index) => (
                <tr key={item.id} className="hover:bg-[var(--neutral-50)]">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--neutral-900)]">
                    REQ-{String(index + 1).padStart(3, '0')}
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--neutral-900)] max-w-xs truncate" title={item.requirement}>
                    {item.requirement}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {getStatusIcon(item.status)}
                      <span className="ml-1 capitalize">{item.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--neutral-500)]">
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--neutral-500)]">
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
                      className="text-[var(--primary-main)] hover:text-[var(--primary-dark)] mr-3"
                    >
                      Add Note
                    </button>
                    <span className="text-[var(--neutral-300)]">|</span>
                    <button className="text-[var(--neutral-600)] hover:text-[var(--neutral-900)] ml-3">
                      View
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" className="px-6 py-12 text-center text-[var(--neutral-500)]">
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

      {/* Notes Modal */}
      {showNotesModal && selectedRequirement && (
        <div className="fixed inset-0 bg-[var(--neutral-900)] bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[var(--neutral-900)]">Add Note</h3>
              <button
                onClick={() => setShowNotesModal(false)}
                className="text-[var(--neutral-400)] hover:text-[var(--neutral-600)] text-2xl"
              >
                &times;
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-[var(--neutral-600)] mb-2">Requirement:</p>
              <p className="text-sm bg-[var(--neutral-50)] p-3 rounded border border-[var(--card-border)]">{selectedRequirement.requirement}</p>
            </div>

            <textarea
              placeholder="Enter your note here..."
              rows={4}
              className="w-full px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleSaveNote(e.target.value);
                }
              }}
            />

            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowNotesModal(false)}
                className="px-4 py-2 text-[var(--neutral-700)] bg-[var(--neutral-100)] rounded-lg hover:bg-[var(--neutral-200)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  const textarea = document.querySelector('textarea');
                  handleSaveNote(textarea.value);
                }}
                className="px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-dark)] transition-colors"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Information Notice */}
      <div className="bg-[var(--info-light)] border border-[var(--info-main)] rounded-lg p-4">
        <div className="flex items-start">
          <MessageSquare className="w-5 h-5 text-[var(--info-main)] mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-[var(--info-dark)] text-sm">Traceability Notes Information</h4>
            <p className="text-xs text-[var(--info-dark)] mt-1">
              Notes are informational only and do not modify requirement text (BR-16).
              All notes are timestamped and associated with specific requirements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraceabilityMatrix;