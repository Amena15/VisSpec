import React, { useState, useMemo, useEffect } from 'react';
import { Search, Filter, Plus, Star, MessageSquare, Clock, CheckCircle, AlertTriangle, AlertOctagon, FileText } from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { documentAPI, validationAPI, traceabilityAPI, projectAPI } from '../services/api';
import { toast } from 'sonner';

const Traceability = () => {
  const { id } = useParams(); // Get project ID parameter from the URL
  console.log('Traceability component - URL project ID:', id);
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [viewRequirement, setViewRequirement] = useState(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedNotes, setSelectedNotes] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  const [requirements, setRequirements] = useState([]);
  const [defects, setDefects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load available projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await projectAPI.getAll();
        console.log('Projects loaded:', response.data);
        setProjects(response.data || []);
      } catch (error) {
        console.error('Failed to load projects:', error);
        toast.error('Failed to load projects');
      }
    };
    loadProjects();
  }, []);

  // Load traceability data from API
  useEffect(() => {
    const loadTraceabilityData = async () => {
      if (!id) {
        console.log('No project ID provided in traceability URL');
        setIsLoading(false);
        return;
      }
      
      setIsLoading(true);
      try {
        // Load project traceability data
        console.log('Loading traceability data for project:', id);
        const response = await traceabilityAPI.getTraceability(id);
        console.log('Traceability response:', response.data);
        
        // Handle different response formats and error cases
        if (response.data.error) {
          toast.error(`Error: ${response.data.error}`);
          return;
        }
        
        // Main endpoint format - convert to frontend format
        if (response.data.traceability) {
          const traceData = response.data.traceability;
          setRequirements(traceData.map(item => ({
            id: item.req_id,
            identifier: item.identifier,
            text: item.text,
            status: item.validation_status || 'valid',
            visual_element: item.visual_elements?.join(', ') || '',
            complexity: item.complexity || 'Medium',
            notes: item.note ? [item.note] : [],
            hasNotes: !!item.note,
            timestamp: new Date().toLocaleDateString()
          })));
          setDefects([]);
          
          if (response.data.project) {
            setSelectedProject(response.data.project);
          }
        } 
        // Fallback for different response structure
        else {
          console.warn('Unexpected response format:', response.data);
          toast.error('Unexpected response format from server');
        }
      } catch (error) {
        console.error('Failed to load traceability data:', error);
        
        // Provide specific error messages
        if (error.response?.status === 404) {
          toast.error('Project not found. Please select a valid project.');
        } else if (error.response?.status === 403) {
          toast.error('Access denied. You do not have permission to view this project.');
        } else if (error.response?.status === 401) {
          toast.error('Authentication required. Please log in again.');
        } else {
          toast.error(`Failed to load traceability data: ${error.response?.data?.detail || error.message}`);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadTraceabilityData();
  }, [id]);

  const traceabilityData = useMemo(() => {
    return requirements.map((req, index) => {
      // Find associated defect for this requirement
      const associatedDefect = defects.find(defect => 
        defect.requirement_id === req.id || 
        defect.req_id === `REQ-${String(req.id || index + 1).padStart(3, '0')}`
      );
      
      return {
        id: req.id || `req-${index + 1}`,
        identifier: req.identifier,
        requirement: req.text || `Requirement ${index + 1}`,
        status: associatedDefect ? 'defective' : (req.status || 'valid'),
        visualElement: req.visual_element || ['Actor: User', 'Actor: Admin', 'Use Case: UC001', 'Use Case: UC002'][index % 4],
        complexity: req.complexity || ['Low', 'Medium', 'High'][index % 3],
        hasNotes: req.notes && req.notes.length > 0,
        notes: req.notes || [],
        timestamp: req.created_at || new Date().toLocaleDateString(),
        defectId: associatedDefect?.id
      };
    });
  }, [requirements, defects]);

  // Filter data based on search and status
  const filteredData = useMemo(() => {
    if (!traceabilityData || traceabilityData.length === 0) return [];
    return traceabilityData.filter(item => {
      const matchesSearch = !searchTerm || 
        item.requirement.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.visualElement.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || item.status === filterStatus;
      return matchesSearch && matchesStatus;
    });
  }, [traceabilityData, searchTerm, filterStatus]);

  const handleSaveNote = async () => {
    if (!selectedRequirement || !noteText.trim()) return;
    
    try {
      const payload = {
        req_id: selectedRequirement.id,
        content: noteText.trim()
      };
      
      // Check authentication token
      const token = localStorage.getItem('token');
      console.log('Authentication token exists:', !!token);
      if (token) {
        console.log('Token length:', token.length);
        console.log('Token starts with:', token.substring(0, 20) + '...');
      }
      
      console.log('Saving note for requirement:', selectedRequirement);
      console.log('Requirement ID being sent:', selectedRequirement.id);
      console.log('Note content:', noteText.trim());
      console.log('Full request payload:', JSON.stringify(payload, null, 2));
      
      // Call API to save note to traceability_notes table
      await traceabilityAPI.saveNote(payload);
      
      toast.success('Note saved successfully!');
      setShowNotesModal(false);
      setSelectedRequirement(null);
      setNoteText('');
      
      // Reload data to show new note
      const response = await traceabilityAPI.getTraceability(id);
      if (response.data && response.data.traceability) {
        const traceData = response.data.traceability;
        setRequirements(traceData.map(item => ({
          id: item.req_id,
          text: item.text,
          status: item.validation_status || 'valid',
          visual_element: item.visual_elements?.join(', ') || '',
          complexity: item.complexity || 'Medium',
          notes: item.note ? [item.note] : [],
          hasNotes: !!item.note,
          timestamp: new Date().toLocaleDateString()
        })));
      }
    } catch (error) {
      console.error('Failed to save note:', error);
      console.error('Error response:', error.response?.data);
      toast.error(`Failed to save note: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'passed': return 'text-[var(--success-hover)] bg-[var(--success-light)]';
      case 'valid': return 'text-[var(--success-hover)] bg-[var(--success-light)]';
      case 'warning': return 'text-[var(--warning-hover)] bg-[var(--warning-light)]';
      case 'ambiguous': return 'text-[var(--warning-hover)] bg-[var(--warning-light)]';
      case 'failed': return 'text-[var(--error-hover)] bg-[var(--error-light)]';
      case 'conflict': return 'text-[var(--error-hover)] bg-[var(--error-light)]';
      case 'defective': return 'text-[var(--error-hover)] bg-[var(--error-light)]';
      default: return 'text-[var(--neutral-500)] bg-[var(--surface-bg)]';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed': return <CheckCircle className="w-4 h-4" />;
      case 'valid': return <CheckCircle className="w-4 h-4" />;
      case 'warning': return <AlertTriangle className="w-4 h-4" />;
      case 'ambiguous': return <AlertTriangle className="w-4 h-4" />;
      case 'failed': return <AlertOctagon className="w-4 h-4" />;
      case 'conflict': return <AlertOctagon className="w-4 h-4" />;
      case 'defective': return <AlertOctagon className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const handleAddNote = (requirementId) => {
    const requirement = traceabilityData.find(req => req.id === requirementId);
    console.log('handleAddNote called with requirementId:', requirementId);
    console.log('Found requirement:', requirement);
    console.log('Requirement ID that will be sent:', requirement?.id);
    setSelectedRequirement(requirement);
    setNoteText('');
    setShowNotesModal(true);
  };

  const handleViewNotes = (item) => {
    setSelectedNotes(item);
    setShowNotesModal(true);
  };

  const handleViewRequirement = (requirementId) => {
    const requirement = traceabilityData.find(req => req.id === requirementId);
    setViewRequirement(requirement);
    setShowViewModal(true);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-main)]"></div>
          <p className="mt-4 text-[var(--text-secondary)]">Loading traceability data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center">
              <div>
                <h1 className="text-3xl font-bold text-[var(--text-primary)]">Inspect Requirements Traceability</h1>
                <p className="text-[var(--text-secondary)] mt-2">Track relationships between requirements across all project documents</p>
              </div>
            </div>
          </div>

          {/* Project Selector */}
          {!id && (
            <div className="mb-6 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Select Project for Traceability Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map(project => (
                  <div 
                    key={project.project_id || project.id} 
                    className="p-4 rounded-lg border cursor-pointer transition-all border-[var(--card-border)] hover:border-[var(--primary-main)] hover:bg-[var(--surface-bg)]"
                    onClick={() => {
                      const projectId = project.project_id || project.id;
                      console.log('Clicked project:', projectId, project.name);
                      console.log('Project object:', project);
                      if (!projectId) {
                        console.error('Project ID is undefined:', project);
                        toast.error('Invalid project: Missing project ID');
                        return;
                      }
                      navigate(`/traceability/${projectId}`);
                    }}
                  >
                    <div className="flex items-center mb-2">
                      <div className="h-5 w-5 bg-[var(--primary-main)] rounded mr-2 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">P</span>
                      </div>
                      <h4 className="font-medium text-[var(--text-primary)]">{project.name || `Project ${(project.project_id || project.id)?.substring(0, 8)}`}</h4>
                    </div>
                    <div className="text-sm text-[var(--text-secondary)]">
                      <p>Documents: {project.document_count || 0}</p>
                      <p>Requirements: {project.requirements_count || 0}</p>
                      <p>Status: {project.status || 'Active'}</p>
                      <p>Created: {project.created_at ? new Date(project.created_at).toLocaleDateString() : 'Unknown'}</p>
                    </div>
                  </div>
                ))}
              </div>
              {projects.length === 0 && (
                <div className="text-center py-8">
                  <div className="h-12 w-12 bg-[var(--neutral-300)] rounded mx-auto mb-4 flex items-center justify-center">
                    <span className="text-[var(--neutral-500)] text-lg font-bold">P</span>
                  </div>
                  <p className="text-[var(--text-secondary)]">No projects available</p>
                  <p className="text-sm text-[var(--text-secondary)] mt-2">Please create a project first to view traceability</p>
                  <button
                    onClick={() => navigate('/projects')}
                    className="mt-4 px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
                  >
                    Go to Projects
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Controls - Only show when project is selected */}
          {id && (
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
                  className="appearance-none bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg px-4 py-2 pr-8 text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent"
                >
                  <option value="all">All Status</option>
                  <option value="valid">Valid Only</option>
                  <option value="defective">Defective Only</option>
                  <option value="ambiguous">Ambiguous Only</option>
                  <option value="conflict">Conflict Only</option>
                </select>
              </div>
            </div>
          )}

          {/* Traceability Table - Only show when project is selected */}
          {id && (
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
                            {item.identifier || `REQ-${String(item.id).padStart(3, '0')}`}
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
                              <button
                                onClick={() => handleViewNotes(item)}
                                className="flex items-center text-[var(--primary-main)] hover:text-[var(--primary-hover)] transition-colors"
                              >
                                <MessageSquare className="w-4 h-4 mr-1" />
                                {item.notes.length || 1} note(s)
                              </button>
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
                            <button
                              onClick={() => handleViewRequirement(item.id)}
                              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] ml-3"
                            >
                              View
                            </button>
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
          )}

          {/* Information Notice - Only show when project is selected */}
          {id && (
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
          )}
        </div>
      </div>

      {/* Notes Modal */}
      {showNotesModal && selectedRequirement && (
        <div className="fixed inset-0 bg-[var(--neutral-900)] bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Add Note</h3>
              <button
                onClick={() => {
                  setShowNotesModal(false);
                  setNoteText('');
                  setSelectedRequirement(null);
                }}
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
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              className="w-full px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)] resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleSaveNote();
                }
              }}
            />

            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => {
                  setShowNotesModal(false);
                  setNoteText('');
                  setSelectedRequirement(null);
                }}
                className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--surface-bg)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Requirement Modal */}
      {showViewModal && viewRequirement && (
        <div className="fixed inset-0 bg-[var(--neutral-900)] bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-2xl w-full p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Requirement Details</h3>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-[var(--neutral-400)] hover:text-[var(--neutral-600)] text-2xl"
              >
                &times;
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Requirement ID:</p>
                <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)] font-mono">
                  REQ-{String(viewRequirement.id).padStart(3, '0')}
                </p>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Requirement Text:</p>
                <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                  {viewRequirement.requirement}
                </p>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Status:</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(viewRequirement.status)}`}>
                  {getStatusIcon(viewRequirement.status)}
                  <span className="ml-1 capitalize">{viewRequirement.status}</span>
                </span>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Visual Elements:</p>
                <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                  {viewRequirement.visualElement}
                </p>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Complexity:</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  viewRequirement.complexity === 'High' ? 'bg-[var(--error-light)] text-[var(--error-dark)]' :
                  viewRequirement.complexity === 'Medium' ? 'bg-[var(--warning-light)] text-[var(--warning-dark)]' :
                  'bg-[var(--success-light)] text-[var(--success-dark)]'
                }`}>
                  {viewRequirement.complexity}
                </span>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Last Updated:</p>
                <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                  {viewRequirement.timestamp}
                </p>
              </div>

              {viewRequirement.hasNotes && (
                <div>
                  <p className="text-sm text-[var(--text-secondary)] mb-2">Notes:</p>
                  <div className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                    {viewRequirement.notes.map((note, index) => (
                      <div key={index} className="mb-2 last:mb-0">
                        <p>{note.content || note}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowViewModal(false)}
                className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--surface-bg)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notes Modal */}
      {showNotesModal && selectedNotes && (
        <div className="fixed inset-0 bg-[var(--neutral-900)] bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--card-bg)] rounded-xl max-w-2xl w-full p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Notes for Requirement</h3>
              <button
                onClick={() => setShowNotesModal(false)}
                className="text-[var(--neutral-400)] hover:text-[var(--neutral-600)] text-2xl"
              >
                &times;
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Requirement:</p>
                <p className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                  {selectedNotes.requirement}
                </p>
              </div>

              <div>
                <p className="text-sm text-[var(--text-secondary)] mb-2">Notes:</p>
                <div className="text-sm bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)]">
                  {selectedNotes.notes && selectedNotes.notes.length > 0 ? (
                    selectedNotes.notes.map((note, index) => (
                      <div key={index} className="mb-3 last:mb-0">
                        <p className="text-[var(--text-primary)]">{note.content || note}</p>
                        {note.updated_at && (
                          <p className="text-xs text-[var(--text-secondary)] mt-1">
                            Updated: {new Date(note.updated_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-[var(--text-secondary)] italic">No notes available</p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowNotesModal(false)}
                className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--surface-bg)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Traceability;
