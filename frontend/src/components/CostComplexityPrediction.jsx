import React from 'react';
import { TrendingUp, Clock, DollarSign, AlertTriangle, Info, ArrowLeft, Eye, BarChart3 } from 'lucide-react';

const CostComplexityPrediction = ({ requirements = [], analysisResults = {}, onBack, onViewPrediction }) => {
  // Calculate metrics based on requirements
  const calculateMetrics = () => {
    const totalRequirements = requirements.length;
    const avgWordsPerReq = requirements.reduce((sum, req) => sum + (req.text?.split(' ').length || 0), 0) / Math.max(totalRequirements, 1);
    
    // Calculate complexity score based on various factors
    let complexityScore = 0;
    if (totalRequirements > 0) {
      // Base score from requirements count
      complexityScore = Math.min(100, totalRequirements * 2);
      
      // Factor in average requirement length
      complexityScore += Math.min(20, avgWordsPerReq * 0.5);
      
      // Factor in defects found
      const defectCount = analysisResults.defects?.length || 0;
      complexityScore += Math.min(30, defectCount * 2);
      
      complexityScore = Math.min(100, complexityScore);
    }
    
    // Estimate effort based on complexity
    const effortWeeks = Math.round(complexityScore / 10);
    const costIndex = complexityScore > 70 ? 'High' : complexityScore > 40 ? 'Medium' : 'Low';
    
    return {
      complexityScore: Math.round(complexityScore),
      effortWeeks: Math.max(1, effortWeeks), // At least 1 week
      costIndex,
      totalRequirements,
      avgWordsPerReq: Math.round(avgWordsPerReq),
      defectCount: analysisResults.defects?.length || 0
    };
  };

  const metrics = calculateMetrics();

  return (
    <div className="space-y-6">
      {/* Top Navigation Buttons */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack || (() => window.history.back())}
          className="flex items-center px-4 py-2 bg-[var(--surface-bg)] text-[var(--neutral-700)] rounded-lg hover:bg-[var(--card-border)] transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
        
        <button
          onClick={onViewPrediction || (() => alert('View Prediction clicked'))}
          className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
        >
          <BarChart3 className="w-4 h-4 mr-2" />
          View Prediction Details
        </button>
      </div>
      
      {/* Main Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center">
            <div className="p-2 bg-[var(--primary-50)] rounded-lg">
              <TrendingUp className="w-6 h-6 text-[var(--primary-main)]" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-[var(--neutral-500)]">Complexity Score</p>
              <p className="text-2xl font-bold text-[var(--neutral-900)]">{metrics.complexityScore}/100</p>
            </div>
          </div>
        </div>

        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center">
            <div className="p-2 bg-[var(--success-light)] rounded-lg">
              <Clock className="w-6 h-6 text-[var(--success-main)]" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-[var(--neutral-500)]">Est. Duration</p>
              <p className="text-2xl font-bold text-[var(--neutral-900)]">{metrics.effortWeeks} Weeks</p>
            </div>
          </div>
        </div>

        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center">
            <div className="p-2 bg-[var(--surface-bg)] rounded-lg">
              <DollarSign className="w-6 h-6 text-[var(--accent-main)]" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-[var(--neutral-500)]">Cost Index</p>
              <p className={`text-2xl font-bold ${
                metrics.costIndex === 'High' ? 'text-[var(--error-main)]' :
                metrics.costIndex === 'Medium' ? 'text-[var(--warning-main)]' : 'text-[var(--success-main)]'
              }`}>
                {metrics.costIndex}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center">
            <div className="p-2 bg-[var(--warning-light)] rounded-lg">
              <AlertTriangle className="w-6 h-6 text-[var(--warning-main)]" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-[var(--neutral-500)]">Defect Density</p>
              <p className="text-2xl font-bold text-[var(--neutral-900)]">{metrics.defectCount}/{metrics.totalRequirements}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis */}
      <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
        <h3 className="text-lg font-semibold text-[var(--neutral-900)] mb-4">Detailed Analysis</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-[var(--neutral-900)] mb-3">Requirements Analysis</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Total Requirements:</span>
                <span className="text-sm font-medium">{metrics.totalRequirements}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Average Words/Req:</span>
                <span className="text-sm font-medium">{metrics.avgWordsPerReq}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Defects Found:</span>
                <span className="text-sm font-medium text-[var(--error-main)]">{metrics.defectCount}</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-[var(--neutral-900)] mb-3">Complexity Factors</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--neutral-500)]">Requirements Count Impact:</span>
                <span className="font-medium">{Math.min(100, metrics.totalRequirements * 2)} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--neutral-500)]">Text Complexity Impact:</span>
                <span className="font-medium">{Math.min(20, metrics.avgWordsPerReq * 0.5)} pts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--neutral-500)]">Defect Impact:</span>
                <span className="font-medium">{Math.min(30, metrics.defectCount * 2)} pts</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-[var(--info-light)] border border-[var(--info-main)] rounded-lg p-4">
        <div className="flex items-start">
          <Info className="w-5 h-5 text-[var(--info-dark)] mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-[var(--neutral-900)] text-sm">Estimation Disclaimer</h4>
            <p className="text-xs text-[var(--neutral-700)] mt-1">
              These estimates are approximations based on requirement density and complexity analysis (BR-13).
              Actual development costs and timelines may vary significantly based on team expertise,
              technology stack, and project-specific factors. Estimates should be used as a reference only.
            </p>
          </div>
        </div>
      </div>

      {/* Visualization */}
      <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
        <h3 className="text-lg font-semibold text-[var(--neutral-900)] mb-4">Complexity Distribution</h3>

        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-[var(--neutral-500)]">Low Complexity</span>
              <span className="font-medium">0-30</span>
            </div>
            <div className="w-full bg-[var(--card-border)] rounded-full h-2">
              <div
                className="bg-[var(--success-main)] h-2 rounded-full"
                style={{ width: `${Math.max(5, metrics.complexityScore < 30 ? 30 : 0)}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-[var(--neutral-500)]">Medium Complexity</span>
              <span className="font-medium">31-70</span>
            </div>
            <div className="w-full bg-[var(--card-border)] rounded-full h-2">
              <div
                className="bg-[var(--warning-main)] h-2 rounded-full"
                style={{
                  width: `${metrics.complexityScore > 30 && metrics.complexityScore <= 70 ? metrics.complexityScore - 30 : metrics.complexityScore > 70 ? 40 : 0}%`,
                  marginLeft: `${metrics.complexityScore > 30 ? Math.max(0, 30) : 0}%`
                }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-[var(--neutral-500)]">High Complexity</span>
              <span className="font-medium">71-100</span>
            </div>
            <div className="w-full bg-[var(--card-border)] rounded-full h-2">
              <div
                className="bg-[var(--error-main)] h-2 rounded-full"
                style={{
                  width: `${metrics.complexityScore > 70 ? metrics.complexityScore - 70 : 0}%`,
                  marginLeft: `${metrics.complexityScore > 70 ? 70 : 0}%`
                }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostComplexityPrediction;