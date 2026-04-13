import React, { useState } from 'react';
import { UploadIcon } from 'lucide-react';

const FileUploader = () => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    document.getElementById("file-upload").click();
  };

  return (
    <div className="w-full">
      <form 
        className={`h-64 w-full border-2 ${dragActive ? 'border-[#4F6D7A] bg-[#F1F5F9]' : 'border-[#CBD5E1] bg-[#F8FAFC]'} border-dashed rounded-xl flex flex-col items-center justify-center hover:bg-[#F1F5F9] transition-colors`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          id="file-upload"
          type="file" 
          className="hidden" 
          onChange={handleChange}
          accept=".pdf,.doc,.docx,.txt,.rtf,.odt"
        />
        <div className="flex flex-col items-center justify-center text-center p-6">
          <div className="bg-[#E0E7FF] p-3 rounded-full mb-4">
            <UploadIcon className="h-8 w-8 text-[#4F6D7A]" />
          </div>
          <h3 className="text-lg font-medium text-[#1F2933] mb-2">
            Drag SRS Document here
          </h3>
          <p className="text-sm text-[#6B7280] mb-4">
            Supported formats: PDF, DOC, DOCX, TXT, RTF, ODT
          </p>
          <button
            type="button"
            onClick={onButtonClick}
            className="bg-[#4F6D7A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#3a505a] transition-colors"
          >
            Browse Files
          </button>
        </div>
      </form>
      {file && (
        <div className="mt-4 p-4 bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg">
          <p className="text-sm text-[#1F2933] truncate">
            Selected: {file.name}
          </p>
          <p className="text-xs text-[#6B7280]">
            Size: {(file.size / 1024).toFixed(2)} KB
          </p>
        </div>
      )}
    </div>
  );
};

export default FileUploader;