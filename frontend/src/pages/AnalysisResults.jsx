import React, { useState, useEffect, useMemo } from 'react';
import {
  ArrowLeft, FileText, AlertTriangle, CheckCircle, Clock, Eye, Download,
  TrendingUp, XCircle, AlertOctagon, BarChart3, Loader2, Play, ShieldCheck,
  Tags, Users, MessageSquare, Search, Filter, ChevronDown, ChevronRight,
  Wand2, Lightbulb, ShieldAlert
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { documentAPI, validationAPI, analysisAPI } from '../services/api';

const CATEGORY_CONFIG = {
  functional: { label: 'Functional', color: 'bg-blue-100 text-blue-800 border-blue-200', icon: '' },
  non_functional: { label: 'Non-Functional', color: 'bg-purple-100 text-purple-800 border-purple-200', icon: '' },
  interface: { label: 'Interface', color: 'bg-green-100 text-green-800 border-green-200', icon: '' },
  constraint: { label: 'Constraint', color: 'bg-orange-100 text-orange-800 border-orange-200', icon: '' },
  data: { label: 'Data', color: 'bg-teal-100 text-teal-800 border-teal-200', icon: '' },
  uncategorized: { label: 'Uncategorized', color: 'bg-gray-100 text-gray-800 border-gray-200', icon: '' },
};

const VALIDATION_STATUS_CONFIG = {
  passed: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50', label: 'Passed' },
  warning: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Warning' },
  failed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', label: 'Failed' },
  pending: { icon: Clock, color: 'text-gray-400', bg: 'bg-gray-50', label: 'Pending' },
};

const MODAL_VERB_COLORS = {
  shall: 'text-green-600 font-semibold',
  must: 'text-red-600 font-semibold',
  should: 'text-amber-600 font-semibold',
  will: 'text-blue-600 font-semibold',
  may: 'text-gray-500',
};

const AnalysisResults = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('findings');
  const [expandedFinding, setExpandedFinding] = useState(null);
  const [expandedReq, setExpandedReq] = useState(null);
  const [document, setDocument] = useState(null);
  const [validation, setValidation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isValidating, setIsValidating] = useState(false);
  const [isEnriching, setIsEnriching] = useState(false);
  const [reqSearch, setReqSearch] = useState('');
  const [reqFilter, setReqFilter] = useState('all');
  const [reqGroupBy, setReqGroupBy] = useState('module');
  const [expandedModules, setExpandedModules] = useState({});

  useEffect(() => {
    if (id) fetchDocument();
  }, [id]);

  const fetchDocument = async () => {
    setIsLoading(true);
    try {
      const response = await documentAPI.getById(id);
      
      // Auto-organize requirements when document loads
      if (response.data && response.data.requirements && !isEnriched) {
        handleEnrichRequirements();
      }
      setDocument(response.data);
      
      // Also fetch validation results if available
      await fetchValidationResults();
    } catch (error) {
      console.error('Failed to fetch document:', error);
      toast.error('Failed to load document');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchValidationResults = async () => {
    try {
      const response = await validationAPI.getValidationResults(id);
      setValidation(response.data);
    } catch (error) {
      // Don't show error for validation results - it might just not exist yet
      console.log('No validation results found yet');
    }
  };

  const handleEnrichRequirements = async () => {
    if (!id) return;
    setIsEnriching(true);
    try {
      const response = await analysisAPI.enrichDocument(id);
      toast.success(`Organized ${response.data.total_requirements} requirements with classifications!`);
      await fetchDocument();
    } catch (error) {
      console.error('Enrichment failed:', error);
      toast.error(error.response?.data?.detail || 'Requirement organization failed. Please try again.');
    } finally {
      setIsEnriching(false);
    }
  };

  const handleRunValidation = async () => {
    if (!id) return;
    setIsValidating(true);
    try {
      const response = await validationAPI.validateDocument(id);
      if (response.data.perfect_score) {
        toast.success('Perfect Score! No defects found.');
      } else {
        toast.success(`Validation complete! Found ${response.data.total_defects} defects.`);
      }
      // Refresh validation results from database
      await fetchValidationResults();
    } catch (error) {
      console.error('Validation failed:', error);
      toast.error(error.response?.data?.detail || 'Validation failed. Please try again.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleApplySuggestion = (findingId) => {
    toast.success('Suggestion applied successfully!');
    setExpandedFinding(null);
  };

  const handleIgnoreFinding = (findingId) => {
    toast.info('Finding ignored');
    setExpandedFinding(null);
  };

  const toggleModule = (moduleName) => {
    setExpandedModules(prev => ({ ...prev, [moduleName]: !prev[moduleName] }));
  };

  const isEnriched = useMemo(() => {
    return document?.requirements?.some(r => r.category);
  }, [document]);

  const processedRequirements = useMemo(() => {
    if (!document?.requirements) return [];
    let reqs = [...document.requirements];
    if (reqSearch.trim()) {
      const term = reqSearch.toLowerCase();
      reqs = reqs.filter(r =>
        (r.original_text || '').toLowerCase().includes(term) ||
        (r.semantic_id || '').toLowerCase().includes(term) ||
        (r.module_name || '').toLowerCase().includes(term)
      );
    }
    if (reqFilter !== 'all') {
      reqs = reqs.filter(r => r.category === reqFilter);
    }
    return reqs;
  }, [document, reqSearch, reqFilter]);

  const groupedRequirements = useMemo(() => {
    if (!processedRequirements.length) return {};
    if (reqGroupBy === 'module') {
      const groups = {};
      processedRequirements.forEach(r => {
        const key = r.module_name || 'General';
        if (!groups[key]) groups[key] = [];
        groups[key].push(r);
      });
      return groups;
    } else if (reqGroupBy === 'category') {
      const groups = {};
      processedRequirements.forEach(r => {
        const key = r.category || 'uncategorized';
        if (!groups[key]) groups[key] = [];
        groups[key].push(r);
      });
      return groups;
    } else {
      return { 'All Requirements': processedRequirements };
    }
  }, [processedRequirements, reqGroupBy]);

  const reqStats = useMemo(() => {
    if (!document?.requirements) return null;
    const reqs = document.requirements;
    const total = reqs.length;
    const byCategory = {};
    const withVagueTerms = reqs.filter(r => r.vague_terms?.length > 0).length;
    const enriched = reqs.filter(r => r.category).length;
    reqs.forEach(r => {
      const cat = r.category || 'uncategorized';
      byCategory[cat] = (byCategory[cat] || 0) + 1;
    });
    return { total, byCategory, withVagueTerms, enriched };
  }, [document]);

  const highlightText = (text, req) => {
    if (!text) return text;
    const modalRegex = new RegExp(`\\b(${Object.keys(MODAL_VERB_COLORS).join('|')})\\b`, 'gi');
    const vaguePattern = (req.vague_terms || []).map(vt => vt.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    const parts = text.split(new RegExp(`(${modalRegex.source}|${vaguePattern ? `\\b(${vaguePattern})\\b` : ''})`, 'gi'));
    
    return parts.map((part, i) => {
      if (!part) return null;
      const lower = part.toLowerCase();
      if (MODAL_VERB_COLORS[lower]) {
        return <span key={i} className={MODAL_VERB_COLORS[lower]}>{part}</span>;
      }
      if ((req.vague_terms || []).some(vt => vt.toLowerCase() === lower)) {
        return <span key={i} className="bg-amber-200 text-amber-900 px-1 rounded font-medium" title="Vague Term">{part}</span>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-[var(--primary-main)] animate-spin" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <div className="text-center">
          <FileText className="h-12 w-12 text-[var(--text-secondary)] mx-auto mb-4" />
          <p className="text-[var(--text-secondary)]">Document not found</p>
        </div>
      </div>
    );
  }

  const defects = validation?.defects || [];
  const requirements = document.requirements || [];
  const overallScore = validation?.overall_score ?? null;
  const hasValidation = validation?.status === 'completed';

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div className="flex items-center">
              <Link to="/documents" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] mr-4">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">Analysis Results</h1>
                <p className="text-[var(--text-secondary)]">{document.filename}</p>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {/* Organization is now automatic when document loads */}
              {hasValidation && (
                <button className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
                  <Download className="h-4 w-4 mr-2" /> Export Report
                </button>
              )}
              {!hasValidation && !isValidating && (
                <button onClick={handleRunValidation}
                  className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
                  <Play className="h-4 w-4 mr-2" /> Run Validation
                </button>
              )}
              {isValidating && (
                <button disabled className="flex items-center px-4 py-2 bg-[var(--surface-bg)] text-[var(--text-secondary)] rounded-lg cursor-not-allowed">
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Processing...
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Document Info Card */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center">
              <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                <FileText className="h-6 w-6 text-[var(--text-secondary)]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">{document.filename}</h2>
                <div className="flex items-center text-sm text-[var(--text-secondary)] mt-1 flex-wrap gap-1">
                  <span>Size: {(document.file_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                  <span className="mx-2">•</span>
                  <span>Words: {document.word_count || 0}</span>
                  <span className="mx-2">•</span>
                  <span>Requirements: {requirements.length}</span>
                  {isEnriched && (
                    <>
                      <span className="mx-2">•</span>
                      <span className="text-green-600 font-medium flex items-center">
                        <CheckCircle className="h-3 w-3 mr-1" /> Organized
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              {hasValidation ? (
                <>
                  <div className="text-center">
                    <div className="flex items-center justify-center">
                      <TrendingUp className="h-5 w-5 text-[var(--text-secondary)] mr-1" />
                      <span className="text-2xl font-bold text-[var(--text-primary)]">{overallScore?.toFixed(0) ?? '--'}%</span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)]">Quality Score</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center">
                      <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-1" />
                      <span className="text-2xl font-bold text-[var(--text-primary)]">{validation.total_defects}</span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)]">Defects Found</p>
                  </div>
                </>
              ) : (
                <div className="text-center">
                  <div className="flex items-center justify-center">
                    <Clock className="h-5 w-5 text-[var(--text-secondary)] mr-1" />
                    <span className="text-lg font-medium text-[var(--text-secondary)]">Not Validated</span>
                  </div>
                  <p className="text-xs text-[var(--text-secondary)]">Run validation to see results</p>
                </div>
              )}
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                document.status === 'ready' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                document.status === 'uploading' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                'bg-[var(--error-light)] text-[var(--error-hover)]'
              }`}>
                {document.status === 'ready' ? <CheckCircle className="h-4 w-4 mr-1" /> :
                 document.status === 'uploading' ? <Clock className="h-4 w-4 mr-1" /> :
                 <XCircle className="h-4 w-4 mr-1" />}
                <span className="capitalize">{document.status}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Perfect Score Banner */}
        {validation?.perfect_score && (
          <div className="mb-6 bg-[var(--success-light)]/20 border border-[var(--success-main)] rounded-xl p-6 flex items-center">
            <ShieldCheck className="h-8 w-8 text-[var(--success-main)] mr-4" />
            <div>
              <h3 className="text-lg font-semibold text-[var(--success-main)]">Perfect Score</h3>
              <p className="text-sm text-[var(--text-secondary)]">No defects were detected in this document. The requirements appear to be well-written and clear.</p>
            </div>
          </div>
        )}

        {/* Tabs Content */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm border border-[var(--card-border)] overflow-hidden mb-6">
          <div className="border-b border-[var(--card-border)]">
            <nav className="flex space-x-8 px-6">
              <button onClick={() => setActiveTab('findings')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'findings' ? 'border-[var(--primary-main)] text-[var(--text-primary)]' : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
                Analysis Findings
              </button>
              <button onClick={() => setActiveTab('requirements')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'requirements' ? 'border-[var(--primary-main)] text-[var(--text-primary)]' : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
                Requirements {requirements.length > 0 && <span className="ml-1 text-xs bg-[var(--surface-bg)] px-2 py-0.5 rounded-full">{requirements.length}</span>}
              </button>
            </nav>
          </div>

          <div className="p-6">
            
            {/* FINDINGS TAB */}
            {activeTab === 'findings' && (
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Analysis Findings</h3>
                {!hasValidation ? (
                  <div className="text-center py-12">
                    <BarChart3 className="h-12 w-12 text-[var(--text-secondary)] mx-auto mb-4" />
                    <p className="text-[var(--text-secondary)] mb-4">No validation has been run yet.</p>
                    <button onClick={handleRunValidation} disabled={isValidating}
                      className="bg-[var(--primary-main)] text-white px-6 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50">
                      {isValidating ? 'Processing...' : 'Run Validation'}
                    </button>
                  </div>
                ) : defects.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-[var(--success-main)] mx-auto mb-4" />
                    <p className="text-[var(--success-main)] font-medium">No defects found!</p>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">This document passed all quality checks.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {defects.map((finding, index) => (
                      <div key={index}
                        className={`border-l-4 p-6 rounded-lg ${
                          finding.severity === 'high' ? 'border-[var(--error-main)] bg-[var(--error-light)]/20' :
                          finding.severity === 'medium' ? 'border-[var(--warning-main)] bg-[var(--warning-light)]/20' :
                          'border-[var(--success-main)] bg-[var(--success-light)]/20'
                        }`}>
                        <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start gap-3 mb-3">
                              <h4 className="font-medium text-[var(--text-primary)] text-lg">{finding.type?.charAt(0).toUpperCase() + finding.type?.slice(1)}</h4>
                              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                                finding.severity === 'high' ? 'bg-[var(--error-light)] text-[var(--error-main)]' :
                                finding.severity === 'medium' ? 'bg-[var(--warning-light)] text-[var(--warning-main)]' :
                                'bg-[var(--success-light)] text-[var(--success-main)]'
                              }`}>
                                {finding.severity === 'high' ? <AlertOctagon className="h-4 w-4 mr-2" /> :
                                 finding.severity === 'medium' ? <AlertTriangle className="h-4 w-4 mr-2" /> :
                                 <CheckCircle className="h-4 w-4 mr-2" />}
                                {finding.severity}
                              </span>
                            </div>
                            <p className="text-[var(--text-secondary)] leading-relaxed">{finding.description}</p>
                            
                            <div className="flex flex-wrap items-center gap-3 mt-3">
                              {finding.confidence && (
                                <span className="inline-flex items-center text-sm bg-gray-100 text-gray-700 px-3 py-1.5 rounded-md">
                                  <span className="font-medium">Confidence:</span> {(finding.confidence * 100).toFixed(0)}%
                                </span>
                              )}
                              <span className="inline-flex items-center text-sm bg-[var(--surface-bg)] px-3 py-1.5 rounded-md border border-[var(--card-border)]">
                                <span className="font-medium">Linked ID:</span> 
                                <span className="font-mono ml-1">{finding.req_id ? finding.req_id.split('-')[0] : 'N/A'}</span>
                              </span>
                              {finding.suggestion && (
                                <span className="inline-flex items-center text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-md">
                                  AI Suggestion available
                                </span>
                              )}
                            </div>
                            {finding.text && (
                              <div className="mt-3 p-3 bg-[var(--surface-bg)] rounded-lg border border-[var(--card-border)]">
                                <h5 className="text-sm font-medium text-[var(--text-secondary)] mb-1">Requirement Statement</h5>
                                <p className="text-sm text-[var(--text-primary)] italic">"{finding.text}"</p>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-3 lg:ml-4 mt-4 lg:mt-0">
                            <button onClick={() => setExpandedFinding(expandedFinding === index ? null : index)}
                              className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors p-2 rounded-lg hover:bg-[var(--surface-bg)]">
                              <Eye className="h-5 w-5" />
                            </button>
                          </div>
                        </div>
                        {expandedFinding === index && (
                          <div className="mt-4 pt-4 border-t border-[var(--card-border)]">
                            <div className="bg-[var(--surface-bg)] p-4 rounded-lg">
                              <h5 className="font-medium text-[var(--text-primary)] mb-2">Details</h5>
                              <p className="text-sm text-[var(--text-secondary)] mb-3">{finding.description}</p>
                              <div className="grid grid-cols-2 gap-4 text-sm">
                                <div><span className="font-medium text-[var(--text-secondary)]">Type:</span> <span className="ml-2 capitalize">{finding.type}</span></div>
                                <div><span className="font-medium text-[var(--text-secondary)]">Severity:</span> <span className="ml-2 capitalize">{finding.severity}</span></div>
                                <div><span className="font-medium text-[var(--text-secondary)]">Requirement ID:</span> <span className="ml-2">{finding.req_id ? finding.req_id.split('-')[0] : 'N/A'}</span></div>
                                <div><span className="font-medium text-[var(--text-secondary)]">Confidence:</span> <span className="ml-2">{(finding.confidence * 100).toFixed(0)}%</span></div>
                              </div>
                              {finding.suggestion && (
                                <div className="mt-3">
                                  <span className="font-medium text-[var(--text-secondary)]">AI Suggestion:</span>
                                  <p className="text-sm text-[var(--text-primary)] mt-1">{finding.suggestion}</p>
                                </div>
                              )}
                              <div className="mt-4 flex space-x-3">
                                <button onClick={() => handleApplySuggestion(index)}
                                  className="px-3 py-1.5 bg-[var(--success-main)] text-white rounded-lg hover:bg-[var(--success-hover)] transition-colors text-sm">
                                  Apply Suggestion
                                </button>
                                <button onClick={() => handleIgnoreFinding(index)}
                                  className="px-3 py-1.5 bg-[var(--surface-bg)] text-[var(--text-primary)] rounded-lg hover:bg-[var(--card-border)] transition-colors text-sm border border-[var(--card-border)]">
                                  Ignore
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* REQUIREMENTS TAB */}
            {activeTab === 'requirements' && (
              <div>
                <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">System Requirements</h3>
                  {/* Categories and filters are now automatically enabled */}
                </div>

                {/* Summary Cards */}
                {reqStats && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-[var(--surface-bg)] rounded-lg p-4 border border-[var(--card-border)]">
                      <div className="text-2xl font-bold text-[var(--text-primary)]">{reqStats.total}</div>
                      <div className="text-xs text-[var(--text-secondary)]">Total Requirements</div>
                    </div>
                    {Object.entries(reqStats.byCategory).slice(0, 3).map(([cat, count]) => {
                      const config = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.uncategorized;
                      return (
                        <div key={cat} className="bg-[var(--surface-bg)] rounded-lg p-4 border border-[var(--card-border)]">
                          <div className="text-2xl font-bold text-[var(--text-primary)]">{count}</div>
                          <div className="text-xs flex items-center">
                            <span className="mr-1">{config.icon}</span>
                            <span className="text-[var(--text-secondary)]">{config.label}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Filter and Search Bar */}
                <div className="flex items-center gap-3 mb-6 flex-wrap">
                  <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                    <input type="text" placeholder="Search requirements..." value={reqSearch} onChange={e => setReqSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2 bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)]" />
                  </div>
                  <select value={reqFilter} onChange={e => setReqFilter(e.target.value)} className="px-3 py-2 bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg text-sm">
                    <option value="all">All Categories</option>
                    {Object.entries(CATEGORY_CONFIG).map(([key, c]) => (
                      <option key={key} value={key}>{c.label}</option>
                    ))}
                  </select>
                  <select value={reqGroupBy} onChange={e => setReqGroupBy(e.target.value)} className="px-3 py-2 bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg text-sm">
                    <option value="module">Group by Module</option>
                    <option value="category">Group by Category</option>
                    <option value="none">No Grouping (Flat List)</option>
                  </select>
                </div>

                {/* Grouped Requirements Render */}
                {Object.keys(groupedRequirements).length === 0 ? (
                  <div className="text-center py-8 text-[var(--text-secondary)]">No requirements match your filters.</div>
                ) : (
                  Object.entries(groupedRequirements).map(([groupName, reqs]) => (
                    <div key={groupName} className="mb-4 border border-[var(--card-border)] rounded-lg overflow-hidden bg-white">
                      <button onClick={() => toggleModule(groupName)} className="w-full flex items-center justify-between px-4 py-3 bg-[var(--surface-bg)] hover:bg-[var(--surface-bg)]/80 transition-colors">
                        <div className="flex items-center">
                          <ChevronRight className={`h-4 w-4 mr-2 transition-transform ${expandedModules[groupName] ? 'rotate-90' : ''}`} />
                          <span className="font-semibold text-[var(--text-primary)] capitalize">{groupName.replace(/_/g, ' ')}</span>
                          <span className="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full">{reqs.length}</span>
                        </div>
                      </button>
                      
                      {expandedModules[groupName] !== false && (
                        <div className="divide-y divide-[var(--card-border)]">
                          {reqs.map(req => {
                            const catConfig = CATEGORY_CONFIG[req.category] || CATEGORY_CONFIG.uncategorized;
                            const statusConfig = VALIDATION_STATUS_CONFIG[req.validation_status] || VALIDATION_STATUS_CONFIG.pending;
                            const StatusIcon = statusConfig.icon;

                            return (
                              <div key={req.req_id} className="p-4 hover:bg-[var(--surface-bg)]/30 transition-colors">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="flex-1">
                                    {/* Top Row: Badges & Tags */}
                                    <div className="flex items-center gap-2 flex-wrap mb-2">
                                      {req.semantic_id && (
                                        <span className="text-xs font-mono font-bold text-[var(--primary-main)] bg-[var(--primary-light)]/20 px-2 py-0.5 rounded border border-[var(--primary-light)]">
                                          {req.semantic_id}
                                        </span>
                                      )}
                                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${catConfig.color}`}>
                                        <span className="mr-1">{catConfig.icon}</span> {catConfig.label}
                                      </span>
                                      
                                      {req.actors?.map((actor, idx) => (
                                        <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700 border border-indigo-100">
                                          <Users className="h-3 w-3 mr-1" /> {actor}
                                        </span>
                                      ))}
                                    </div>
                                    
                                    {/* Requirement Text */}
                                    <div className="text-sm text-[var(--text-primary)] leading-relaxed">
                                      {highlightText(req.original_text, req)}
                                    </div>
                                  </div>

                                  {/* Right Side: Status Icon */}
                                  <div className="flex-shrink-0 flex items-center justify-center mt-1">
                                    <div className={`flex flex-col items-center ${statusConfig.color}`} title={`Validation: ${statusConfig.label}`}>
                                      <StatusIcon className="h-5 w-5 mb-1" />
                                      <span className="text-[10px] font-medium uppercase tracking-wider">{statusConfig.label}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults;