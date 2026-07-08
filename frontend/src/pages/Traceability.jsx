import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ArrowUpDown,
  BadgeCheck,
  ChevronLeft,
  ChevronRight,
  Clock3,
  ExternalLink,
  Eye,
  Filter,
  MessageSquare,
  Search,
  Sparkles,
  X,
} from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { projectAPI, traceabilityAPI } from '../services/api';
import { toast } from 'sonner';

const ITEMS_PER_PAGE_OPTIONS = [10, 15, 20];

const sanitizeText = (value) => {
  if (!value) return '';

  return String(value)
    .replace(/\\u[0-9a-f]{4}/gi, ' ')
    .replace(/\\uc0\\u\d+/gi, ' ')
    .replace(/\buc\d+\b/gi, ' ')
    .replace(/\bu\d{3,}\b/gi, ' ')
    .replace(/\\'..?/g, '')
    .replace(/\\r\\n|\\n|\\t/g, ' ')
    .replace(/\\(?!n|r|t)/g, ' ')
    .replace(/\r\n|\r|\n/g, ' ')
    .replace(/[#{*_`>~]+/g, ' ')
    .replace(/\b(par|pard|plain|cf\d+|f\d+|fs\d+)\b/gi, ' ')
    .replace(/###\s*/g, '')
    .replace(/\{\s*"text"\s*:\s*"/gi, '')
    .replace(/\"\s*\}/g, '')
    .replace(/\"/g, '')
    .replace(/^\s*(?:N?FR)\b[\s:_-]*(?:[A-Z]{2,}(?:[\s_-]*\d+)*)?\s*[:.-]?\s*/i, '')
    .replace(/\s+-\s+/g, ' - ')
    .replace(/\s+/g, ' ')
    .trim();
};

const normalizeStatus = (value) => {
  const status = String(value || 'unknown').toLowerCase();

  if (['passed', 'valid', 'ok', 'success'].includes(status)) return 'passed';
  if (['warning', 'ambiguous', 'partial'].includes(status)) return 'warning';
  if (['failed', 'defective', 'conflict', 'error'].includes(status)) return 'failed';
  return 'unknown';
};

const normalizeComplexity = (value) => {
  const complexity = String(value || 'medium').toLowerCase();

  if (['high', 'h'].includes(complexity)) return 'high';
  if (['low', 'l'].includes(complexity)) return 'low';
  return 'medium';
};

const parseMappedNodes = (value) => {
  if (!value) return [];

  const rawItems = Array.isArray(value)
    ? value
    : String(value)
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

  return rawItems.map((item) => {
    const [kindPart, ...labelParts] = item.split(':');
    const kind = (labelParts.length > 0 ? kindPart : 'node').trim().toLowerCase();
    const label = (labelParts.length > 0 ? labelParts.join(':') : kindPart).trim();

    return { label, kind, raw: item };
  });
};

const statusBadge = (status) => {
  switch (normalizeStatus(status)) {
    case 'passed':
      return { bg: 'bg-[var(--success-light)]', text: 'text-[var(--success-hover)]', ring: 'ring-[var(--success-light)]', label: 'Passed', icon: BadgeCheck };
    case 'warning':
      return { bg: 'bg-[var(--warning-light)]', text: 'text-[var(--warning-hover)]', ring: 'ring-[var(--warning-light)]', label: 'Warning', icon: AlertTriangle };
    case 'failed':
      return { bg: 'bg-[var(--error-light)]', text: 'text-[var(--error-hover)]', ring: 'ring-[var(--error-light)]', label: 'Failed', icon: AlertOctagon };
    default:
      return { bg: 'bg-[var(--surface-bg)]', text: 'text-[var(--text-secondary)]', ring: 'ring-[var(--card-border)]', label: 'Unknown', icon: Clock3 };
  }
};

const complexityBadge = (complexity) => {
  switch (normalizeComplexity(complexity)) {
    case 'high':
      return { bg: 'bg-[var(--error-light)]', text: 'text-[var(--error-hover)]', label: 'High' };
    case 'low':
      return { bg: 'bg-[var(--success-light)]', text: 'text-[var(--success-hover)]', label: 'Low' };
    default:
      return { bg: 'bg-[var(--warning-light)]', text: 'text-[var(--warning-hover)]', label: 'Medium' };
  }
};

const chipTone = (kind) => {
  const normalized = String(kind || '').toLowerCase();

  if (normalized.includes('actor')) return 'bg-sky-100 text-sky-700 ring-sky-200';
  if (normalized.includes('use case')) return 'bg-violet-100 text-violet-700 ring-violet-200';
  if (normalized.includes('system')) return 'bg-emerald-100 text-emerald-700 ring-emerald-200';
  return 'bg-slate-100 text-slate-700 ring-slate-200';
};

const Traceability = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(id || '');
  const [requirements, setRequirements] = useState([]);
  const [defects, setDefects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterComplexity, setFilterComplexity] = useState('all');
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewRequirement, setViewRequirement] = useState(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await projectAPI.getAll();
        const loadedProjects = response.data || [];
        setProjects(loadedProjects);

        if (!id && !selectedProjectId && loadedProjects.length > 0) {
          const preferredProject = [...loadedProjects].sort((left, right) => {
            const leftRequirements = Number(right?.requirements_count || 0) - Number(left?.requirements_count || 0);
            if (leftRequirements !== 0) return leftRequirements;

            const leftDate = left?.created_at ? new Date(left.created_at).getTime() : 0;
            const rightDate = right?.created_at ? new Date(right.created_at).getTime() : 0;
            return rightDate - leftDate;
          })[0];

          const projectId = preferredProject?.project_id || preferredProject?.id;
          if (projectId) {
            setSelectedProjectId(projectId);
          }
        }
      } catch (error) {
        console.error('Failed to load projects:', error);
        toast.error('Failed to load projects');
      }
    };

    loadProjects();
  }, []);

  useEffect(() => {
    const loadTraceabilityData = async () => {
      const activeProjectId = id || selectedProjectId;

      if (!activeProjectId) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);

      try {
        const response = await traceabilityAPI.getTraceability(activeProjectId);

        if (response.data?.error) {
          toast.error(`Error: ${response.data.error}`);
          return;
        }

        if (response.data?.traceability) {
          setRequirements(
            response.data.traceability.map((item) => ({
              id: item.req_id,
              doc_id: item.doc_id,
              identifier: item.identifier,
              text: item.text,
              status: item.validation_status || 'valid',
              visualElements: item.visual_elements || [],
              complexity: item.complexity || 'Medium',
              notes: item.note ? [item.note] : [],
              hasNotes: !!item.note,
              timestamp: new Date().toLocaleDateString(),
            })),
          );
          setDefects([]);
        }

        if (response.data?.project) {
          setSelectedProject(response.data.project);
        }
      } catch (error) {
        console.error('Failed to load traceability data:', error);

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
  }, [id, selectedProjectId]);

  const traceabilityData = useMemo(() => {
    return requirements.map((req, index) => {
      const associatedDefect = defects.find((defect) =>
        defect.requirement_id === req.id || defect.req_id === `REQ-${String(req.id || index + 1).padStart(3, '0')}`,
      );

      const identifier = req.identifier || `REQ-${String(index + 1).padStart(3, '0')}`;
      const visualElements = parseMappedNodes(req.visualElements || ['Actor: User', 'Use Case: Login']);
      const requirementText = sanitizeText(req.text) || `Requirement ${index + 1}`;

      return {
        id: req.id || `req-${index + 1}`,
        identifier,
        docId: req.doc_id || req.docId || null,
        requirement: requirementText,
        rawRequirement: req.text || '',
        status: normalizeStatus(associatedDefect ? 'failed' : req.status),
        visualElements,
        complexity: normalizeComplexity(req.complexity),
        hasNotes: req.notes && req.notes.length > 0,
        notes: req.notes || [],
        timestamp: req.timestamp,
        defectId: associatedDefect?.id,
      };
    });
  }, [requirements, defects]);

  const filteredData = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return traceabilityData.filter((item) => {
      const matchesSearch =
        !query ||
        item.identifier.toLowerCase().includes(query) ||
        item.requirement.toLowerCase().includes(query) ||
        item.visualElements.some((node) => node.raw.toLowerCase().includes(query) || node.label.toLowerCase().includes(query));

      const matchesStatus = filterStatus === 'all' || normalizeStatus(item.status) === filterStatus;
      const matchesComplexity = filterComplexity === 'all' || normalizeComplexity(item.complexity) === filterComplexity;

      return matchesSearch && matchesStatus && matchesComplexity;
    });
  }, [traceabilityData, searchTerm, filterStatus, filterComplexity]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / itemsPerPage));
  const paginatedData = filteredData.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, filterStatus, filterComplexity, itemsPerPage]);

  useEffect(() => {
    setCurrentPage((page) => Math.min(page, totalPages));
  }, [totalPages]);

  const summary = useMemo(() => {
    return traceabilityData.reduce(
      (accumulator, item) => {
        accumulator.total += 1;
        accumulator[item.status] = (accumulator[item.status] || 0) + 1;
        if (item.hasNotes) accumulator.notes += 1;
        return accumulator;
      },
      { total: 0, passed: 0, warning: 0, failed: 0, unknown: 0, notes: 0 },
    );
  }, [traceabilityData]);

  const handleAddNote = (requirement) => {
    setSelectedRequirement(requirement);
    setNoteText('');
    setShowNotesModal(true);
  };

  const handleViewRequirement = (requirement) => {
    setViewRequirement(requirement);
    setShowViewModal(true);
  };

  const handleViewNode = (requirement, node) => {
    const normalizedKind = String(node?.kind || '').toLowerCase();
    const preferredDiagram = normalizedKind.includes('actor') || normalizedKind.includes('use case')
      ? 'usecase'
      : 'sequence';

    const targetDocumentId = requirement?.docId || '';
    const basePath = targetDocumentId ? `/visualization/${targetDocumentId}` : '/visualization';
    const search = new URLSearchParams({
      highlight: node.label,
      nodeType: normalizedKind || 'node',
      diagram: preferredDiagram,
      source: 'traceability',
    });

    window.open(`${basePath}?${search.toString()}`, '_blank', 'noopener,noreferrer');
    toast.success(`Opening visualization for ${node.label}`);
  };

  const activeProjectId = id || selectedProjectId;
  const activeProject = selectedProject || projects.find((project) => {
    const projectId = project.project_id || project.id;
    return projectId === activeProjectId;
  }) || null;

  const handleSaveNote = async () => {
    if (!selectedRequirement || !noteText.trim()) return;

    try {
      await traceabilityAPI.saveNote({ req_id: selectedRequirement.id, content: noteText.trim() });
      toast.success('Note saved successfully!');
      setShowNotesModal(false);
      setSelectedRequirement(null);
      setNoteText('');

      const response = await traceabilityAPI.getTraceability(id);
      if (response.data?.traceability) {
        setRequirements(
          response.data.traceability.map((item) => ({
            id: item.req_id,
            doc_id: item.doc_id,
            identifier: item.identifier,
            text: item.text,
            status: item.validation_status || 'valid',
            visualElements: item.visual_elements || [],
            complexity: item.complexity || 'Medium',
            notes: item.note ? [item.note] : [],
            hasNotes: !!item.note,
            timestamp: new Date().toLocaleDateString(),
          })),
        );
      }
    } catch (error) {
      console.error('Failed to save note:', error);
      toast.error(`Failed to save note: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-main)] mx-auto" />
          <p className="mt-4 text-[var(--text-secondary)]">Loading traceability data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <section className="rounded-3xl border border-[var(--card-border)] bg-gradient-to-br from-white via-[var(--card-bg)] to-[var(--primary-50)] shadow-[0_20px_70px_rgba(37,99,235,0.08)] p-6 sm:p-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-3 max-w-3xl">
                <div className="inline-flex items-center gap-2 rounded-full bg-[var(--primary-50)] px-3 py-1 text-xs font-semibold text-[var(--primary-dark)] ring-1 ring-[var(--info-light)]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Analyst Dashboard
                </div>
                <div>
                  <h1 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)] tracking-tight">Inspect Requirements Traceability</h1>
                  <p className="mt-2 max-w-2xl text-[var(--text-secondary)]">
                    Clean, filterable traceability with mapped UML nodes, note tracking, and a compact analyst-style review flow.
                  </p>
                  <div className="mt-4 flex flex-wrap items-center gap-2 text-sm text-[var(--text-secondary)]">
                    <span className="font-medium text-[var(--text-primary)]">Active project:</span>
                    {activeProject ? (
                      <span className="inline-flex items-center rounded-full bg-[var(--primary-50)] px-3 py-1 font-semibold text-[var(--primary-dark)] ring-1 ring-[var(--info-light)]">
                        {activeProject.name || activeProject.project_name || activeProjectId || 'Unknown'}
                      </span>
                    ) : (
                      <span>No project selected</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3 w-full lg:w-auto">
                {[
                  { label: 'Total', value: summary.total, tone: 'text-[var(--text-primary)]' },
                  { label: 'Passed', value: summary.passed, tone: 'text-[var(--success-hover)]' },
                  { label: 'Warning', value: summary.warning, tone: 'text-[var(--warning-hover)]' },
                  { label: 'Failed', value: summary.failed, tone: 'text-[var(--error-hover)]' },
                  { label: 'With notes', value: summary.notes, tone: 'text-[var(--primary-dark)]' },
                ].map((metric) => (
                  <div key={metric.label} className="rounded-2xl border border-[var(--card-border)] bg-white/80 px-4 py-3 shadow-sm backdrop-blur-sm">
                    <p className="text-xs uppercase tracking-[0.18em] text-[var(--text-secondary)]">{metric.label}</p>
                    <p className={`mt-2 text-2xl font-semibold ${metric.tone}`}>{metric.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {!id && (
            <section className="rounded-3xl border border-[var(--card-border)] bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">Select Project for Traceability Analysis</h3>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">Switch projects to inspect different traceability matrices.</p>
                </div>
                <p className="text-sm text-[var(--text-secondary)]">
                  {activeProjectId ? 'Loaded the most relevant project automatically.' : 'Choose a project below.'}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <div
                    key={project.project_id || project.id}
                    className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                      (project.project_id || project.id) === activeProjectId
                        ? 'border-[var(--primary-main)] bg-[var(--primary-50)] ring-1 ring-[var(--info-light)]'
                        : 'border-[var(--card-border)] hover:border-[var(--primary-main)] hover:bg-[var(--primary-50)]'
                    }`}
                    onClick={() => {
                      const projectId = project.project_id || project.id;
                      if (!projectId) {
                        toast.error('Invalid project: Missing project ID');
                        return;
                      }
                      setSelectedProjectId(projectId);
                      setSelectedProject(project);
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
                  <div className="h-12 w-12 bg-[var(--neutral-200)] rounded-2xl mx-auto mb-4 flex items-center justify-center">
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
            </section>
          )}

          {activeProjectId && (
            <section className="rounded-3xl border border-[var(--card-border)] bg-white shadow-sm p-4 sm:p-5">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 flex-1">
                  <div className="relative xl:col-span-2">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <input
                      type="text"
                      placeholder="Search REQ-ID, keyword, or mapped node..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] py-3 pl-10 pr-4 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--primary-main)] focus:ring-2 focus:ring-[var(--primary-50)]"
                    />
                  </div>

                  <div className="relative">
                    <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <select
                      value={filterStatus}
                      onChange={(e) => setFilterStatus(e.target.value)}
                      className="w-full appearance-none rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] py-3 pl-10 pr-4 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--primary-main)] focus:ring-2 focus:ring-[var(--primary-50)]"
                    >
                      <option value="all">All Statuses</option>
                      <option value="passed">Passed</option>
                      <option value="warning">Warning</option>
                      <option value="failed">Failed</option>
                    </select>
                  </div>

                  <div className="relative">
                    <ArrowUpDown className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-secondary)]" />
                    <select
                      value={filterComplexity}
                      onChange={(e) => setFilterComplexity(e.target.value)}
                      className="w-full appearance-none rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] py-3 pl-10 pr-4 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--primary-main)] focus:ring-2 focus:ring-[var(--primary-50)]"
                    >
                      <option value="all">All Complexity</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] px-4 py-3 text-sm text-[var(--text-secondary)]">
                    Showing <span className="font-semibold text-[var(--text-primary)]">{filteredData.length}</span> result(s)
                  </div>
                  <div className="flex items-center gap-2 rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] px-4 py-3">
                    <span className="text-sm text-[var(--text-secondary)]">Rows</span>
                    <select
                      value={itemsPerPage}
                      onChange={(e) => setItemsPerPage(Number(e.target.value))}
                      className="bg-transparent text-sm font-medium text-[var(--text-primary)] outline-none"
                    >
                      {ITEMS_PER_PAGE_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </section>
          )}

          {activeProjectId && (
            <section className="rounded-3xl border border-[var(--card-border)] bg-white shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-[var(--card-border)]">
                  <thead className="bg-[var(--surface-bg)]/80">
                    <tr>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">REQ-ID</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Requirement</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Status</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Mapped UML Nodes</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Complexity</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Notes</th>
                      <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--card-border)] bg-white">
                    {paginatedData.length > 0 ? (
                      paginatedData.map((item) => {
                        const status = statusBadge(item.status);
                        const complexity = complexityBadge(item.complexity);

                        return (
                          <tr key={item.id} className="align-top hover:bg-[var(--primary-50)]/40 transition-colors">
                            <td className="px-5 py-4 whitespace-nowrap text-sm font-semibold text-[var(--primary-dark)]">{item.identifier}</td>

                            <td className="px-5 py-4">
                              <div className="max-w-xl">
                                <p className="line-clamp-2 text-sm leading-6 text-[var(--text-primary)]" title={item.requirement}>
                                  {item.requirement}
                                </p>
                              </div>
                            </td>

                            <td className="px-5 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${status.bg} ${status.text} ${status.ring}`}>
                                <status.icon className="h-3.5 w-3.5" />
                                {status.label}
                              </span>
                            </td>

                            <td className="px-5 py-4">
                              <div className="flex flex-wrap gap-2">
                                {item.visualElements.length > 0 ? (
                                  item.visualElements.map((node) => (
                                    <button
                                      key={`${item.id}-${node.raw}`}
                                      type="button"
                                      onClick={() => handleViewNode(item, node)}
                                      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 transition hover:scale-[1.01] ${chipTone(node.kind)}`}
                                      title={`Open highlight for ${node.raw}`}
                                    >
                                      {node.kind && <span className="opacity-80">{node.kind}</span>}
                                      <span>{node.label}</span>
                                      <ExternalLink className="h-3 w-3" />
                                    </button>
                                  ))
                                ) : (
                                  <span className="text-sm text-[var(--text-secondary)]">-</span>
                                )}
                              </div>
                            </td>

                            <td className="px-5 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${complexity.bg} ${complexity.text}`}>{complexity.label}</span>
                            </td>

                            <td className="px-5 py-4 whitespace-nowrap">
                              {item.hasNotes ? (
                                <button
                                  type="button"
                                  onClick={() => handleViewRequirement(item)}
                                  className="inline-flex items-center gap-2 rounded-full bg-[var(--surface-bg)] px-3 py-1.5 text-xs font-semibold text-[var(--text-primary)] transition hover:bg-[var(--primary-50)]"
                                >
                                  <span className="relative inline-flex">
                                    <MessageSquare className="h-4 w-4 text-[var(--primary-main)]" />
                                    <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-[var(--error)]" />
                                  </span>
                                  {item.notes.length} note(s)
                                </button>
                              ) : (
                                <span className="text-sm text-[var(--text-secondary)]">No notes</span>
                              )}
                            </td>

                            <td className="px-5 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleViewRequirement(item)}
                                  className="inline-flex items-center gap-2 rounded-full border border-[var(--primary-100)] bg-[var(--primary-50)] px-3.5 py-2 text-xs font-semibold text-[var(--primary-dark)] shadow-sm transition hover:border-[var(--primary-main)] hover:bg-[var(--primary-100)] hover:text-[var(--primary-main)]"
                                  title="View details"
                                >
                                  <Eye className="h-4 w-4" />
                                  View
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleAddNote(item)}
                                  className="relative inline-flex items-center gap-2 rounded-full border border-[var(--warning-light)] bg-[var(--warning-light)]/60 px-3.5 py-2 text-xs font-semibold text-[var(--warning-hover)] shadow-sm transition hover:border-[var(--warning-hover)] hover:bg-[var(--warning-light)] hover:text-[var(--warning-hover)]"
                                  title="Add note"
                                >
                                  <MessageSquare className="h-4 w-4" />
                                  Note
                                  {item.hasNotes && <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-[var(--error)]" />}
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan="7" className="px-6 py-14 text-center">
                          <div className="mx-auto flex max-w-sm flex-col items-center rounded-3xl border border-dashed border-[var(--card-border)] bg-[var(--surface-bg)] px-6 py-10">
                            <AlertTriangle className="h-10 w-10 text-[var(--warning-hover)]" />
                            <p className="mt-4 text-lg font-semibold text-[var(--text-primary)]">No requirements match your filters</p>
                            <p className="mt-1 text-sm text-[var(--text-secondary)]">Try a different keyword, status, or complexity filter.</p>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {filteredData.length > 0 && (
                <div className="flex flex-col gap-4 border-t border-[var(--card-border)] bg-[var(--surface-bg)] px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-[var(--text-secondary)]">
                    Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredData.length)} of {filteredData.length} requirements
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                      disabled={currentPage === 1}
                      className="inline-flex items-center gap-2 rounded-xl border border-[var(--card-border)] bg-white px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:border-[var(--primary-main)] hover:text-[var(--primary-main)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </button>
                    <span className="rounded-xl border border-[var(--card-border)] bg-white px-3 py-2 text-sm font-medium text-[var(--text-primary)]">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      type="button"
                      onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                      disabled={currentPage === totalPages}
                      className="inline-flex items-center gap-2 rounded-xl border border-[var(--card-border)] bg-white px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:border-[var(--primary-main)] hover:text-[var(--primary-main)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}

          {activeProjectId && (
            <section className="rounded-3xl border border-[var(--info-light)] bg-[var(--info-light)]/40 p-4">
              <div className="flex items-start gap-3">
                <MessageSquare className="mt-0.5 h-5 w-5 text-[var(--info-dark)]" />
                <div>
                  <h4 className="text-sm font-semibold text-[var(--info-dark)]">Traceability Matrix Information</h4>
                  <p className="mt-1 text-xs leading-5 text-[var(--info-dark)]">
                    Requirements are sanitized before display, mapped UML nodes are clickable, and the current page only shows the rows you need to inspect.
                  </p>
                </div>
              </div>
            </section>
          )}
        </div>
      </div>

      {showNotesModal && selectedRequirement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.55)] p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-3xl border border-[var(--card-border)] bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">Add Note</h3>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">Annotate the selected requirement for review.</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowNotesModal(false);
                  setNoteText('');
                  setSelectedRequirement(null);
                }}
                className="rounded-full p-2 text-[var(--text-secondary)] transition hover:bg-[var(--surface-bg)] hover:text-[var(--text-primary)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Requirement</p>
              <p className="mt-2 text-sm leading-6 text-[var(--text-primary)]">{selectedRequirement.requirement}</p>
            </div>

            <textarea
              placeholder="Enter your note here..."
              rows={5}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              className="mt-4 w-full resize-none rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none transition focus:border-[var(--primary-main)] focus:ring-2 focus:ring-[var(--primary-50)]"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleSaveNote();
                }
              }}
            />

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setShowNotesModal(false);
                  setNoteText('');
                  setSelectedRequirement(null);
                }}
                className="rounded-xl border border-[var(--card-border)] bg-white px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition hover:border-[var(--primary-main)] hover:text-[var(--primary-main)]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveNote}
                className="rounded-xl bg-[var(--primary-main)] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[var(--primary-hover)]"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {showViewModal && viewRequirement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.55)] p-4 backdrop-blur-sm">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-[var(--card-border)] bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">Requirement Details</h3>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">Full traceability record, notes, and mapped nodes.</p>
              </div>
              <button
                type="button"
                onClick={() => setShowViewModal(false)}
                className="rounded-full p-2 text-[var(--text-secondary)] transition hover:bg-[var(--surface-bg)] hover:text-[var(--text-primary)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">REQ-ID</p>
                <p className="mt-2 font-mono text-sm text-[var(--text-primary)]">{viewRequirement.identifier}</p>
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Status</p>
                {(() => {
                  const badge = statusBadge(viewRequirement.status);
                  return (
                    <span className={`mt-2 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${badge.bg} ${badge.text}`}>
                      <badge.icon className="h-3.5 w-3.5" />
                      {badge.label}
                    </span>
                  );
                })()}
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4 sm:col-span-2">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Requirement Text</p>
                <p className="mt-2 text-sm leading-6 text-[var(--text-primary)]">{viewRequirement.requirement}</p>
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4 sm:col-span-2">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Mapped UML Nodes</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {viewRequirement.visualElements.length > 0 ? (
                    viewRequirement.visualElements.map((node) => (
                      <span key={`${viewRequirement.id}-${node.raw}`} className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 ${chipTone(node.kind)}`}>
                        <span>{node.label}</span>
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-[var(--text-secondary)]">No mapped nodes available</span>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Complexity</p>
                <span className={`mt-2 inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${complexityBadge(viewRequirement.complexity).bg} ${complexityBadge(viewRequirement.complexity).text}`}>
                  {complexityBadge(viewRequirement.complexity).label}
                </span>
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Last Updated</p>
                <p className="mt-2 text-sm text-[var(--text-primary)]">{viewRequirement.timestamp}</p>
              </div>

              <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4 sm:col-span-2">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--text-secondary)]">Notes</p>
                <div className="mt-3 space-y-3">
                  {viewRequirement.notes && viewRequirement.notes.length > 0 ? (
                    viewRequirement.notes.map((note, index) => (
                      <div key={index} className="rounded-2xl border border-[var(--card-border)] bg-white p-3">
                        <p className="text-sm text-[var(--text-primary)]">{note.content || note}</p>
                        {note.updated_at && <p className="mt-1 text-xs text-[var(--text-secondary)]">Updated: {new Date(note.updated_at).toLocaleString()}</p>}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm italic text-[var(--text-secondary)]">No notes available</p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowViewModal(false)}
                className="rounded-xl border border-[var(--card-border)] bg-white px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition hover:border-[var(--primary-main)] hover:text-[var(--primary-main)]"
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
