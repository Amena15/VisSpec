import React, { useState, useEffect } from 'react';
import {
  Eye,
  FileText,
  ArrowLeft,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Play,
  Settings,
  ChevronDown
} from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { diagramsAPI, visualizationAPI } from '../services/api';
import { toast } from 'sonner';

const VisualizationGenerator = () => {
  const { id } = useParams();
  const [activeView, setActiveView] = useState('sequence');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [zoomLevel, setZoomLevel] = useState(100);
  const [showSettings, setShowSettings] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [diagramData, setDiagramData] = useState(null);
  const [document, setDocument] = useState(null);

  useEffect(() => {
    if (id) {
      loadDocumentAndDiagrams();
    }
  }, [id]);

  const loadDocumentAndDiagrams = async () => {
    setIsLoading(true);
    try {
      // Load scenarios from API
      const scenariosResponse = await diagramsAPI.getScenarios(id);
      setScenarios(scenariosResponse.data || []);

      // Load diagram data based on active view
      if (activeView === 'sequence') {
        const useCaseResponse = await diagramsAPI.getUseCaseDiagram(id);
        setDiagramData({
          usecase: useCaseResponse.data,
          sequence: null
        });
      } else {
        const sequenceResponse = await diagramsAPI.getSequenceDiagram(id, selectedScenario);
        setDiagramData({
          usecase: null,
          sequence: sequenceResponse.data
        });
      }
    } catch (error) {
      console.error('Failed to load diagrams:', error);
      toast.error('Failed to load diagram data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (id && activeView) {
      loadDocumentAndDiagrams();
    }
  }, [id, activeView, selectedScenario]);

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 10, 150));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 10, 50));
  };

  const handleResetZoom = () => {
    setZoomLevel(100);
  };

  const handleDownload = () => {
    try {
      const diagramElement = document.querySelector('.mermaid, .diagram-container svg');
      if (diagramElement) {
        const svgData = new XMLSerializer().serializeToString(diagramElement);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        
        img.onload = function() {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
          
          const link = document.createElement('a');
          link.download = `${activeView}-diagram.png`;
          link.href = canvas.toDataURL();
          link.click();
        };
        
        img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
        toast.success('Diagram downloaded successfully!');
      } else {
        toast.error('No diagram to download');
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download diagram');
    }
  };

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <Link to="/analysis" className="text-[#4F6D7A] hover:text-[#4338CA] mr-4">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-[#111827]">Visualizations</h1>
                <p className="text-[#6B7280]">Automated UML diagram generation from requirements</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleDownload}
                className="flex items-center px-4 py-2 bg-white border border-[#E5E7EB] rounded-lg text-[#4F6D7A] hover:bg-[#F9FAFB] transition-colors"
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </button>
            </div>
          </div>

          {/* Controls */}
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
              <div className="flex space-x-4">
                <div className="flex space-x-1 bg-[#F3F4F6] p-1 rounded-lg">
                  <button
                    onClick={() => setActiveView('sequence')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeView === 'sequence'
                        ? 'bg-white text-[#4F6D7A] shadow-sm'
                        : 'text-[#6B7280] hover:text-[#4F6D7A]'
                    }`}
                  >
                    Sequence View
                  </button>
                  <button
                    onClick={() => setActiveView('usecase')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeView === 'usecase'
                        ? 'bg-white text-[#4F6D7A] shadow-sm'
                        : 'text-[#6B7280] hover:text-[#4F6D7A]'
                    }`}
                  >
                    Use Case View
                  </button>
                </div>

                <div className="relative">
                  <select
                    value={selectedScenario}
                    onChange={(e) => setSelectedScenario(e.target.value)}
                    className="appearance-none bg-white border border-[#E5E7EB] rounded-lg px-4 py-2 pr-8 text-[#1F2933] focus:ring-2 focus:ring-[#4F6D7A] focus:border-transparent"
                  >
                    <option value="">Select Scenario to Visualize</option>
                    {scenarios.map(scenario => (
                      <option key={scenario.id} value={scenario.id}>
                        {scenario.name} ({scenario.steps} steps)
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={handleZoomOut}
                  className="p-2 rounded-lg border border-[#E5E7EB] text-[#4F6D7A] hover:bg-[#F9FAFB] transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-[#6B7280]">{zoomLevel}%</span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 rounded-lg border border-[#E5E7EB] text-[#4F6D7A] hover:bg-[#F9FAFB] transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleResetZoom}
                  className="p-2 rounded-lg border border-[#E5E7EB] text-[#4F6D7A] hover:bg-[#F9FAFB] transition-colors"
                  title="Reset Zoom"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 rounded-lg border border-[#E5E7EB] text-[#4F6D7A] hover:bg-[#F9FAFB] transition-colors"
                  title="Settings"
                >
                  <Settings className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Diagram Visualization */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-[#E5E7EB]">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-[#111827]">
                    {activeView === 'sequence' ? 'Sequence Diagram' : 'Use Case Diagram'}
                  </h2>
                  <p className="text-sm text-[#6B7280]">
                    {activeView === 'sequence'
                      ? diagramData.sequence.description
                      : diagramData.usecase.description}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs px-2 py-1 bg-[#E0E7FF] text-[#4F46E5] rounded-full">
                    {selectedScenario ? scenarios.find(s => s.id === selectedScenario)?.name : 'All Scenarios'}
                  </span>
                </div>
              </div>
            </div>

            <div className="p-8">
              <div
                className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg p-8 flex items-center justify-center min-h-[400px]"
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'center' }}
              >
                {/* Use Case Diagram Sample - Updated with Screenshot */}
                <div className="text-center w-full">
                  <h3 className="text-lg font-semibold text-[#111827] mb-4">
                    {activeView === 'sequence' ? 'Sequence Diagram' : 'Use Case Diagram'}
                  </h3>
                  
                  {/* Display the screenshot */}
                  <div className="flex justify-center">
                    <img 
                      src="/usecase-diagram-sample.png" 
                      alt={activeView === 'sequence' ? 'Sequence Diagram Sample' : 'Use Case Diagram Sample'} 
                      className="max-w-full max-h-[300px] object-contain border border-[#E5E7EB] rounded-lg"
                    />
                  </div>
                  
                  <p className="text-[#6B7280] max-w-md mx-auto mt-4">
                    {activeView === 'sequence'
                      ? 'Interactive sequence diagram showing the flow between system components'
                      : 'High-level use case diagram showing system actors and their interactions'}
                  </p>

                  <div className="mt-4 flex justify-center">
                    <button className="bg-[#4F6D7A] text-white px-4 py-2 rounded-lg hover:bg-[#4338CA] transition-colors flex items-center">
                      <Play className="h-4 w-4 mr-2" />
                      Generate Diagram
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Diagram Code Panel */}
          <div className="mt-6 bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 bg-[#F3F4F6] border-b border-[#E5E7EB]">
              <h3 className="text-sm font-medium text-[#111827]">Generated Mermaid.js Code</h3>
            </div>
            <div className="p-4">
              <pre className="bg-[#1F2933] text-[#F9FAFB] p-4 rounded-lg text-sm overflow-x-auto">
                {activeView === 'sequence' ? diagramData.sequence.code : diagramData.usecase.code}
              </pre>
            </div>
          </div>

          {/* Business Rules */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-[#111827] mb-4">Validation Rules</h3>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <div className="bg-[#E0E7FF] rounded-full p-1 mr-3 mt-0.5">
                    <FileText className="h-4 w-4 text-[#4F46E5]" />
                  </div>
                  <div>
                    <p className="font-medium text-[#111827]">BR-11: Text-Based Diagrams</p>
                    <p className="text-sm text-[#6B7280]">Diagrams strictly reflect the text provided; no hallucinated actors</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <div className="bg-[#E0E7FF] rounded-full p-1 mr-3 mt-0.5">
                    <FileText className="h-4 w-4 text-[#4F46E5]" />
                  </div>
                  <div>
                    <p className="font-medium text-[#111827]">BR-12: Step Limit</p>
                    <p className="text-sm text-[#6B7280]">Sequence diagrams limited to 15 steps per scenario for readability</p>
                  </div>
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-[#111827] mb-4">Scenario Details</h3>
              <div className="space-y-3">
                {scenarios.map(scenario => (
                  <div key={scenario.id} className="flex items-center justify-between p-3 bg-[#F9FAFB] rounded-lg">
                    <span className="text-[#111827]">{scenario.name}</span>
                    <span className="text-xs px-2 py-1 bg-[#E0E7FF] text-[#4F46E5] rounded-full">
                      {scenario.steps} steps
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VisualizationGenerator;