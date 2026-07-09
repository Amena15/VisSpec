import React, { useState } from 'react';
import { Download, FileText, Clock, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../services/api';

const ExportReport = ({ documentData, analysisResults, onClose }) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleExport = async () => {
    setIsGenerating(true);

    try {
      // Simulate report generation
      // Call backend export API and trigger a real PDF download
      const payload = {
        project_name: documentData?.projectName || 'Untitled Project',
        analysis_data: analysisResults?.analysisData || analysisResults || {},
        diagrams: documentData?.diagrams || [],
        metrics: analysisResults?.metrics || analysisResults || {},
        traceability: documentData?.traceability || analysisResults?.traceability || [],
        report_type: 'full',
      };

      const response = await apiClient.post('/api/reports/export', payload, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      const fileName = `vispec_report_${documentData?.projectName || 'Untitled_Project'}.pdf`;
      a.href = url;
      a.download = fileName.replace(/[^a-z0-9 _-]/gi, '_');
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Report exported successfully as PDF!', {
        duration: 3000,
        position: 'top-right'
      });

      if (onClose) {
        onClose();
      }
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Report generation failed. Please try again.', {
        duration: 3000,
        position: 'top-right'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  // Calculate metrics for the report
  const totalRequirements = documentData?.requirements?.length || 0;
  const totalDefects = analysisResults?.defects?.length || 0;
  const qualityScore = analysisResults?.qualityScore || 0;
  const estimatedEffort = analysisResults?.estimatedEffort || 'N/A';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--card-bg)] rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        <div className="p-6 border-b border-[var(--card-border)]">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[var(--neutral-900)]">Export Validation Report</h2>
            <button
              onClick={onClose}
              className="text-[var(--neutral-400)] hover:text-[var(--neutral-700)] text-2xl"
            >
              &times;
            </button>
          </div>
          <p className="text-sm text-[var(--neutral-600)] mt-1">Generate and download your analysis report</p>
        </div>

        <div className="p-6 space-y-6">
          {/* Report Preview */}
          <div className="bg-[var(--neutral-50)] rounded-lg p-4">
            <h3 className="font-medium text-[var(--neutral-900)] mb-3">Report Summary</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--neutral-600)]">Total Requirements:</span>
                <span className="font-medium text-[var(--neutral-900)]">{totalRequirements}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--neutral-600)]">Defects Found:</span>
                <span className="font-medium text-[var(--error-main)]">{totalDefects}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--neutral-600)]">Quality Score:</span>
                <span className="font-medium text-[var(--neutral-900)]">{qualityScore}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--neutral-600)]">Estimated Effort:</span>
                <span className="font-medium text-[var(--neutral-900)]">{estimatedEffort}</span>
              </div>
            </div>
          </div>

          {/* Export Format */}
          <div>
            <label className="block text-sm font-medium text-[var(--neutral-700)] mb-2">Export Format</label>
            <div className="flex items-center justify-center p-3 rounded-lg border border-[var(--accent-main)] bg-[var(--accent-50)] text-[var(--accent-main)] font-medium">
              <FileText className="w-5 h-5 mr-2" />
              PDF
            </div>
          </div>

          {/* Watermark Notice */}
          <div className="bg-[var(--info-light)] border border-[var(--info-main)] rounded-lg p-3">
            <div className="flex items-start">
              <FileText className="w-5 h-5 text-[var(--info-main)] mt-0.5 mr-2 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-[var(--info-dark)] text-sm">VisSpec Watermark</h4>
                <p className="text-xs text-[var(--info-dark)] mt-1">
                  All exported reports include a VisSpec watermark and timestamp.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-[var(--card-border)] flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[var(--neutral-700)] bg-[var(--neutral-100)] rounded-lg hover:bg-[var(--neutral-200)] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isGenerating}
            className="px-6 py-2 bg-[var(--btn-primary-bg)] text-white rounded-lg hover:bg-[var(--btn-primary-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export Report
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportReport;