import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Clock, Target, AlertCircle, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';

const DefectCard = ({ 
  defect, 
  onApplySuggestion, 
  onIgnoreDefect, 
  onViewOriginal,
  showOriginal = false,
  isExpanded = false,
  onToggleExpand 
}) => {
  const [localExpanded, setLocalExpanded] = useState(isExpanded);
  const [showOriginalText, setShowOriginalText] = useState(showOriginal);

  const toggleExpand = () => {
    if (onToggleExpand) {
      onToggleExpand();
    } else {
      setLocalExpanded(!localExpanded);
    }
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

  const handleApplySuggestion = (e) => {
    e.stopPropagation();
    if (onApplySuggestion && defect.suggestion) {
      onApplySuggestion(defect);
    }
  };

  const handleIgnoreDefect = (e) => {
    e.stopPropagation();
    if (onIgnoreDefect) {
      onIgnoreDefect(defect);
    }
  };

  const handleViewOriginal = (e) => {
    e.stopPropagation();
    setShowOriginalText(!showOriginalText);
    if (onViewOriginal) {
      onViewOriginal(defect);
    }
  };

  const isExpanded = onToggleExpand ? isExpanded : localExpanded;

  return (
    <div className={`border rounded-lg overflow-hidden transition-all ${getSeverityColor(defect.severity)}`}>
      <div
        className="p-4 cursor-pointer hover:bg-opacity-80 transition-colors"
        onClick={toggleExpand}
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
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {isExpanded && (
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
                  onClick={handleApplySuggestion}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Apply Suggestion
                </button>
              )}
              
              {onIgnoreDefect && (
                <button
                  onClick={handleIgnoreDefect}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-sm font-medium"
                >
                  Ignore
                </button>
              )}

              {defect.text && (
                <button
                  onClick={handleViewOriginal}
                  className="px-4 py-2 bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium flex items-center space-x-1"
                >
                  {showOriginalText ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>{showOriginalText ? 'Hide' : 'Show'} Original</span>
                </button>
              )}
            </div>

            {defect.text && showOriginalText && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Original Text:</h4>
                <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                  <p className="text-gray-600 text-sm italic">{defect.text}</p>
                </div>
              </div>
            )}

            {defect.similarity_score && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Similarity Analysis:</h4>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <p className="text-blue-700 text-sm">
                    Similarity Score: {Math.round(defect.similarity_score * 100)}%
                  </p>
                  {defect.similar_requirements && (
                    <p className="text-blue-600 text-xs mt-1">
                      Found {defect.similar_requirements.length} similar requirements
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DefectCard;
