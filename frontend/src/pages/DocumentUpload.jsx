import React, { useState } from 'react';
import { UploadCloud, File as Document, CheckCircle, X, AlertCircle, ArrowRight, AlertTriangle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const DocumentUpload = () => {
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);

  // Function to validate file before upload according to BR-07 and BR-08
  const validateFile = (file) => {
    const errors = [];

    // BR-07: Only .pdf and .docx formats are accepted
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
      'application/msword' // .doc
    ];

    if (!validTypes.includes(file.type) &&
        !file.name.toLowerCase().endsWith('.pdf') &&
        !file.name.toLowerCase().endsWith('.docx') &&
        !file.name.toLowerCase().endsWith('.doc')) {
      errors.push(`${file.name} is not a supported file type. Only .pdf, .docx, and .doc files are accepted.`);
    }

    // BR-08: Maximum file size is strictly 10MB to prevent server overload
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
      errors.push(`${file.name} exceeds the maximum file size of 10MB.`);
    }

    return errors;
  };

  // Function to add a mock file and navigate to analysis
  const addMockFile = (name, size, type = 'application/pdf') => {
    // Instead of simulating upload, directly navigate to analysis page
    navigate('/analysis');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    const processedFiles = [];

    droppedFiles.forEach(file => {
      const errors = validateFile(file);

      if (errors.length > 0) {
        // Add file with error status
        const errorFile = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'error',
          errors: errors
        };
        processedFiles.push(errorFile);
        setValidationErrors(prev => [...prev, ...errors]);
      } else {
        // Add valid file
        const validFile = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'uploading',
          progress: 0
        };
        processedFiles.push(validFile);
      }
    });

    setFiles(prev => [...prev, ...processedFiles]);

    // Simulate upload progress for valid files only
    processedFiles
      .filter(file => file.status !== 'error')
      .forEach(fileObj => {
        simulateUpload(fileObj.id);
      });
  };

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const processedFiles = [];

    selectedFiles.forEach(file => {
      const errors = validateFile(file);

      if (errors.length > 0) {
        // Add file with error status
        const errorFile = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'error',
          errors: errors
        };
        processedFiles.push(errorFile);
        setValidationErrors(prev => [...prev, ...errors]);
      } else {
        // Add valid file
        const validFile = {
          id: Date.now() + Math.random(),
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'uploading',
          progress: 0
        };
        processedFiles.push(validFile);
      }
    });

    setFiles(prev => [...prev, ...processedFiles]);

    // Simulate upload progress for valid files only
    processedFiles
      .filter(file => file.status !== 'error')
      .forEach(fileObj => {
        simulateUpload(fileObj.id);
      });
  };

  const simulateUpload = (fileId) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setFiles(prev => prev.map(file =>
        file.id === fileId ? { ...file, progress } : file
      ));

      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          setFiles(prev => prev.map(file =>
            file.id === fileId ? { ...file, status: 'complete', progress: 100 } : file
          ));
        }, 300);
      }
    }, 200);
  };

  // Function to handle document analysis after successful upload
  const handleStartAnalysis = () => {
    const completedFiles = files.filter(file => file.status === 'complete');
    if (completedFiles.length > 0) {
      // In a real app, this would trigger the analysis process
      // For now, we'll just navigate to the analysis page
      window.location.href = '/analysis';
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

        {/* Upload Drop Zone */}
        <div
          className={`h-64 bg-[var(--card-bg)] border-2 rounded-xl flex flex-col items-center justify-center text-center transition-colors ${
            isDragging
              ? 'border-[var(--primary-main)] bg-[var(--primary-main)]/5'
              : 'border-dashed border-[var(--card-border)]'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="mb-4">
            <UploadCloud className={`h-12 w-12 ${isDragging ? 'text-[var(--primary-main)]' : 'text-[var(--text-secondary)]'}`} />
          </div>
          <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">Drag & Drop your SRS Document</h3>
          <p className="text-[var(--text-secondary)] mb-4">Supports .PDF, .DOCX, and .DOC files</p>
          <p className="text-sm text-[var(--text-secondary)]">Maximum file size: 10MB</p>

          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".pdf,.docx,.doc"
            multiple
            onChange={handleFileInput}
          />
          <label
            htmlFor="file-upload"
            className="mt-4 bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors cursor-pointer"
          >
            Choose File
          </label>
        </div>

        {/* Validation Errors Display */}
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

        {/* Uploaded Files List */}
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
                    {file.status === 'uploading' && (
                      <div className="w-32 bg-[var(--surface-bg)] rounded-full h-2">
                        <div
                          className="bg-[var(--success-main)] h-2 rounded-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        ></div>
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
                            <div className="text-[10px] text-left mt-1 max-w-[150px]">
                              {file.errors[0]}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <button
                      onClick={() => removeFile(file.id)}
                      className="text-[var(--text-secondary)] hover:text-[var(--error-main)] transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sample Documents Section */}
        <div className="mt-8">
          <h3 className="text-lg font-medium text-[var(--neutral-900)] mb-4">Try Sample Documents</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/analysis-results')}
              className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 text-left hover:shadow-md transition-shadow flex items-center"
            >
              <Document className="h-5 w-5 text-[var(--primary-main)] mr-3" />
              <div>
                <p className="font-medium text-[var(--text-primary)]">Student Registration System.pdf</p>
                <p className="text-sm text-[var(--text-secondary)]">PDF • 2.4 MB</p>
              </div>
            </button>

            <button
              onClick={() => navigate('/analysis-results')}
              className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 text-left hover:shadow-md transition-shadow flex items-center"
            >
              <Document className="h-5 w-5 text-[var(--primary-main)] mr-3" />
              <div>
                <p className="font-medium text-[var(--text-primary)]">E-Commerce Platform Requirements.docx</p>
                <p className="text-sm text-[var(--text-secondary)]">DOCX • 1.8 MB</p>
              </div>
            </button>

            <button
              onClick={() => navigate('/analysis-results')}
              className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 text-left hover:shadow-md transition-shadow flex items-center"
            >
              <Document className="h-5 w-5 text-[var(--primary-main)] mr-3" />
              <div>
                <p className="font-medium text-[var(--text-primary)]">Healthcare Management System.doc</p>
                <p className="text-sm text-[var(--text-secondary)]">DOC • 1.2 MB</p>
              </div>
            </button>
          </div>

        </div>

        {/* Start Analysis Button */}
        <div className="mt-8 flex justify-end">
          {files.some(file => file.status === 'complete') ? (
            <Link
              to="/analysis-results"
              className="bg-[var(--primary-main)] text-white px-6 py-3 rounded-lg font-medium hover:bg-[var(--primary-hover)] transition-colors flex items-center"
            >
              Run Validation
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          ) : (
            <button
              disabled={true}
              className="bg-[var(--surface-bg)] text-[var(--text-secondary)] px-6 py-3 rounded-lg font-medium cursor-not-allowed"
            >
              Run Validation
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;