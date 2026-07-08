import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ChevronRight } from 'lucide-react';
import { 
  CheckCircle, 
  XCircle, 
  MessageSquare, 
  RotateCcw, 
  Loader2, 
  FileText, 
  Eye, 
  BarChart3, 
  Clock,
  AlertTriangle,
  ExternalLink,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  Download,
  FileText as FileIcon,
  X
} from 'lucide-react';

import { apiClient } from '../services/api';

const SupervisorReview = () => {
  const { project_id } = useParams();
  const navigate = useNavigate();

  const [reviewView, setReviewView] = useState(null);
  const [decision, setDecision] = useState('approved');
  const [comments, setComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // Enhanced features state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [documentFilter, setDocumentFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedDocuments, setExpandedDocuments] = useState({});
  const itemsPerPage = 25;
  
  // Modal state for full requirement text
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const run = async () => {
      setIsLoading(true);
      try {
        const token = localStorage.getItem('token');
        console.log('[SupervisorReview] token present:', !!token);
        if (!token) console.warn('[SupervisorReview] No token in localStorage');

        const res = await apiClient.get(`/api/supervisor/review/${project_id}`);
        setReviewView(res.data);
      } catch (err) {
        console.error('[SupervisorReview] failed to load review view:', err?.response || err);
        toast.error('Failed to load review view');
      } finally {
        setIsLoading(false);
      }
    };
    if (project_id) run();
  }, [project_id]);

  const reqStats = useMemo(() => {
    const items = reviewView?.traceability || [];
    return {
      total: items.length,
      failed: items.filter((i) => i.validation_status === 'failed').length,
      warning: items.filter((i) => i.validation_status === 'warning').length,
      passed: items.filter((i) => i.validation_status === 'passed').length,
    };
  }, [reviewView]);

  // Enhanced filtering and pagination logic
  const filteredAndPaginatedTraceability = useMemo(() => {
    let items = reviewView?.traceability || [];
    
    // Apply search filter
    if (searchTerm) {
      items = items.filter(item => 
        (item.identifier || item.semantic_id || item.req_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.text || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Apply status filter
    if (statusFilter !== 'all') {
      items = items.filter(item => item.validation_status === statusFilter);
    }
    
    // Apply document filter
    if (documentFilter !== 'all') {
      items = items.filter(item => item.source_document === documentFilter);
    }
    
    // Get unique documents for filter
    const uniqueDocuments = [...new Set(items.map(item => item.source_document || 'Unknown'))];
    
    // Pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedItems = items.slice(startIndex, startIndex + itemsPerPage);
    
    return {
      items: paginatedItems,
      totalCount: items.length,
      totalPages: Math.ceil(items.length / itemsPerPage),
      uniqueDocuments
    };
  }, [reviewView, searchTerm, statusFilter, documentFilter, currentPage]);

  // Toggle document expansion
  const toggleDocumentExpansion = (document) => {
    setExpandedDocuments(prev => ({
      ...prev,
      [document]: !prev[document]
    }));
  };

  // Handle requirement text click
  const handleRequirementClick = (item) => {
    setSelectedRequirement(item);
    setShowModal(true);
  };

  // Close modal
  const closeModal = () => {
    setShowModal(false);
    setSelectedRequirement(null);
  };

  // Export to PDF
  const exportToPDF = async () => {
    try {
      const reportData = {
        project_name: reviewView?.project?.name || 'Unknown Project',
        analysis_data: {
          total_requirements: reviewView?.traceability?.length || 0,
          quality_score: reviewView?.latest_validation?.overall_score || 0,
          defect_count: reqStats.failed + reqStats.warning,
          review_status: 'supervisor_review'
        },
        diagrams: [],
        metrics: {
          validation_status: {
            passed: reqStats.passed,
            failed: reqStats.failed,
            warning: reqStats.warning
          },
          completion_rate: Math.round((reqStats.passed / (reviewView?.traceability?.length || 1)) * 100)
        },
        traceability: reviewView?.traceability || [],
        report_type: 'supervisor'
      };

      const response = await apiClient.post('/api/reports/export', reportData, {
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `supervisor_review_${reviewView?.project?.name?.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Review report exported successfully');
    } catch (error) {
      console.error('Failed to export report:', error);
      toast.error('Failed to export report');
    }
  };

  const statusBadge = (s) => {
    switch (s) {
      case 'failed':
        return { bg: 'bg-[var(--error-light)]', text: 'text-[var(--error-hover)]', Icon: XCircle };
      case 'warning':
        return { bg: 'bg-[var(--warning-light)]', text: 'text-[var(--warning-hover)]', Icon: RotateCcw };
      default:
        return { bg: 'bg-[var(--success-light)]', text: 'text-[var(--success-hover)]', Icon: CheckCircle };
    }
  };

  const complexityBadge = (complexity) => {
    switch (complexity) {
      case 'high':
        return { bg: 'bg-[var(--error-light)]', text: 'text-[var(--error-hover)]', label: 'High' };
      case 'medium':
        return { bg: 'bg-[var(--warning-light)]', text: 'text-[var(--warning-hover)]', label: 'Medium' };
      default:
        return { bg: 'bg-[var(--success-light)]', text: 'text-[var(--success-hover)]', label: 'Low' };
    }
  };

  const parseVisualElements = (value) => {
    if (!value) return [];

    const rawItems = Array.isArray(value)
      ? value
      : String(value)
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean);

    return rawItems.map((item) => {
      const [kindPart, ...labelParts] = String(item).split(':');
      const kind = (labelParts.length > 0 ? kindPart : 'node').trim().toLowerCase();
      const label = (labelParts.length > 0 ? labelParts.join(':') : kindPart).trim();
      return { kind, label, raw: String(item) };
    });
  };

  const openDiagramForRequirement = (item, selectedNode = null) => {
    const docId = item?.doc_id;
    const highlightLabel = selectedNode?.label || parseVisualElements(item?.visual_elements)[0]?.label || '';
    const nodeKind = selectedNode?.kind || parseVisualElements(item?.visual_elements)[0]?.kind || 'node';
    const preferredDiagram = nodeKind.includes('actor') || nodeKind.includes('use case') ? 'usecase' : 'sequence';

    const basePath = docId ? `/visualization/${docId}` : '/visualization';
    const query = new URLSearchParams({
      source: 'supervisor-review',
      diagram: preferredDiagram,
    });

    if (highlightLabel) {
      query.set('highlight', highlightLabel);
      query.set('nodeType', nodeKind);
    }

    window.open(`${basePath}?${query.toString()}`, '_blank', 'noopener,noreferrer');
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const res = await apiClient.post(`/api/supervisor/review/${project_id}`, {
        decision,
        comments,
      });

      toast.success('Review submitted');
      // Optional: navigate back to supervisor dashboard
      navigate('/supervisor');
      return res;
    } catch (err) {
      console.error(err);
      toast.error(err?.response?.data?.detail || 'Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-[var(--primary-main)] animate-spin" />
      </div>
    );
  }

  const traceability = reviewView?.traceability || [];

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
        {/* Breadcrumb Navigation */}
        <div className="mb-6">
          <nav className="flex items-center text-sm text-[var(--text-secondary)]">
            <button
              onClick={() => navigate('/supervisor')}
              className="hover:text-[var(--primary-main)] transition-colors"
            >
              Reviews
            </button>
            <ChevronRight className="w-4 h-4 mx-2" />
            <span className="text-[var(--text-primary)]">{reviewView?.project?.name || 'Loading...'}</span>
          </nav>
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Project Review</h1>
          <p className="text-[var(--text-secondary)] mt-2">Review and approve project requirements</p>
        </div>

        {/* Consolidated Project Overview */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Project Overview</h2>
            <div className="text-sm text-[var(--text-secondary)]">
              {reviewView?.project?.name || 'Unknown Project'}
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <FileText className="h-6 w-6 text-[var(--primary-main)]" />
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">{reqStats.total}</div>
              <div className="text-sm text-[var(--text-secondary)]">Total Requirements</div>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <BarChart3 className="h-6 w-6 text-[var(--warning-main)]" />
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">
                {reviewView?.latest_validation?.overall_score || 0}%
              </div>
              <div className="text-sm text-[var(--text-secondary)]">Quality Score</div>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <XCircle className="h-6 w-6 text-[var(--error-main)]" />
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">{reqStats.failed}</div>
              <div className="text-sm text-[var(--text-secondary)]">Failed</div>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <RotateCcw className="h-6 w-6 text-[var(--warning-main)]" />
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">{reqStats.warning}</div>
              <div className="text-sm text-[var(--text-secondary)]">Warning</div>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <CheckCircle className="h-6 w-6 text-[var(--success-main)]" />
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">{reqStats.passed}</div>
              <div className="text-sm text-[var(--text-secondary)]">Passed</div>
            </div>
          </div>
          
          {/* Status Pills */}
          <div className="flex items-center gap-4 mt-6 pt-6 border-t border-[var(--card-border)]">
            <span className="text-sm text-[var(--text-secondary)]">Status Breakdown:</span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusBadge('failed').bg} ${statusBadge('failed').text}`}>
              Failed: {reqStats.failed}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusBadge('warning').bg} ${statusBadge('warning').text}`}>
              Warning: {reqStats.warning}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusBadge('passed').bg} ${statusBadge('passed').text}`}>
              Passed: {reqStats.passed}
            </span>
          </div>
        </div>

        <div className="w-full">
          <div className="bg-white rounded-xl border border-gray-200 shadow-lg p-8">

            {/* Enhanced Traceability Table Header */}
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Traceability Matrix (Read-only)</h2>
            </div>

            {/* Sticky Search and Filter Controls */}
            <div className="bg-[var(--surface-bg)] rounded-lg p-4 mb-4 border border-[var(--card-border)] lg:sticky lg:top-8 z-10">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                  <input
                    type="text"
                    placeholder="Search requirements..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setCurrentPage(1);
                    }}
                    className="w-full pl-10 pr-3 py-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)]"
                  />
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-3 py-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)]"
                >
                  <option value="all">All Status</option>
                  <option value="passed">Passed</option>
                  <option value="warning">Warning</option>
                  <option value="failed">Failed</option>
                </select>

                {/* Document Filter */}
                <select
                  value={documentFilter}
                  onChange={(e) => {
                    setDocumentFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="px-3 py-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)]"
                >
                  <option value="all">All Documents</option>
                  {filteredAndPaginatedTraceability.uniqueDocuments.map(doc => (
                    <option key={doc} value={doc}>{doc}</option>
                  ))}
                </select>

                {/* Results Count */}
                <div className="text-sm text-[var(--text-secondary)] flex items-center">
                  <span>{filteredAndPaginatedTraceability.totalCount} requirements found</span>
                </div>

                {/* Export PDF */}
                <button
                  onClick={exportToPDF}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
                >
                  <Download className="h-4 w-4" />
                  Export PDF
                </button>
              </div>
            </div>

            {/* Professional Wide Table */}
            <div className="overflow-x-auto bg-white rounded-lg border border-[var(--card-border)] shadow-sm">
              <table className="w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-20">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Requirement ID</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Requirement Text</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Validation Status</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Visual Element</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Complexity</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-r border-gray-200">Notes</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAndPaginatedTraceability.items.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                        {reviewView?.traceability?.length === 0 ? 'No requirements found in this project.' : 'No requirements match your filters.'}
                      </td>
                    </tr>
                  ) : (
                    // Group by document
                    Object.entries(
                      filteredAndPaginatedTraceability.items.reduce((groups, item) => {
                        const doc = item.source_document || 'Unknown Document';
                        if (!groups[doc]) groups[doc] = [];
                        groups[doc].push(item);
                        return groups;
                      }, {})
                    ).map(([document, items]) => {
                      const isExpanded = expandedDocuments[document] !== false;
                      const docStats = {
                        total: items.length,
                        failed: items.filter(i => i.validation_status === 'failed').length,
                        warning: items.filter(i => i.validation_status === 'warning').length,
                        passed: items.filter(i => i.validation_status === 'passed').length
                      };
                      
                      return (
                        <React.Fragment key={document}>
                          {/* Document Header */}
                          <tr className="bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors border-b border-gray-200" onClick={() => toggleDocumentExpansion(document)}>
                            <td colSpan="7" className="px-6 py-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                  <div className="flex items-center gap-3">
                                    {isExpanded ? (
                                      <ChevronDown className="h-5 w-5 text-gray-500" />
                                    ) : (
                                      <ChevronUp className="h-5 w-5 text-gray-500" />
                                    )}
                                    <FileIcon className="h-5 w-5 text-blue-600" />
                                  </div>
                                  <div>
                                    <span className="font-semibold text-gray-900 text-base">{document}</span>
                                    <div className="text-sm text-gray-500 mt-1">{docStats.total} requirements</div>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3">
                                  {docStats.failed > 0 && (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                      Failed: {docStats.failed}
                                    </span>
                                  )}
                                  {docStats.warning > 0 && (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                      Warning: {docStats.warning}
                                    </span>
                                  )}
                                  {docStats.passed > 0 && (
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                      Passed: {docStats.passed}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                          
                          {/* Document Requirements */}
                          {isExpanded && items.map((item) => {
                            const status = statusBadge(item.validation_status);
                            const complexity = complexityBadge(item.complexity || 'low');
                            const isHighSeverity = item.validation_status === 'failed';
                            
                            return (
                              <tr 
                                key={item.req_id || item.semantic_id} 
                                className={`hover:bg-gray-50 transition-colors ${
                                  isHighSeverity ? 'border-l-4 border-l-red-500' : ''
                                } ${items.indexOf(item) % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                              >
                                <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                  <div className="text-sm font-mono font-semibold text-blue-600">
                                    {item.identifier || item.semantic_id || item.req_id}
                                  </div>
                                </td>
                                <td className="px-6 py-4 border-r border-gray-200">
                                  <div 
                                    className="text-sm text-blue-600 max-w-md cursor-pointer hover:text-blue-800 hover:underline" 
                                    title={item.text}
                                    onClick={() => handleRequirementClick(item)}
                                  >
                                    {item.text && item.text.length > 120 ? `${item.text.substring(0, 120)}...` : item.text}
                                  </div>
                                  {item.text && item.text.length > 120 && (
                                    <div className="text-xs text-gray-500 mt-1">Click to view full text</div>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                  <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
                                    item.validation_status === 'failed' ? 'bg-red-100 text-red-800' :
                                    item.validation_status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-green-100 text-green-800'
                                  }`}>
                                    {item.validation_status === 'failed' && <XCircle className="h-3 w-3" />}
                                    {item.validation_status === 'warning' && <RotateCcw className="h-3 w-3" />}
                                    {item.validation_status === 'passed' && <CheckCircle className="h-3 w-3" />}
                                    {item.validation_status}
                                  </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                  {parseVisualElements(item.visual_elements).length > 0 ? (
                                    <div className="flex max-w-md flex-wrap gap-2">
                                      {parseVisualElements(item.visual_elements).map((node) => (
                                        <button
                                          key={`${item.req_id}-${node.raw}`}
                                          type="button"
                                          onClick={() => openDiagramForRequirement(item, node)}
                                          className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
                                          title={`Open diagram focus for ${node.raw}`}
                                        >
                                          <span className="opacity-80">{node.kind}</span>
                                          <span>{node.label}</span>
                                          <ExternalLink className="h-3 w-3" />
                                        </button>
                                      ))}
                                    </div>
                                  ) : (
                                    <span className="text-gray-400">-</span>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap border-r border-gray-200">
                                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                    item.complexity === 'high' ? 'bg-red-100 text-red-800' :
                                    item.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-green-100 text-green-800'
                                  }`}>
                                    {item.complexity || 'low'}
                                  </span>
                                </td>
                                <td className="px-6 py-4 border-r border-gray-200">
                                  {item.note?.content ? (
                                    <div className="text-sm text-gray-900 max-w-md">
                                      <div className="flex items-start gap-2">
                                        <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                                        <span className="truncate" title={item.note.content}>
                                          {item.note.content.length > 80 ? `${item.note.content.substring(0, 80)}...` : item.note.content}
                                        </span>
                                      </div>
                                    </div>
                                  ) : (
                                    <span className="text-gray-400 text-sm">No notes</span>
                                  )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <button
                                    onClick={() => openDiagramForRequirement(item)}
                                    className="text-blue-600 hover:text-blue-800 flex items-center gap-2 text-sm font-medium transition-colors"
                                    title="View Diagrams"
                                  >
                                    <Eye className="h-4 w-4" />
                                    <span>View</span>
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {filteredAndPaginatedTraceability.totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg mt-4">
                <div className="text-sm text-[var(--text-secondary)]">
                  Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredAndPaginatedTraceability.totalCount)} of {filteredAndPaginatedTraceability.totalCount} requirements
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 text-sm bg-[var(--card-bg)] border border-[var(--card-border)] rounded hover:bg-[var(--surface-bg)] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-[var(--text-primary)]">
                    Page {currentPage} of {filteredAndPaginatedTraceability.totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(Math.min(filteredAndPaginatedTraceability.totalPages, currentPage + 1))}
                    disabled={currentPage === filteredAndPaginatedTraceability.totalPages}
                    className="px-3 py-1 text-sm bg-[var(--card-bg)] border border-[var(--card-border)] rounded hover:bg-[var(--surface-bg)] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Floating Decision Footer */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-2xl p-4 z-50">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-1">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Decision</label>
                  <select
                    className="w-48 px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    value={decision}
                    onChange={(e) => setDecision(e.target.value)}
                  >
                    <option value="approved">Approve</option>
                    <option value="changes_requested">Request Changes</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Comments (optional)</label>
                  <textarea
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors h-10 resize-none"
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Provide supervisor feedback..."
                  />
                </div>
              </div>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium text-base whitespace-nowrap"
              >
                {isSubmitting ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Submitting...
                  </span>
                ) : (
                  'Submit Review'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Requirement Details Modal */}
        {showModal && selectedRequirement && (
          <div className="fixed inset-0 z-50 overflow-y-auto bg-black/50 p-4 md:p-6">
            <div className="mx-auto flex min-h-full items-start justify-center">
              <div className="bg-white rounded-xl border border-gray-200 shadow-2xl max-w-4xl w-full max-h-[calc(100vh-3rem)] flex flex-col overflow-hidden">
              {/* Modal Header */}
              <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Requirement Details</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {selectedRequirement.identifier || selectedRequirement.semantic_id || selectedRequirement.req_id}
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="flex-1 min-h-0 overflow-y-auto p-6 overscroll-contain">
                <div className="space-y-6">
                  {/* Requirement ID */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Requirement ID</label>
                    <div className="text-sm font-mono text-blue-600 bg-blue-50 px-3 py-2 rounded-lg">
                      {selectedRequirement.identifier || selectedRequirement.semantic_id || selectedRequirement.req_id}
                    </div>
                  </div>

                  {/* Source Document */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Source Document</label>
                    <div className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                      {selectedRequirement.source_document || 'Unknown Document'}
                    </div>
                  </div>

                  {/* Module Name */}
                  {selectedRequirement.module_name && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Module</label>
                      <div className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                        {selectedRequirement.module_name}
                      </div>
                    </div>
                  )}

                  {/* Full Requirement Text */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Requirement Text</label>
                    <div className="text-sm text-gray-900 bg-gray-50 px-4 py-3 rounded-lg leading-relaxed">
                      {selectedRequirement.text || 'No text available'}
                    </div>
                  </div>

                  {/* Validation Status */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Validation Status</label>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
                        selectedRequirement.validation_status === 'failed' ? 'bg-red-100 text-red-800' :
                        selectedRequirement.validation_status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {selectedRequirement.validation_status === 'failed' && <XCircle className="h-3 w-3" />}
                        {selectedRequirement.validation_status === 'warning' && <RotateCcw className="h-3 w-3" />}
                        {selectedRequirement.validation_status === 'passed' && <CheckCircle className="h-3 w-3" />}
                        {selectedRequirement.validation_status}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({selectedRequirement.defect_count || 0} defects)
                      </span>
                    </div>
                  </div>

                  {/* Visual Elements */}
                  {selectedRequirement.visual_elements && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Visual Elements</label>
                      <div className="bg-gray-50 px-3 py-2 rounded-lg">
                        <div className="flex flex-wrap gap-2">
                          {parseVisualElements(selectedRequirement.visual_elements).map((node) => (
                            <button
                              key={`${selectedRequirement.req_id}-${node.raw}`}
                              type="button"
                              onClick={() => openDiagramForRequirement(selectedRequirement, node)}
                              className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
                            >
                              <span className="opacity-80">{node.kind}</span>
                              <span>{node.label}</span>
                              <ExternalLink className="h-3 w-3" />
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Complexity */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Complexity</label>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        selectedRequirement.complexity === 'high' ? 'bg-red-100 text-red-800' :
                        selectedRequirement.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {selectedRequirement.complexity || 'low'}
                      </span>
                    </div>
                  </div>

                  {/* Notes */}
                  {selectedRequirement.note?.content && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                      <div className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                        <div className="flex items-start gap-2">
                          <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                          <span>{selectedRequirement.note.content}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Defects */}
                  {selectedRequirement.defects && selectedRequirement.defects.length > 0 && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Defects ({selectedRequirement.defects.length})</label>
                      <div className="space-y-2">
                        {selectedRequirement.defects.map((defect, index) => (
                          <div key={defect.defect_id || index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                    defect.severity === 'high' ? 'bg-red-100 text-red-800' :
                                    defect.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-gray-100 text-gray-800'
                                  }`}>
                                    {defect.severity}
                                  </span>
                                  <span className="text-xs text-gray-500">
                                    {defect.confidence && `(${Math.round(defect.confidence * 100)}% confidence)`}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-900">{defect.description}</p>
                                {defect.ai_suggestion && (
                                  <p className="text-sm text-gray-600 mt-1 italic">
                                    <span className="font-medium">Suggestion:</span> {defect.ai_suggestion}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Modal Footer */}
              <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
                <button
                  onClick={closeModal}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => openDiagramForRequirement(selectedRequirement)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <Eye className="h-4 w-4" />
                  View Diagrams
                </button>
              </div>
            </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SupervisorReview;

