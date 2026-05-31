import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Target, Clock, AlertCircle } from 'lucide-react';

const ValidationSummary = ({ defects, qualityScore, totalRequirements }) => {
  const getDefectStats = () => {
    const stats = {
      high: 0,
      medium: 0,
      low: 0,
      total: defects.length,
      ambiguity: 0,
      incompleteness: 0,
      inconsistency: 0,
      unverifiable: 0
    };

    defects.forEach(defect => {
      // Count by severity
      if (defect.severity) {
        const severity = defect.severity.toLowerCase();
        if (severity === 'high') stats.high++;
        else if (severity === 'medium') stats.medium++;
        else if (severity === 'low') stats.low++;
      }

      // Count by type
      if (defect.type) {
        const type = defect.type.toLowerCase();
        if (type === 'ambiguity') stats.ambiguity++;
        else if (type === 'incompleteness') stats.incompleteness++;
        else if (type === 'inconsistency') stats.inconsistency++;
        else if (type === 'unverifiable') stats.unverifiable++;
      }
    });

    return stats;
  };

  const stats = getDefectStats();
  const defectRate = totalRequirements > 0 ? (stats.total / totalRequirements * 100).toFixed(1) : 0;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getDefectTypeIcon = (type) => {
    switch (type) {
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

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-6">Validation Summary</h2>
      
      {/* Overall Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-semibold text-gray-900">Overall Quality Score</span>
          <span className={`text-2xl font-bold ${getScoreColor(qualityScore)}`}>
            {qualityScore}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${getScoreBgColor(qualityScore)}`}
            style={{ width: `${qualityScore}%` }}
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Requirements</span>
            <span className="text-lg font-bold text-gray-900">{totalRequirements}</span>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Defects Found</span>
            <span className="text-lg font-bold text-red-600">{stats.total}</span>
          </div>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Defect Rate</span>
            <span className="text-lg font-bold text-orange-600">{defectRate}%</span>
          </div>
        </div>
      </div>

      {/* Severity Breakdown */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Severity Breakdown</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <XCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-gray-600">High Severity</span>
            </div>
            <span className="font-semibold text-red-600">{stats.high}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-gray-600">Medium Severity</span>
            </div>
            <span className="font-semibold text-yellow-600">{stats.medium}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-blue-500" />
              <span className="text-sm text-gray-600">Low Severity</span>
            </div>
            <span className="font-semibold text-blue-600">{stats.low}</span>
          </div>
        </div>
      </div>

      {/* Defect Type Breakdown */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Defect Types</h3>
        <div className="space-y-2">
          {stats.ambiguity > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getDefectTypeIcon('ambiguity')}
                <span className="text-sm text-gray-600">Ambiguity</span>
              </div>
              <span className="font-semibold text-gray-700">{stats.ambiguity}</span>
            </div>
          )}
          
          {stats.incompleteness > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getDefectTypeIcon('incompleteness')}
                <span className="text-sm text-gray-600">Incompleteness</span>
              </div>
              <span className="font-semibold text-gray-700">{stats.incompleteness}</span>
            </div>
          )}
          
          {stats.inconsistency > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getDefectTypeIcon('inconsistency')}
                <span className="text-sm text-gray-600">Inconsistency</span>
              </div>
              <span className="font-semibold text-gray-700">{stats.inconsistency}</span>
            </div>
          )}
          
          {stats.unverifiable > 0 && (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getDefectTypeIcon('unverifiable')}
                <span className="text-sm text-gray-600">Unverifiable</span>
              </div>
              <span className="font-semibold text-gray-700">{stats.unverifiable}</span>
            </div>
          )}
          
          {stats.total === 0 && (
            <div className="flex items-center justify-center py-4">
              <CheckCircle className="w-8 h-8 text-green-500 mr-2" />
              <span className="text-green-600 font-medium">No defects found!</span>
            </div>
          )}
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-center">
          {stats.high > 0 ? (
            <div className="flex items-center text-red-600">
              <XCircle className="w-5 h-5 mr-2" />
              <span className="font-medium">Critical issues require attention</span>
            </div>
          ) : stats.medium > 0 ? (
            <div className="flex items-center text-yellow-600">
              <AlertTriangle className="w-5 h-5 mr-2" />
              <span className="font-medium">Some improvements recommended</span>
            </div>
          ) : stats.low > 0 ? (
            <div className="flex items-center text-blue-600">
              <AlertCircle className="w-5 h-5 mr-2" />
              <span className="font-medium">Minor issues found</span>
            </div>
          ) : (
            <div className="flex items-center text-green-600">
              <CheckCircle className="w-5 h-5 mr-2" />
              <span className="font-medium">All requirements passed validation</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ValidationSummary;
