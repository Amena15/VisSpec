import React, { useState, useEffect, useCallback } from 'react';
import { UploadCloud, File as Document, CheckCircle, X, AlertCircle, ArrowRight, AlertTriangle, Plus } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { projectAPI, documentAPI } from '../services/api';

const DocumentUpload = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await projectAPI.getAll();
        setProjects(response.data || []);
        if (response.data && response.data.length > 0) {
          setSelectedProject(response.data[0].project_id);
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error);
        toast.error('Failed to load projects. Please try again.');
      }
    };
    fetchProjects();
  }, []);

  const validateFile = (file) => {
    const errors = [];
    const validExtensions = ['pdf', 'docx', 'txt'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
      errors.push(`${file.name} is not a supported file type. Only .pdf, .docx, and .txt files are accepted.`);
    }
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      errors.push(`${file.name} exceeds the maximum file size of 10MB.`);
    }
    return errors;
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      toast.error('Please enter a project name');
      return;
    }
    try {
      const response = await projectAPI.create({ name: newProjectName.trim() });
      const newProject = response.data;
      setProjects(prev => [newProject, ...prev]);
      setSelectedProject(newProject.project_id);
      setNewProjectName('');
      setIsCreatingProject(false);
      toast.success('Project created successfully');
    } catch (error) {
      console.error('Failed to create project:', error);
      toast.error('Failed to create project');
    }
  };

  const handleDragOver = useCallback((e) => { e.preventDefault(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setIsDragging(false); }, []);

  const processFiles = (fileList) => {
    const processedFiles = [];
    fileList.forEach(file => {
      const errors = validateFile(file);
      if (errors.length > 0) {
        processedFiles.push({ id: Date.now() + Math.random(), name: file.name, size: file.size, type: file.type, status: 'error', errors, file: null });
        setValidationErrors(prev => [...prev, ...errors]);
      } else {
        processedFiles.push({ id: Date.now() + Math.random(), name: file.name, size: file.size, type: file.type, status: 'pending', progress: 0, file });
      }
    });
    setFiles(prev => [...prev, ...processedFiles]);
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(Array.from(e.dataTransfer.files));
  }, []);

  const handleFileInput = (e) => {
    processFiles(Array.from(e.target.files));
  };

  const handleUpload = async (fileObj) => {
    if (!selectedProject) { toast.error('Please select or create a project first'); return; }
    if (!fileObj.file) return;
    setIsUploading(true);
    setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'uploading', progress: 0 } : f));

    try {
      const onUploadProgress = (progressEvent) => {
        const progress = progressEvent.total ? Math.round((progressEvent.loaded * 100) / progressEvent.total) : 0;
        setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, progress } : f));
      };
      const response = await documentAPI.upload(selectedProject, fileObj.file, onUploadProgress);
      const result = response.data;
      setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'complete', progress: 100 } : f));
      setUploadResult(result);
      toast.success(`Document uploaded! Found ${result.requirements_found} requirements.`);
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMsg = error.response?.data?.detail || 'Upload failed due to server error. Please retry.';
      setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'error', errors: [errorMsg] } : f));
      toast.error(errorMsg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartAnalysis = () => {
    if (uploadResult?.doc_id) {
      navigate(`/analysis-results/${uploadResult.doc_id}`);
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)] p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[var(--neutral-900)]">Upload Requirements Document</h1>
          <p className="text-[var(--neutral-600)] mt-2">Submit your SRS document for automated analysis</p>
        </div>

        <div className="bg-[var(--card-bg)] rounded-xl border border-[var(--card-border)] p-6 mb-6">
          <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">Select Project</h3>
          {isCreatingProject ? (
            <div className="flex gap-2">
              <input type="text" value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)} placeholder="Enter project name..."
                className="flex-1 px-4 py-2 border border-[var(--card-border)] rounded-lg bg-[var(--surface-bg)] text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-main)]"
                onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()} />
              <button onClick={handleCreateProject} className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors">Create</button>
              <button onClick={() => { setIsCreatingProject(false); setNewProjectName(''); }}
                className="bg-[var(--surface-bg)] text-[var(--text-secondary)] px-4 py-2 rounded-lg hover:bg-[var(--card-border)] transition-colors">Cancel</button>
            </div>
          ) : (
            <div className="flex gap-2 items-center">
              <select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)}
                className="flex-1 px-4 py-2 border border-[var(--card-border)] rounded-lg bg-[var(--surface-bg)] text-[var(--text-primary)]">
                <option value="">Select a project...</option>
                {projects.map(project => (
                  <option key={project.project_id} value={project.project_id}>{project.name} ({project.document_count || 0} documents)</option>
                ))}
              </select>
              <button onClick={() => setIsCreatingProject(true)}
                className="flex items-center gap-2 bg-[var(--surface-bg)] text-[var(--primary-main)] px-4 py-2 rounded-lg hover:bg-[var(--primary-main)]/10 transition-colors border border-[var(--card-border)]">
                <Plus className="h-4 w-4" /> New Project
              </button>
            </div>
          )}
        </div>

        <div className={`h-64 bg-[var(--card-bg)] border-2 rounded-xl flex flex-col items-center justify-center text-center transition-colors ${isDragging ? 'border-[var(--primary-main)] bg-[var(--primary-main)]/5' : 'border-dashed border-[var(--card-border)]'}`}
          onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
          <div className="mb-4">
            <UploadCloud className={`h-12 w-12 ${isDragging ? 'text-[var(--primary-main)]' : 'text-[var(--text-secondary)]'}`} />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Drag & Drop your SRS Document</h3>
          <p className="text-[var(--text-secondary)] mb-4">Supports .PDF, .DOCX, and .TXT files</p>
          <p className="text-sm text-[var(--text-secondary)]">Maximum file size: 10MB</p>
          <input type="file" id="file-upload" className="hidden" accept=".pdf,.docx,.txt" multiple onChange={handleFileInput} />
          <label htmlFor="file-upload" className="mt-4 bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors cursor-pointer">Choose File</label>
        </div>

        {validationErrors.length > 0 && (
          <div className="mt-6">
            <div className="bg-[var(--error-light)]/10 border-l-4 border-[var(--error-main)] p-4 rounded">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-[var(--error-main)] mr-3" />
                <div>
                  <p className="text-sm font-medium text-[var(--error-main)]">Validation Errors</p>
                  <ul className="mt-2 space-y-1">
                    {validationErrors.map((error, index) => (
                      <li key={index} className="text-sm text-[var(--error-main)]">{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {files.length > 0 && (
          <div className="mt-8">
            <h3 className="text-lg font-medium text-primary mb-4">Uploaded Files</h3>
            <div className="space-y-3">
              {files.map((file) => (
                <div key={file.id} className="bg-[var(--card-bg)] shadow-sm rounded-lg p-4 flex items-center justify-between">
                  <div className="flex items-center">
                    <Document className="h-5 w-5 text-[var(--primary-main)] mr-3" />
                    <div>
                      <p className="font-medium text-[var(--text-primary)] text-sm">{file.name}</p>
                      <p className="text-xs text-[var(--text-secondary)]">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {file.status === 'pending' && (
                      <button onClick={() => handleUpload(file)} disabled={isUploading}
                        className="bg-[var(--primary-main)] text-white px-3 py-1.5 rounded-lg text-sm hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50">Upload</button>
                    )}
                    {file.status === 'uploading' && (
                      <div className="w-32 bg-[var(--surface-bg)] rounded-full h-2">
                        <div className="bg-[var(--success-main)] h-2 rounded-full transition-all duration-300" style={{ width: `${file.progress}%` }}></div>
                      </div>
                    )}
                    {file.status === 'complete' && (
                      <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-[var(--success-main)] mr-2" />
                        <span className="text-xs text-[var(--success-main)] font-medium">Complete</span>
                      </div>
                    )}
                    {file.status === 'error' && (
                      <div className="flex items-center">
                        <AlertCircle className="h-5 w-5 text-[var(--error-main)] mr-2" />
                        <div className="text-xs text-[var(--error-main)] font-medium">
                          <div>Error</div>
                          {file.errors && file.errors.length > 0 && (
                            <div className="text-[10px] text-left mt-1 max-w-[150px]">{file.errors[0]}</div>
                          )}
                        </div>
                      </div>
                    )}
                    <button onClick={() => removeFile(file.id)} className="text-[var(--text-secondary)] hover:text-[var(--error-main)] transition-colors">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {uploadResult && (
          <div className="mt-6 bg-[var(--success-light)]/10 border border-[var(--success-main)] rounded-xl p-6">
            <h3 className="text-lg font-semibold text-[var(--success-main)] mb-2">Document Summary</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div><span className="text-[var(--text-secondary)]">Word Count:</span> <span className="font-medium text-[var(--text-primary)]">{uploadResult.word_count}</span></div>
              <div><span className="text-[var(--text-secondary)]">Requirements Found:</span> <span className="font-medium text-[var(--text-primary)]">{uploadResult.requirements_found}</span></div>
              <div><span className="text-[var(--text-secondary)]">Sections:</span> <span className="font-medium text-[var(--text-primary)]">{uploadResult.sections_found?.length || 0}</span></div>
            </div>
          </div>
        )}

        <div className="mt-8 flex justify-end">
          {uploadResult ? (
            <button onClick={handleStartAnalysis}
              className="bg-[var(--primary-main)] text-white px-6 py-3 rounded-lg font-medium hover:bg-[var(--primary-hover)] transition-colors flex items-center">
              Run Validation <ArrowRight className="ml-2 h-5 w-5" />
            </button>
          ) : (
            <button disabled className="bg-[var(--surface-bg)] text-[var(--text-secondary)] px-6 py-3 rounded-lg font-medium cursor-not-allowed">
              Run Validation
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;

