import React, { useState } from 'react';
import { DocumentTextIcon, ExclamationTriangleIcon, LightBulbIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const DocumentAnalysis = () => {
  const [inputText, setInputText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('semantic');

  const handleAnalyze = async () => {
    if (!inputText.trim()) {
      alert('Please enter some text to analyze');
      return;
    }

    setIsLoading(true);
    try {
      // In a real implementation, this would call the backend API
      // For demo purposes, we'll simulate the response
      const response = await fetch('http://localhost:8000/api/analysis/full', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          semantic_request: { text: inputText, analysis_type: 'semantic' },
          predictive_request: { text: inputText, analysis_type: 'predictive' }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisResult(data);
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      // For demo purposes, create a mock response
      setAnalysisResult({
        semantic_analysis: {
          id: 'demo1',
          text: inputText,
          entities: [
            { text: 'user', label: 'ROLE', description: 'System role' },
            { text: 'login', label: 'ACTION', description: 'Authentication process' }
          ],
          relations: [],
          ambiguities: [
            { term: 'some', description: 'Vague quantifier', context: 'The system shall handle some requests' }
          ],
          confidence_score: 0.75,
          processed_at: new Date().toISOString()
        },
        predictive_analysis: {
          id: 'demo2',
          text: inputText,
          complexity_score: 65,
          estimated_effort_hours: 12.5,
          risk_level: 'medium',
          recommendations: [
            'Define specific authentication requirements',
            'Specify error handling procedures',
            'Clarify performance expectations'
          ],
          processed_at: new Date().toISOString()
        },
        overall_confidence: 0.78,
        generated_at: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setAnalysisResult(null);
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)] py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="lg:flex lg:items-center lg:justify-between">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-[var(--neutral-900)] sm:truncate sm:text-3xl sm:tracking-tight">
              Document Analysis
            </h2>
            <p className="mt-2 text-sm text-[var(--neutral-600)]">
              Analyze textual requirements for semantic content and predictive insights
            </p>
          </div>
        </div>

        <div className="mt-6 bg-[var(--card-bg)] shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="grid grid-cols-1 gap-6">
              <div>
                <label htmlFor="document-input" className="block text-sm font-medium text-[var(--neutral-900)]">
                  Enter Requirements Text
                </label>
                <div className="mt-1">
                  <textarea
                    id="document-input"
                    rows={8}
                    className="shadow-sm focus:ring-[var(--primary-main)] focus:border-[var(--primary-main)] mt-1 block w-full sm:text-sm border border-[var(--card-border)] rounded-md p-3 bg-[var(--card-bg)] text-[var(--text-primary)]"
                    placeholder="Paste or type your requirements text here..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isLoading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-[var(--primary-main)] hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--primary-main)] disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                      Analyze
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleClear}
                  className="inline-flex items-center px-4 py-2 border border-[var(--card-border)] text-sm font-medium rounded-md shadow-sm text-[var(--neutral-900)] bg-[var(--card-bg)] hover:bg-[var(--surface-bg)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--accent-main)]"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        {analysisResult && (
          <div className="mt-6 space-y-6">
            {/* Analysis Tabs */}
            <div className="bg-[var(--card-bg)] shadow rounded-lg">
              <div className="border-b border-[var(--card-border)]">
                <nav className="-mb-px flex space-x-8 px-4">
                  <button
                    onClick={() => setActiveTab('semantic')}
                    className={`${
                      activeTab === 'semantic'
                        ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                        : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                  >
                    Semantic Analysis
                  </button>
                  <button
                    onClick={() => setActiveTab('predictive')}
                    className={`${
                      activeTab === 'predictive'
                        ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                        : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                  >
                    Predictive Analysis
                  </button>
                  <button
                    onClick={() => setActiveTab('combined')}
                    className={`${
                      activeTab === 'combined'
                        ? 'border-[var(--primary-main)] text-[var(--primary-main)]'
                        : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--card-border)]'
                    } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                  >
                    Combined Results
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'semantic' && analysisResult?.semantic_analysis && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-lg font-medium text-[var(--text-primary)]">Detected Entities</h3>
                      <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {(analysisResult.semantic_analysis.entities || []).map((entity, index) => (
                          <div key={index} className="bg-[var(--surface-bg)] p-4 rounded-lg">
                            <div className="flex items-center">
                              <DocumentTextIcon className="h-5 w-5 text-[var(--primary-main)]" />
                              <span className="ml-2 font-medium">{entity.text}</span>
                            </div>
                            <div className="mt-1 text-sm text-[var(--text-secondary)]">{entity.label}</div>
                            <div className="mt-1 text-xs text-[var(--text-secondary)]">{entity.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-[var(--neutral-900)]">Identified Ambiguities</h3>
                      <div className="mt-2">
                        {(analysisResult.semantic_analysis.ambiguities || []).length > 0 ? (
                          <ul className="space-y-3">
                            {(analysisResult.semantic_analysis.ambiguities || []).map((ambiguity, index) => (
                              <li key={index} className="flex items-start">
                                <ExclamationTriangleIcon className="h-5 w-5 text-[var(--warning-main)] mt-0.5 flex-shrink-0" />
                                <div className="ml-3">
                                  <p className="text-sm font-medium text-[var(--text-primary)]">{ambiguity.term}</p>
                                  <p className="text-sm text-[var(--text-secondary)]">{ambiguity.description}</p>
                                  <p className="mt-1 text-xs text-[var(--text-secondary)]">Context: "{ambiguity.context}"</p>
                                </div>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <div className="text-sm text-[var(--neutral-600)]">No ambiguities detected in the text.</div>
                        )}
                      </div>
                    </div>

                    <div className="bg-[var(--card-bg)] p-4 rounded-lg">
                      <div className="flex items-center">
                        <LightBulbIcon className="h-5 w-5 text-[var(--primary-main)]" />
                        <span className="ml-2 font-medium">Analysis Confidence</span>
                      </div>
                      <div className="mt-2">
                        <div className="w-full bg-[var(--surface-bg)] rounded-full h-2.5">
                          <div
                            className="bg-[var(--primary-main)] h-2.5 rounded-full"
                            style={{ width: `${(analysisResult.semantic_analysis.confidence_score || 0) * 100}%` }}
                          ></div>
                        </div>
                        <div className="mt-1 text-sm text-[var(--text-secondary)]">
                          Confidence: {((analysisResult.semantic_analysis.confidence_score || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'predictive' && analysisResult?.predictive_analysis && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <div className="text-sm font-medium text-[var(--text-secondary)]">Complexity Score</div>
                        <div className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                          {(analysisResult.predictive_analysis.complexity_score || 0).toFixed(1)}/100
                        </div>
                        <div className="mt-2">
                          <div className="w-full bg-[var(--surface-bg)] rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                (analysisResult.predictive_analysis.complexity_score || 0) < 40
                                  ? 'bg-[var(--success-main)]'
                                  : (analysisResult.predictive_analysis.complexity_score || 0) < 70
                                  ? 'bg-[var(--warning-main)]'
                                  : 'bg-[var(--error-main)]'
                              }`}
                              style={{ width: `${(analysisResult.predictive_analysis.complexity_score || 0)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>

                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <div className="text-sm font-medium text-[var(--text-secondary)]">Estimated Effort</div>
                        <div className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                          {(analysisResult.predictive_analysis.estimated_effort_hours || 0).toFixed(1)} hrs
                        </div>
                        <div className="mt-1 text-sm text-[var(--text-secondary)]">Development time</div>
                      </div>

                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <div className="text-sm font-medium text-[var(--text-secondary)]">Risk Level</div>
                        <div className={`mt-1 text-2xl font-semibold ${
                          analysisResult.predictive_analysis.risk_level === 'low' ? 'text-[var(--success-main)]' :
                          analysisResult.predictive_analysis.risk_level === 'medium' ? 'text-[var(--warning-main)]' :
                          analysisResult.predictive_analysis.risk_level === 'high' ? 'text-[var(--error-main)]' :
                          'text-[var(--error-main)]'
                        }`}>
                          {(analysisResult.predictive_analysis.risk_level || 'unknown').charAt(0).toUpperCase() + (analysisResult.predictive_analysis.risk_level || 'unknown').slice(1)}
                        </div>
                      </div>

                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <div className="text-sm font-medium text-[var(--text-secondary)]">Confidence</div>
                        <div className="mt-1 text-2xl font-semibold text-[var(--text-primary)]">
                          {((analysisResult.predictive_analysis.confidence_score || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-[var(--text-primary)]">Recommendations</h3>
                      <div className="mt-2">
                        <ul className="space-y-2">
                          {(analysisResult.predictive_analysis.recommendations || []).map((rec, index) => (
                            <li key={index} className="flex items-start">
                              <LightBulbIcon className="h-5 w-5 text-[var(--primary-main)] mt-0.5 flex-shrink-0" />
                              <span className="ml-2 text-sm text-[var(--text-secondary)]">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'combined' && analysisResult && (
                  <div className="space-y-6">
                    <div className="bg-[var(--surface-bg)] p-4 rounded-lg">
                      <div className="flex items-center">
                        <LightBulbIcon className="h-5 w-5 text-[var(--primary-main)]" />
                        <span className="ml-2 font-medium">Overall Analysis Confidence</span>
                      </div>
                      <div className="mt-2">
                        <div className="w-full bg-[var(--surface-bg)] rounded-full h-2.5">
                          <div
                            className="bg-[var(--primary-main)] h-2.5 rounded-full"
                            style={{ width: `${(analysisResult.overall_confidence || 0) * 100}%` }}
                          ></div>
                        </div>
                        <div className="mt-1 text-sm text-[var(--text-secondary)]">
                          Combined Confidence: {((analysisResult.overall_confidence || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <h4 className="text-md font-medium text-[var(--text-primary)]">Semantic Insights</h4>
                        <div className="mt-2">
                          <p className="text-sm text-[var(--text-secondary)]">
                            Found {(analysisResult.semantic_analysis?.entities?.length || 0)} entities and{' '}
                            {(analysisResult.semantic_analysis?.ambiguities?.length || 0)} ambiguities.
                          </p>
                        </div>
                      </div>

                      <div className="bg-[var(--card-bg)] p-4 rounded-lg shadow">
                        <h4 className="text-md font-medium text-[var(--text-primary)]">Predictive Insights</h4>
                        <div className="mt-2">
                          <p className="text-sm text-[var(--text-secondary)]">
                            Complexity: {(analysisResult.predictive_analysis?.complexity_score?.toFixed(1) || 0)}/100,{' '}
                            Effort: {(analysisResult.predictive_analysis?.estimated_effort_hours?.toFixed(1) || 0)} hours
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Visualization Link */}
            <div className="bg-[var(--card-bg)] shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-[var(--text-primary)]">Generate Visualization</h3>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">
                  Create visual representations of your analyzed requirements.
                </p>
                <div className="mt-4">
                  <button
                    type="button"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-[var(--primary-main)] hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--primary-main)]"
                    onClick={() => window.location.href = '/visualization'}
                  >
                    <DocumentTextIcon className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                    Create Visualization
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentAnalysis;