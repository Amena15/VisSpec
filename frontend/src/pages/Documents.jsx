import React, { useState, useEffect } from 'react';
import {
  Folder,
  FileText,
  Search,
  Filter,
  LayoutGrid,
  List,
  Plus,
  Star,
  MoreHorizontal,
  Calendar,
  Trash2,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { projectAPI, documentAPI } from '../services/api';

const Documents = () => {
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeMenu, setActiveMenu] = useState(null);
  const [projects, setProjects] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [projectsRes, docsRes] = await Promise.all([
        projectAPI.getAll(),
        documentAPI.getAll()
      ]);
      setProjects(projectsRes.data || []);
      setDocuments(docsRes.data || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (window.confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      try {
        await documentAPI.delete(docId);
        setDocuments(prev => prev.filter(doc => doc.doc_id !== docId));
        setActiveMenu(null);
        toast.success('Document deleted successfully');
      } catch (error) {
        console.error('Error deleting document:', error);
        toast.error('Failed to delete document');
      }
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project and all its documents? This action cannot be undone.')) {
      try {
        await projectAPI.delete(projectId);
        setProjects(prev => prev.filter(p => p.project_id !== projectId));
        setDocuments(prev => prev.filter(d => d.project_id !== projectId));
        setActiveMenu(null);
        toast.success('Project and associated data deleted');
      } catch (error) {
        console.error('Error deleting project:', error);
        toast.error('Failed to delete project');
      }
    }
  };

  const toggleMenu = (itemId, type = 'document') => {
    const menuKey = `${type}-${itemId}`;
    setActiveMenu(activeMenu === menuKey ? null : menuKey);
  };

  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    return new Date(dateStr).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-[var(--primary-main)] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-4 sm:py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
            <div className="mb-6 sm:mb-0">
              <h1 className="text-3xl font-bold text-[var(--text-primary)]">Documents</h1>
              <p className="text-[var(--text-secondary)] mt-1">Manage all your requirements in one place</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
                <input type="text" placeholder="Search documents..." value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full sm:w-64 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent bg-[var(--card-bg)] text-[var(--text-primary)]" />
              </div>
              <div className="flex border border-[var(--card-border)] rounded-lg">
                <button onClick={() => setViewMode('grid')} className={`p-2 ${viewMode === 'grid' ? 'bg-[var(--primary-main)] text-white' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-bg)]'} rounded-l-lg transition-colors`}>
                  <LayoutGrid className="h-4 w-4" />
                </button>
                <button onClick={() => setViewMode('list')} className={`p-2 ${viewMode === 'list' ? 'bg-[var(--primary-main)] text-white' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-bg)]'} rounded-r-lg transition-colors`}>
                  <List className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">Projects</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
              {projects.map((project) => (
                <div key={project.project_id} className="bg-[var(--card-bg)] p-4 sm:p-6 rounded-xl border border-[var(--card-border)] shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                        <Folder className="h-6 w-6 text-[var(--primary-main)]" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-[var(--text-primary)]">{project.name}</h3>
                        <p className="text-sm text-[var(--text-secondary)]">{project.document_count} documents</p>
                      </div>
                    </div>
                    <div className="relative">
                      <button onClick={(e) => { e.stopPropagation(); toggleMenu(project.project_id, 'project'); }}
                        className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                      {activeMenu === `project-${project.project_id}` && (
                        <div className="absolute right-0 mt-2 w-40 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)]">
                          <button onClick={(e) => { e.stopPropagation(); handleDeleteProject(project.project_id); }}
                            className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center">
                            <Trash2 className="h-4 w-4 mr-2" /> Delete Project
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-[var(--text-primary)]">All Documents</h2>
              <p className="text-sm text-[var(--text-secondary)]">{filteredDocuments.length} documents</p>
            </div>

            {filteredDocuments.length === 0 ? (
              <div className="text-center py-12 bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)]">
                <FileText className="h-12 w-12 text-[var(--text-secondary)] mx-auto mb-4" />
                <p className="text-[var(--text-secondary)]">No documents found</p>
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredDocuments.map((doc) => (
                  <div key={doc.doc_id} className="bg-[var(--card-bg)] p-6 rounded-xl border border-[var(--card-border)] shadow-sm hover:shadow-md transition-all cursor-pointer">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center">
                        <div className="bg-[var(--surface-bg)] p-3 rounded-lg mr-4">
                          <FileText className="h-5 w-5 text-[var(--primary-main)]" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-[var(--text-primary)] text-sm truncate max-w-[180px]">{doc.filename}</h3>
                          <p className="text-sm text-[var(--text-secondary)]">{(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                      </div>
                      <div className="relative">
                        <button onClick={(e) => { e.stopPropagation(); toggleMenu(doc.doc_id, 'document'); }}
                          className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors">
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                        {activeMenu === `document-${doc.doc_id}` && (
                          <div className="absolute right-0 mt-2 w-48 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)]">
                            <button onClick={(e) => { e.stopPropagation(); window.location.href = `/analysis-results/${doc.doc_id}`; }}
                              className="w-full text-left px-4 py-2 text-sm text-[var(--primary-main)] hover:bg-[var(--primary-light)] flex items-center">
                              <FileText className="h-4 w-4 mr-2" /> View Analysis
                            </button>
                            <button onClick={(e) => { e.stopPropagation(); handleDeleteDocument(doc.doc_id); }}
                              className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center">
                              <Trash2 className="h-4 w-4 mr-2" /> Delete Document
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-6">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        doc.status === 'ready' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                        doc.status === 'uploading' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                        'bg-[var(--error-light)] text-[var(--error-hover)]'
                      }`}>
                        {doc.status}
                      </span>
                      <div className="flex items-center text-sm text-[var(--text-secondary)]">
                        <Calendar className="h-4 w-4 mr-1" />
                        {formatDate(doc.upload_date)}
                      </div>
                    </div>
                    {doc.requirements_found > 0 && (
                      <div className="mt-3 text-xs text-[var(--text-secondary)]">
                        {doc.requirements_found} requirements found
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] shadow-sm overflow-hidden">
                <table className="min-w-full divide-y divide-[var(--card-border)]">
                  <thead className="bg-[var(--card-bg)]">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Size</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--card-border)]">
                    {filteredDocuments.map((doc) => (
                      <tr key={doc.doc_id} className="hover:bg-[var(--surface-bg)] transition-colors cursor-pointer">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="bg-[var(--surface-bg)] p-2 rounded-lg mr-3">
                              <FileText className="h-5 w-5 text-[var(--primary-main)]" />
                            </div>
                            <div>
                              <div className="text-sm font-medium text-[var(--text-primary)]">{doc.filename}</div>
                              {doc.requirements_found > 0 && (
                                <div className="text-xs text-[var(--text-secondary)]">{doc.requirements_found} requirements</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">{(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            doc.status === 'ready' ? 'bg-[var(--success-light)] text-[var(--success-hover)]' :
                            doc.status === 'uploading' ? 'bg-[var(--warning-light)] text-[var(--warning-hover)]' :
                            'bg-[var(--error-light)] text-[var(--error-hover)]'
                          }`}>
                            {doc.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {formatDate(doc.upload_date)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-secondary)]">
                          <div className="relative">
                            <button onClick={(e) => { e.stopPropagation(); toggleMenu(doc.doc_id, 'document'); }}
                              className="text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors">
                              <MoreHorizontal className="h-4 w-4" />
                            </button>
                            {activeMenu === `document-${doc.doc_id}` && (
                              <div className="absolute right-0 mt-2 w-40 bg-[var(--card-bg)] rounded-md shadow-lg py-1 z-10 border border-[var(--card-border)]">
                                <button onClick={(e) => { e.stopPropagation(); handleDeleteDocument(doc.doc_id); }}
                                  className="w-full text-left px-4 py-2 text-sm text-[var(--error-main)] hover:bg-[var(--error-light)] flex items-center">
                                  <Trash2 className="h-4 w-4 mr-2" /> Delete Document
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documents;

