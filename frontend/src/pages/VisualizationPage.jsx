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
import PlantUMLViewer from '../components/PlantUMLViewer';
import { ieeeDiagramsAPI, documentAPI, diagramsAPI } from '../services/api';

const VisualizationPage = () => {
  const { documentId } = useParams(); // Revert back to documentId
  const navigate = useNavigate();

  const [diagramType, setDiagramType] = useState('usecase');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [scenarios, setScenarios] = useState([]);
  const [currentDiagram, setCurrentDiagram] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [error, setError] = useState(null);
  const [compliance, setCompliance] = useState(null);
  
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

  // Fetch IEEE-compliant diagram when selected document changes
  useEffect(() => {
    if (!selectedDocument || selectedDocument === 'undefined' || selectedDocument === '') {
      console.log('No valid document selected, showing document selector');
      setError('Please select a document to visualize.');
      setLoading(false);
      return;
    }
    
    // Try to fetch existing diagrams first
    const fetchExistingDiagram = async () => {
      try {
        // For now, we'll just set loading to false and let user generate new diagram
        setCurrentDiagram(null);
        setLoading(false);
      } catch (err) {
        console.error('Diagram fetch error:', err);
        setError('Failed to load diagram. Please generate a new one.');
        toast.error('Could not load diagram');
        setLoading(false);
      }
    };
    
    fetchExistingDiagram();
  }, [selectedDocument, diagramType]);

  // Fetch available scenarios (sequence diagram scenarios) when switching to sequence tab
  useEffect(() => {
    if (diagramType !== 'sequence' || !selectedDocument || selectedDocument === 'undefined' || selectedDocument === '') return;
    
    const fetchScenarios = async () => {
      try {
        const res = await diagramsAPI.getScenarios(selectedDocument);
        const scenarioList = res.data.scenarios || [];
        setScenarios(scenarioList);
        if (scenarioList.length > 0 && !selectedScenario) {
          setSelectedScenario(scenarioList[0].id);
        }
      } catch (err) {
        console.error('Scenarios fetch error:', err);
        setScenarios([]);
      }
    };
    
    fetchScenarios();
  }, [diagramType, selectedDocument]);

  // Generate IEEE-compliant diagram
  const handleGenerateDiagram = async () => {
    if (!selectedDocument) {
      toast.error('Please select a document first');
      return;
    }
    
    setGenerating(true);
    setError(null);
    
    try {
      const response = await ieeeDiagramsAPI.generateDiagram(
        selectedDocument,
        diagramType,
        selectedScenario || null
      );
      
      // Access the actual response data from axios response
      const data = response.data;
      
      if (data.success) {
        setCurrentDiagram({
          mermaid_syntax: data.plantuml_syntax,
          diagram_id: data.diagram_id,
          compliance: data.compliance
        });
        setCompliance(data.compliance);
        toast.success(`IEEE-compliant ${diagramType} diagram generated successfully`);
        
        if (data.compliance?.warning) {
          toast.warning(data.compliance.warning);
        }
      } else {
        setError(data.error || 'Failed to generate diagram');
        toast.error(data.error || 'Failed to generate diagram');
      }
    } catch (err) {
      console.error('Diagram generation error:', err);
      setError('Failed to generate diagram. Please try again.');
      toast.error('Could not generate diagram');
    } finally {
      setGenerating(false);
    }
  };

  // Handle diagram type change
  const handleDiagramTypeChange = (newType) => {
    setDiagramType(newType);
    setCurrentDiagram(null); // Reset current diagram when type changes
  };

  // Handle document selection
  const handleDocumentChange = (e) => {
    const documentId = e.target.value;
    setSelectedDocument(documentId);
    navigate(`/visualization/${documentId}`);
  };

  // Handle zoom controls
  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 10, 200));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 10, 50));
  const handleResetZoom = () => setZoomLevel(100);

  // Export PlantUML as PNG for PDF generation
  const handleExportPlantUML = async () => {
    if (!currentDiagram?.plantuml_syntax) {
      toast.error('No PlantUML syntax to export');
      return;
    }
    
    try {
      const response = await ieeeDiagramsAPI.renderPlantUMLToPNG(currentDiagram.plantuml_syntax);
      
      if (response.success && response.png_base64) {
        // Convert base64 to blob and download
        const byteCharacters = atob(response.png_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'image/png' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${diagramType}_diagram.png`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('PlantUML PNG exported for PDF generation');
      } else {
        // Fallback to PlantUML syntax export
        const blob = new Blob([currentDiagram.plantuml_syntax], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${diagramType}_diagram.puml`;
        a.click();
        URL.revokeObjectURL(url);
        toast.warning('PNG rendering failed, exported PlantUML syntax instead');
      }
    } catch (err) {
      console.error('PlantUML rendering error:', err);
      // Fallback to PlantUML syntax export
      const blob = new Blob([currentDiagram.plantuml_syntax], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${diagramType}_diagram.puml`;
      a.click();
      URL.revokeObjectURL(url);
      toast.warning('PNG rendering failed, exported PlantUML syntax instead');
    }
  };

  // Export SVG from Mermaid (for interactive use)
  const handleExportSVG = () => {
    const svgElement = document.querySelector('.mermaid svg');
    if (!svgElement) {
      toast.error('No SVG element found to export');
      return;
    }
    
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${diagramType}_diagram.svg`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('SVG exported (Mermaid rendering)');
  };

  // Get current diagram string for display
  const currentDiagramString = currentDiagram?.mermaid_syntax || '';
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
          <div className="flex gap-2">
            <button
              onClick={handleExportSVG}
              disabled={!currentDiagramString}
              className="flex items-center px-4 py-2 bg-[var(--success-main)] text-white rounded-lg hover:bg-[var(--success-hover)] disabled:opacity-50"
            >
              <Download className="w-4 h-4 mr-2" />
              Export SVG (Mermaid)
            </button>
            <button
              onClick={handleExportPlantUML}
              disabled={!currentDiagramString}
              className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] disabled:opacity-50"
            >
              <Download className="h-4 w-4 mr-2" />
              Export PlantUML (PDF)
            </button>
          </div>
        </div>

        {/* Document Selector */}
        {!selectedDocument && (
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="h-5 w-5 text-[var(--text-secondary)]" />
              <h3 className="text-lg font-semibold text-[var(--text-primary)]">Select Document</h3>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-[var(--text-secondary)]">
                Document:
              </label>
              <select
                value={selectedDocument}
                onChange={handleDocumentChange}
                className="flex-1 px-4 py-2 bg-[var(--content-bg)] border border-[var(--card-border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)]"
              >
                <option value="">Select a document...</option>
                {documents.map((doc) => (
                  <option key={doc.doc_id} value={doc.doc_id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>
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
                onClick={handleGenerateDiagram}
                disabled={generating || !selectedDocument}
                className="flex items-center px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] disabled:opacity-50"
              >
                {generating ? 'Generating...' : 'Generate IEEE-Compliant Diagram'}
              </button>
            </div>

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

        {/* Compliance warnings */}
        {compliance?.warning && (
          <div className="mb-6 bg-[var(--warning-light)]/20 border-l-4 border-[var(--warning-main)] p-4 rounded">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-3" />
              <p className="text-sm text-[var(--warning-main)]">
                ⚠️ {compliance.warning}
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
            {compliance && (
              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                <span className="mr-4">BR-11 Compliant: {compliance.br_11_compliant ? '✓' : '✗'}</span>
                <span>BR-12 Compliant: {compliance.br_12_compliant ? '✓' : '✗'}</span>
              </div>
            )}
          </div>
          <div className="p-8 min-h-[500px] flex items-center justify-center">
            {loading || generating ? (
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--primary-main)] mb-4" />
                <p className="text-[var(--text-secondary)]">Generating IEEE-compliant diagram...</p>
              </div>
            ) : error ? (
              <div className="text-center text-[var(--error-main)]">
                <AlertTriangle className="h-12 w-12 mx-auto mb-4" />
                <p>{error}</p>
                <button
                  onClick={handleGenerateDiagram}
                  className="mt-4 px-4 py-2 bg-[var(--primary-main)] text-white rounded-lg"
                >
                  Generate Diagram
                </button>
              </div>
            ) : !selectedDocument ? (
              <div className="text-center text-[var(--text-secondary)]">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Please select a document to visualize.</p>
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
                <p>No diagram available. Click "Generate IEEE-Compliant Diagram" to create one.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisualizationPage;