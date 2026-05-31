import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Clock, Target, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

const ValidationResults = ({ defects, onApplySuggestion, onIgnoreDefect, onUndo, canUndo }) => {
  const [expandedDefects, setExpandedDefects] = useState(new Set());
  
  const toggleDefect = (defectId) => {
    const newExpanded = new Set(expandedDefects);
    if (newExpanded.has(defectId)) {
      newExpanded.delete(defectId);
    } else {
      newExpanded.add(defectId);
    }
    setExpandedDefects(newExpanded);
  };

  const getSeverityIcon = (severity) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'medium':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'low':
        return <AlertCircle className="w-5 h-5 text-blue-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'border-red-200 bg-red-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      case 'low':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getDefectTypeIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'ambiguity':
        return <Target className="w-4 h-4" />;
      case 'incompleteness':
        return <Clock className="w-4 h-4" />;
      case 'inconsistency':
        return <AlertTriangle className="w-4 h-4" />;
      case 'unverifiable':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  const handleApplySuggestion = (defect) => {
    if (onApplySuggestion && defect.suggestion) {
      onApplySuggestion(defect);
    }
  };

  const handleIgnoreDefect = (defect) => {
    if (onIgnoreDefect) {
      onIgnoreDefect(defect);
    }
  };

  if (!defects || defects.length === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-green-800 mb-2">No Defects Found</h3>
        <p className="text-green-600">All requirements passed validation successfully!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Validation Results</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            {defects.length} defect{defects.length !== 1 ? 's' : ''} found
          </span>
          {canUndo && (
            <button
              onClick={onUndo}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Undo (Ctrl+Z)
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {defects.map((defect, index) => (
          <div
            key={defect.id || index}
            className={`border rounded-lg overflow-hidden transition-all ${getSeverityColor(defect.severity)}`}
          >
            <div
              className="p-4 cursor-pointer hover:bg-opacity-80 transition-colors"
              onClick={() => toggleDefect(defect.id || index)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  {getSeverityIcon(defect.severity)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      {getDefectTypeIcon(defect.type)}
                      <span className="font-semibold text-gray-900 capitalize">{defect.type}</span>
                      <span className="text-sm text-gray-500">• Severity: {defect.severity}</span>
                      <span className="text-sm text-gray-500">• Confidence: {Math.round((defect.confidence || 0) * 100)}%</span>
                    </div>
                    <p className="text-gray-700 text-sm mb-2">{defect.description}</p>
                    {defect.req_id && (
                      <p className="text-xs text-gray-500">Requirement ID: {defect.req_id}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  {expandedDefects.has(defect.id || index) ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </div>
              </div>
            </div>

            {expandedDefects.has(defect.id || index) && (
              <div className="border-t border-gray-200 p-4 bg-white bg-opacity-50">
                <div className="space-y-4">
                  {defect.suggestion && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Suggested Fix:</h4>
                      <div className="bg-white border border-gray-200 rounded-md p-3">
                        <p className="text-gray-700 text-sm">{defect.suggestion}</p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-3">
                    {defect.suggestion && onApplySuggestion && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleApplySuggestion(defect);
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                      >
                        Apply Suggestion
                      </button>
                    )}
                    
                    {onIgnoreDefect && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleIgnoreDefect(defect);
                        }}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-sm font-medium"
                      >
                        Ignore
                      </button>
                    )}
                  </div>

                  {defect.text && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Original Text:</h4>
                      <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                        <p className="text-gray-600 text-sm italic">{defect.text}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ValidationResults;
