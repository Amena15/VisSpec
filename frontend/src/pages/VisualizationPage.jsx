import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Filter,
  ChevronDown,
  AlertTriangle,
  FileText
} from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import DiagramViewer from '../components/DiagramViewer';
import { diagramsAPI, documentAPI } from '../services/api'; // Use new diagramsAPI methods (Module 4)

const VisualizationPage = () => {
  const { documentId } = useParams(); // or projectId – adjust to your routing
  const navigate = useNavigate();

  const [diagramType, setDiagramType] = useState('usecase');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [scenarios, setScenarios] = useState([]);
  const [useCaseDiagram, setUseCaseDiagram] = useState(null);
  const [sequenceDiagram, setSequenceDiagram] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [error, setError] = useState(null);
  const [stepLimitWarning, setStepLimitWarning] = useState(false);
  
  // Document selection state
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(documentId || '');

  // Fetch documents on mount
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const res = await documentAPI.getAll();
        setDocuments(res.data || []);
      } catch (err) {
        console.error('Documents fetch error:', err);
        toast.error('Could not load documents');
      }
    };
    fetchDocuments();
  }, []);

  // Fetch Use Case diagram when selectedDocument changes
  useEffect(() => {
    if (!selectedDocument || selectedDocument === 'undefined' || selectedDocument === '') {
      console.log('No valid document selected, showing document selector');
      setError('Please select a document to visualize.');
      setLoading(false);
      return;
    }
    
    const fetchUseCase = async () => {
      console.log('Fetching use case diagram for document:', selectedDocument);
      setLoading(true);
      try {
        const res = await diagramsAPI.getUseCaseDiagram(selectedDocument);
        console.log('Use case API response:', res);
        console.log('Response data:', res.data);
        
        if (res.data.error === 'No validated requirements found') {
          setError('This document has no validated requirements. Please validate the document first.');
          toast.info('No validated requirements found for this document');
          setUseCaseDiagram(res.data);
        } else {
          console.log('Setting use case diagram:', res.data);
          setUseCaseDiagram(res.data);
          setError(null);
          console.log('Use case diagram set successfully');
        }
      } catch (err) {
        console.error('Use case fetch error:', err);
        setError('Failed to load Use Case diagram. Ensure document has validated requirements.');
        toast.error('Could not load Use Case diagram');
      } finally {
        console.log('Setting loading to false');
        setLoading(false);
      }
    };
    fetchUseCase();
  }, [selectedDocument]);

  // Fetch available scenarios (sequence diagram scenarios) only when switching to sequence tab
  useEffect(() => {
    if (diagramType !== 'sequence' || !selectedDocument || selectedDocument === 'undefined' || selectedDocument === '') return;
    const fetchScenarios = async () => {
      setGenerating(true);
      try {
        const res = await diagramsAPI.getScenarios(selectedDocument);
        const scenarioList = res.data.scenarios || [];
        setScenarios(scenarioList);
        if (scenarioList.length > 0 && !selectedScenario) {
          setSelectedScenario(scenarioList[0].id);
        } else if (scenarioList.length === 0) {
          setSequenceDiagram(null);
          setError('No scenarios detected. Run validation on your document first.');
        }
      } catch (err) {
        console.error('Scenarios fetch error:', err);
        setScenarios([]);
        setError('Could not detect scenarios. Make sure requirements are validated.');
      } finally {
        setGenerating(false);
      }
    };
    fetchScenarios();
  }, [diagramType, selectedDocument]);

  // Fetch Sequence diagram when selected scenario changes
  useEffect(() => {
    if (diagramType !== 'sequence' || !selectedScenario || !selectedDocument || selectedDocument === 'undefined' || selectedDocument === '') return;
    const fetchSequence = async () => {
      setGenerating(true);
      setStepLimitWarning(false);
      try {
        const res = await diagramsAPI.getSequenceDiagram(selectedDocument, selectedScenario);
        setSequenceDiagram(res.data);
        setError(null);
        // Check step limit (BR-12)
        if (res.data.truncated) {
          setStepLimitWarning(true);
          toast.warning('Diagram truncated to 15 steps (BR-12)');
        }
      } catch (err) {
        console.error('Sequence diagram fetch error:', err);
        setSequenceDiagram(null);
        setError(`Failed to load diagram for scenario "${selectedScenario}".`);
      } finally {
        setGenerating(false);
      }
    };
    fetchSequence();
  }, [diagramType, selectedScenario, selectedDocument]);

  // Zoom controls
  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 10, 50));
  const handleResetZoom = () => setZoomLevel(100);

  // Export current diagram as Mermaid format
  const handleExportMermaid = () => {
    let diagramCode = null;
    
    if (diagramType === 'usecase') {
      diagramCode = useCaseDiagram?.mermaid_syntax;
    } else if (diagramType === 'sequence') {
      diagramCode = sequenceDiagram?.mermaid_syntax;
    }
    
    if (!diagramCode) {
      toast.error('No diagram to export');
      return;
    }
    const blob = new Blob([diagramCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${diagramType}_diagram_${Date.now()}.mermaid`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Determine what to render - use Mermaid syntax only
  const getCurrentDiagramString = () => {
    if (diagramType === 'usecase') return useCaseDiagram?.mermaid_syntax || null;
    return sequenceDiagram?.mermaid_syntax || null;
  };

  const currentDiagramString = getCurrentDiagramString();
  const hasNoScenarios = diagramType === 'sequence' && scenarios.length === 0 && !generating;

  return (
    <div className="min-h-screen bg-[var(--content-bg)] py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/analysis-results')}
              className="p-2 rounded-lg hover:bg-[var(--card-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">Visualization</h1>
              <p className="text-sm text-[var(--text-secondary)]">Generated from validated requirements</p>
            </div>
          </div>
          <button
            onClick={handleExportMermaid}
            disabled={!currentDiagramString}
            className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] disabled:opacity-50"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Diagram
          </button>
        </div>

        {/* Document Selector */}
        {!documentId && (
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="h-5 w-5 text-[var(--text-secondary)]" />
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Select Document</h3>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-[var(--text-secondary)]">
                Document:
              </label>
              <div className="relative">
                <select
                  value={selectedDocument}
                  onChange={(e) => setSelectedDocument(e.target.value)}
                  className="appearance-none bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg px-4 py-2 pr-8 text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-main)] min-w-[300px]"
                >
                  <option value="">Select a document...</option>
                  {documents.map(doc => (
                    <option key={doc.doc_id || doc.filename || `doc-${Math.random()}`} value={doc.doc_id}>
                      {doc.filename || `Document ${doc.doc_id}`}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)] pointer-events-none" />
              </div>
            </div>
            {documents.length === 0 && !loading && (
              <div className="mt-4 p-3 bg-[var(--warning-light)]/20 border-l-4 border-[var(--warning-main)] rounded">
                <p className="text-sm text-[var(--warning-main)]">
                  No documents available. Upload a document first.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Controls */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setDiagramType('usecase')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  diagramType === 'usecase'
                    ? 'bg-[var(--primary-main)] text-white shadow-sm'
                    : 'bg-[var(--surface-bg)] text-[var(--text-secondary)] hover:text-[var(--primary-main)]'
                }`}
              >
                Use Case Diagram
              </button>
              <button
                onClick={() => setDiagramType('sequence')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  diagramType === 'sequence'
                    ? 'bg-[var(--primary-main)] text-white shadow-sm'
                    : 'bg-[var(--surface-bg)] text-[var(--text-secondary)] hover:text-[var(--primary-main)]'
                }`}
              >
                Sequence Diagram
              </button>
            </div>

            {diagramType === 'sequence' && scenarios.length > 0 && (
              <div className="flex items-center gap-3">
                <Filter className="h-4 w-4 text-[var(--text-secondary)]" />
                <label className="text-sm font-medium text-[var(--text-secondary)]">
                  Scenario:
                </label>
                <div className="relative">
                  <select
                    value={selectedScenario}
                    onChange={(e) => setSelectedScenario(e.target.value)}
                    className="appearance-none bg-[var(--surface-bg)] border border-[var(--card-border)] rounded-lg px-4 py-2 pr-8 text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-main)] min-w-[200px]"
                  >
                    {scenarios.map(sc => (
                      <option key={sc.id || sc.name || `scenario-${Math.random()}`} value={sc.id}>
                        {sc.name} ({sc.steps || '?'} steps)
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)] pointer-events-none" />
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <button
                onClick={handleZoomOut}
                className="p-2 rounded-lg border border-[var(--card-border)] hover:bg-[var(--surface-bg)]"
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <span className="text-sm text-[var(--text-secondary)]">{zoomLevel}%</span>
              <button
                onClick={handleZoomIn}
                className="p-2 rounded-lg border border-[var(--card-border)] hover:bg-[var(--surface-bg)]"
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                onClick={handleResetZoom}
                className="p-2 rounded-lg border border-[var(--card-border)] hover:bg-[var(--surface-bg)]"
                title="Reset Zoom"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Step limit warning */}
        {stepLimitWarning && (
          <div className="mb-6 bg-[var(--warning-light)]/20 border-l-4 border-[var(--warning-main)] p-4 rounded">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-3" />
              <p className="text-sm text-[var(--warning-main)]">
                ⚠️ Diagram exceeds 15 steps (BR‑12). Truncated for readability.
              </p>
            </div>
          </div>
        )}

        {/* Diagram Display */}
        <div className="bg-[var(--card-bg)] rounded-xl shadow-sm overflow-hidden">
          <div className="p-6 border-b border-[var(--card-border)]">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              {diagramType === 'sequence'
                ? (selectedScenario ? `Sequence: ${selectedScenario}` : 'Sequence Diagram')
                : 'Use Case Diagram'}
            </h2>
          </div>
          <div className="p-8 min-h-[500px] flex items-center justify-center">
            {loading || generating ? (
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--primary-main)] mb-4" />
                <p className="text-[var(--text-secondary)]">Generating diagram...</p>
              </div>
            ) : error ? (
              <div className="text-center text-[var(--error-main)]">
                <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                <p>{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-4 px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg"
                >
                  Retry
                </button>
              </div>
            ) : hasNoScenarios ? (
              <div className="text-center text-[var(--text-secondary)]">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No scenarios detected. Run validation on a document first.</p>
              </div>
            ) : currentDiagramString ? (
              <div className="w-full overflow-auto">
                <DiagramViewer
                  key={`${diagramType}-${selectedScenario || 'usecase'}`}
                  chartString={currentDiagramString}
                  zoomLevel={zoomLevel}
                  darkMode={false}
                />
              </div>
            ) : (
              <div className="text-center text-[var(--text-secondary)]">
                <p>No diagram available. Click "Generate" after validation.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisualizationPage;