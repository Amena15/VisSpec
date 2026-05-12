import { useState, useEffect, useCallback, useRef } from 'react';
import { documentAPI, projectAPI } from '../services/api';
import { toast } from 'sonner';

// Custom hook for dashboard data management
export const useDashboardData = () => {
  const [documents, setDocuments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    analyzedDocuments: 0,
    avgQualityScore: 0,
    totalDefects: 0,
    myProjects: 0,
    completedProjects: 0,
    inProgressProjects: 0,
    totalRequirements: 0,
    avgComplexity: 'Medium'
  });
  const [loading, setLoading] = useState({
    documents: false,
    projects: false,
    stats: false
  });
  const [error, setError] = useState({
    documents: null,
    projects: null,
    stats: null
  });

  // Cache management
  const cacheRef = useRef({
    documents: null,
    projects: null,
    timestamp: null,
    ttl: 5 * 60 * 1000 // 5 minutes cache
  });

  // Check if cache is valid
  const isCacheValid = useCallback(() => {
    const cache = cacheRef.current;
    return cache.timestamp && (Date.now() - cache.timestamp < cache.ttl);
  }, []);

  // Transform document data for display
  const transformDocument = useCallback((doc) => {
    return {
      id: doc.doc_id,
      title: doc.filename || 'Untitled Document',
      filename: doc.filename,
      uploadedAt: doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Unknown',
      updatedAt: doc.upload_date ? new Date(doc.upload_date).toLocaleDateString() : 'Unknown',
      status: doc.status || 'Ready for Analysis',
      qualityScore: doc.quality_score || Math.min(100, Math.max(0, Math.round((doc.word_count || 0) / 10))),
      complexity: doc.word_count > 1000 ? 'High' : doc.word_count > 500 ? 'Medium' : 'Low',
      defects: doc.defect_count || 0, // Real defect count from database validation
      effortEstimate: doc.word_count ? `${Math.ceil(doc.word_count / 200)}h` : 'Unknown',
      comments: doc.requirements_found ? `${doc.requirements_found} requirements found` : 'No comments',
      projectId: doc.project_id,
      wordCount: doc.word_count || 0,
      requirementsFound: doc.requirements_found || 0
    };
  }, []);

  // Transform project data for display
  const transformProject = useCallback((project) => {
    return {
      id: project.project_id,
      name: project.name,
      description: project.description,
      status: project.status,
      documentCount: project.document_count || 0,
      requirementsCount: project.requirements_count || 0,
      createdAt: project.created_at,
      updatedAt: project.updated_at
    };
  }, []);

  // Calculate statistics from data
  const calculateStats = useCallback((docs, projs) => {
    const completedDocs = docs.filter(d => d.status === 'completed' || d.status === 'Analyzed & Organized').length;
    const avgQualityScore = docs.length > 0 
      ? Math.round(docs.reduce((sum, doc) => sum + (doc.qualityScore || 0), 0) / docs.length)
      : 0;
    const totalDefects = docs.reduce((sum, doc) => sum + (doc.defects || 0), 0);
    const totalRequirements = docs.reduce((sum, doc) => sum + (doc.requirementsFound || 0), 0);

    // Determine average complexity
    const complexityScores = { Low: 1, Medium: 2, High: 3 };
    const avgComplexityValue = docs.length > 0 
      ? docs.reduce((sum, doc) => sum + (complexityScores[doc.complexity] || 2), 0) / docs.length
      : 2;
    const avgComplexity = avgComplexityValue < 1.5 ? 'Low' : avgComplexityValue > 2.5 ? 'High' : 'Medium';

    return {
      totalDocuments: docs.length,
      analyzedDocuments: completedDocs,
      avgQualityScore,
      totalDefects,
      myProjects: projs.length,
      completedProjects: projs.filter(p => p.status === 'completed').length,
      inProgressProjects: projs.filter(p => p.status === 'in-progress' || p.status === 'ready').length,
      totalRequirements,
      avgComplexity
    };
  }, []);

  // Load documents with caching
  const loadDocuments = useCallback(async (forceRefresh = false) => {
    if (!forceRefresh && isCacheValid() && cacheRef.current.documents) {
      setDocuments(cacheRef.current.documents.map(transformDocument));
      return;
    }

    setLoading(prev => ({ ...prev, documents: true }));
    setError(prev => ({ ...prev, documents: null }));

    try {
      const response = await documentAPI.getAll();
      const documentsData = response.data || [];
      const transformedDocuments = documentsData.map(transformDocument);
      
      setDocuments(transformedDocuments);
      
      // Update cache
      cacheRef.current.documents = documentsData;
      cacheRef.current.timestamp = Date.now();
      
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load documents';
      setError(prev => ({ ...prev, documents: errorMessage }));
      toast.error(errorMessage);
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(prev => ({ ...prev, documents: false }));
    }
  }, [transformDocument, isCacheValid]);

  // Load projects
  const loadProjects = useCallback(async () => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(prev => ({ ...prev, projects: null }));

    try {
      const response = await projectAPI.getAll();
      const projectsData = response.data || [];
      const transformedProjects = projectsData.map(transformProject);
      
      setProjects(transformedProjects);
      
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load projects';
      setError(prev => ({ ...prev, projects: errorMessage }));
      toast.error(errorMessage);
      console.error('Failed to load projects:', err);
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, [transformProject]);

  // Refresh all data
  const refreshData = useCallback(async () => {
    setLoading(prev => ({ ...prev, stats: true }));
    
    try {
      await Promise.all([
        loadDocuments(true), // Force refresh documents
        loadProjects()
      ]);
    } finally {
      setLoading(prev => ({ ...prev, stats: false }));
    }
  }, [loadDocuments, loadProjects]);

  // Update stats when data changes
  useEffect(() => {
    const newStats = calculateStats(documents, projects);
    setStats(newStats);
  }, [documents, projects, calculateStats]);

  // Initial data load
  useEffect(() => {
    loadDocuments();
    loadProjects();
  }, [loadDocuments, loadProjects]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      refreshData();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [refreshData]);

  return {
    documents,
    projects,
    stats,
    loading,
    error,
    refreshData,
    loadDocuments: () => loadDocuments(true),
    loadProjects
  };
};
