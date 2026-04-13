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
  ChevronDown,
  CheckCircle,
  Clock,
  AlertTriangle,
  Sun,
  Moon,
  Grid3X3,
  Filter,
  AlertCircle
} from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import DiagramViewer from '../components/DiagramViewer';
import { documentAPI } from '../services/api';

const VisualizationPage = () => {
  const { documentId } = useParams(); // Get document ID from route params
  const navigate = useNavigate();
  const [diagramType, setDiagramType] = useState('usecase');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [zoomLevel, setZoomLevel] = useState(100);
  const [darkMode, setDarkMode] = useState(false); // Kept for functionality but UI element will be removed
  const [allScenariosView, setAllScenariosView] = useState(false);
  const [loading, setLoading] = useState(true);
  const [documentData, setDocumentData] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [diagramData, setDiagramData] = useState({
    sequence: {},
    usecase: {}
  });

  // Fetch document data and extract scenarios
  useEffect(() => {
    const fetchDocumentAndScenarios = async () => {
      try {
        setLoading(true);

        // In a real app, we would fetch the document data from the API
        // For now, we'll use mock data based on the requirements
        if (documentId) {
          const response = await documentAPI.getById(documentId);
          setDocumentData(response.data);

          // Extract scenarios from the document analysis
          const extractedScenarios = extractScenariosFromDocument(response.data);
          setScenarios(extractedScenarios);

          // Generate diagrams for each scenario
          const generatedDiagrams = generateDiagramsForScenarios(extractedScenarios);
          setDiagramData(generatedDiagrams);

          // Set the first scenario as default if none is selected
          if (extractedScenarios.length > 0 && !selectedScenario) {
            setSelectedScenario(extractedScenarios[0].id);
          }
        } else {
          // Mock data for demonstration
          const mockScenarios = [
            { id: 'login', name: 'Login Process', steps: 5, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] },
            { id: 'registration', name: 'User Registration', steps: 6, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] },
            { id: 'payment', name: 'Payment Processing', steps: 7, actors: ['Customer', 'Payment Gateway', 'Order Service', 'Inventory Service'] },
            { id: 'document-upload', name: 'Document Upload', steps: 4, actors: ['User', 'UI Layer', 'File Service', 'Storage'] },
            { id: 'data-backup', name: 'Data Backup', steps: 8, actors: ['Admin', 'Backup Service', 'Storage', 'Notification Service'] }
          ];

          setScenarios(mockScenarios);
          const generatedDiagrams = generateDiagramsForScenarios(mockScenarios);
          setDiagramData(generatedDiagrams);

          // Set the first scenario as default
          if (mockScenarios.length > 0 && !selectedScenario) {
            setSelectedScenario(mockScenarios[0].id);
          }
        }
      } catch (error) {
        console.error('Error fetching document data:', error);

        // Fallback to mock data if API call fails
        const mockScenarios = [
          { id: 'login', name: 'Login Process', steps: 5, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] },
          { id: 'registration', name: 'User Registration', steps: 6, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] },
          { id: 'payment', name: 'Payment Processing', steps: 7, actors: ['Customer', 'Payment Gateway', 'Order Service', 'Inventory Service'] },
          { id: 'document-upload', name: 'Document Upload', steps: 4, actors: ['User', 'UI Layer', 'File Service', 'Storage'] },
          { id: 'data-backup', name: 'Data Backup', steps: 8, actors: ['Admin', 'Backup Service', 'Storage', 'Notification Service'] }
        ];

        setScenarios(mockScenarios);
        const generatedDiagrams = generateDiagramsForScenarios(mockScenarios);
        setDiagramData(generatedDiagrams);

        // Set the first scenario as default
        if (mockScenarios.length > 0 && !selectedScenario) {
          setSelectedScenario(mockScenarios[0].id);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDocumentAndScenarios();
  }, [documentId]);

  // Extract scenarios from document analysis
  const extractScenariosFromDocument = (docData) => {
    // This would parse the document analysis results to extract scenarios
    // For now, returning mock data based on the document content
    // In a real implementation, this would analyze the document text to identify scenarios

    // Simulate checking if document has enough information for scenarios
    if (!docData || !docData.content || docData.content.length < 100) {
      // If document is too small or doesn't exist, return minimal scenarios
      return [];
    }

    // Parse document content to extract scenarios
    // This is a simplified implementation - in reality, this would use NLP techniques
    const content = docData.content || '';
    const detectedScenarios = [];

    // Look for common scenario patterns in the document
    if (content.toLowerCase().includes('login') || content.toLowerCase().includes('authenticate')) {
      detectedScenarios.push({ id: 'login', name: 'Login Process', steps: 5, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] });
    }

    if (content.toLowerCase().includes('register') || content.toLowerCase().includes('signup')) {
      detectedScenarios.push({ id: 'registration', name: 'User Registration', steps: 6, actors: ['User', 'UI Layer', 'Auth Service', 'Database'] });
    }

    if (content.toLowerCase().includes('payment') || content.toLowerCase().includes('checkout')) {
      detectedScenarios.push({ id: 'payment', name: 'Payment Processing', steps: 7, actors: ['Customer', 'Payment Gateway', 'Order Service', 'Inventory Service'] });
    }

    if (content.toLowerCase().includes('upload') || content.toLowerCase().includes('document')) {
      detectedScenarios.push({ id: 'document-upload', name: 'Document Upload', steps: 4, actors: ['User', 'UI Layer', 'File Service', 'Storage'] });
    }

    if (content.toLowerCase().includes('backup') || content.toLowerCase().includes('restore')) {
      detectedScenarios.push({ id: 'data-backup', name: 'Data Backup', steps: 8, actors: ['Admin', 'Backup Service', 'Storage', 'Notification Service'] });
    }

    // If no scenarios were detected, return an empty array
    if (detectedScenarios.length === 0) {
      return [];
    }

    // Only return detected scenarios
    return detectedScenarios;
  };

  // Generate diagrams for each scenario
  const generateDiagramsForScenarios = (scenarios) => {
    const sequenceDiagrams = {};
    const usecaseDiagram = generateUseCaseDiagram(scenarios);

    scenarios.forEach(scenario => {
      sequenceDiagrams[scenario.id] = generateSequenceDiagram(scenario);
    });

    return {
      sequence: sequenceDiagrams,
      usecase: usecaseDiagram
    };
  };

  // Generate sequence diagram for a scenario
  const generateSequenceDiagram = (scenario) => {
    // Create a mock sequence diagram based on scenario
    let code = `sequenceDiagram\n`;

    // Add participants (actors)
    scenario.actors.forEach(actor => {
      code += `    participant ${actor.replace(/\s+/g, '')} as ${actor}\n`;
    });

    // Add steps based on scenario type
    switch(scenario.id) {
      case 'login':
        code += `    User->>+UI Layer: Enter credentials\n    UI Layer->>+Auth Service: Validate credentials\n    Auth Service->>+Database: Query user data\n    Database-->>-Auth Service: Return user info\n    Auth Service-->>-UI Layer: Authentication result\n    UI Layer-->>-User: Login confirmation`;
        break;
      case 'registration':
        code += `    User->>+UI Layer: Enter registration details\n    UI Layer->>+Auth Service: Create account\n    Auth Service->>+Database: Store user data\n    Database-->>-Auth Service: Confirmation\n    Auth Service-->>-UI Layer: Account created\n    UI Layer-->>-User: Registration success`;
        break;
      case 'payment':
        code += `    Customer->>+Order Service: Initiate payment\n    Order Service->>+Payment Gateway: Process payment\n    Payment Gateway->>+Bank: Verify funds\n    Bank-->>-Payment Gateway: Verification result\n    Payment Gateway-->>-Order Service: Payment confirmed\n    Order Service-->>-Customer: Payment success`;
        break;
      case 'document-upload':
        code += `    User->>+UI Layer: Select file to upload\n    UI Layer->>+File Service: Upload file\n    File Service->>+Storage: Save file\n    Storage-->>-File Service: Confirmation\n    File Service-->>-UI Layer: Upload complete\n    UI Layer-->>-User: File uploaded`;
        break;
      case 'data-backup':
        code += `    Admin->>+Backup Service: Initiate backup\n    Backup Service->>+Storage: Create backup\n    Storage-->>-Backup Service: Backup complete\n    Backup Service->>+Notification Service: Send notification\n    Notification Service-->>-Admin: Backup completed`;
        break;
      default:
        // Generate generic steps if scenario not recognized
        for (let i = 1; i <= Math.min(scenario.steps, 15); i++) {
          code += `    ${scenario.actors[0]}->>${scenario.actors[1]}: Action ${i}\n`;
        }
    }

    return {
      title: `${scenario.name} Sequence Diagram`,
      code: code,
      description: `Shows the interaction flow for ${scenario.name}. Contains ${scenario.steps} steps.`,
      steps: scenario.steps
    };
  };

  // Generate use case diagram for all scenarios following UML 2.5 standards with PlantUML
  const generateUseCaseDiagram = (scenarios) => {
    let code = `@startuml\n`;
    code += `left to right direction\n`;
    code += `skinparam packageStyle rectangle\n\n`;

    // Define actors with proper UML stick figure notation
    code += `actor "Requirements Analyst\\n(Student/Developer)" as Analyst\n`;
    code += `actor "QA Manager\\n(Supervisor/Auditor)" as Manager\n\n`;

    // Define system boundary with rectangle
    code += `rectangle "Online Shopping System" {\n`;

    // Define use cases based on the actual scenarios provided
    const useCases = [];

    // Map scenarios to use cases
    scenarios.forEach((scenario, index) => {
      const ucId = `UC${index + 1}`;
      const ucName = scenario.name;
      useCases.push({ id: ucId, name: ucName });
      code += `  usecase "${ucName}" as ${ucId}\n`;
    });

    // If no scenarios provided, use default use cases
    if (scenarios.length === 0) {
      const defaultUseCasesArray = [
        { id: 'UC1', name: 'Authenticate User' },
        { id: 'UC2', name: 'Register New Account' },
        { id: 'UC3', name: 'Upload SRS Document' },
        { id: 'UC4', name: 'Validate SRS Requirements' },
        { id: 'UC5', name: 'Generate UML Diagrams' },
        { id: 'UC6', name: 'View Analysis Results' }
      ];

      defaultUseCasesArray.forEach(uc => {
        code += `  usecase "${uc.name}" as ${uc.id}\n`;
        useCases.push(uc);
      });
    }

    code += `}\n\n`;

    // Define relationships between actors and use cases following UML standards
    // Use SOLID lines WITHOUT arrowheads from actors to use cases
    code += `' Actor associations (solid lines, no arrows)\n`;

    if (scenarios.length > 0) {
      // Associate each use case with the appropriate actor based on scenario type
      // Skip authentication and basic operations (login, upload) as they are sub-use cases
      useCases.forEach((useCase, index) => {
        // Skip login and upload use cases - they are sub-use cases
        if (useCase.name.toLowerCase().includes('login') ||
            useCase.name.toLowerCase().includes('upload')) {
          return; // Skip adding association for login and upload
        }

        // Associate user-related use cases with Analyst actor (keeping register and backup)
        if (useCase.name.toLowerCase().includes('register') ||
            useCase.name.toLowerCase().includes('backup')) {
          code += `Analyst -- ${useCase.id}\n`;
        } else if (useCase.name.toLowerCase().includes('payment')) {
          code += `Manager -- ${useCase.id}\n`;
        } else {
          // Default to Analyst for other cases that are not login, upload, or payment
          code += `Analyst -- ${useCase.id}\n`;
        }
      });
    } else {
      // If no scenarios provided, associate default use cases appropriately
      // Skip UC1 (Login to System) and UC3 (Upload Requirements) - they are sub-use cases
      code += `Analyst -- UC2\n`; // Create Account (register)
      code += `Analyst -- UC5\n`; // Validate Requirements
      code += `Analyst -- UC6\n`; // Generate UML Diagrams
      code += `Analyst -- UC7\n`; // View Analysis Results
      code += `Analyst -- UC8\n`; // Inspect Traceability
      code += `Analyst -- UC9\n`; // View Quality Metrics
      code += `Manager -- UC10\n`; // Export Report
      code += `Manager -- UC11\n`; // Evaluate Submission
      code += `Manager -- UC12\n`; // Review Analysis
    }

    // Include relationships (dashed arrows pointing TO the included use case)
    code += `' Include relationships (dashed arrows pointing to included use case)\n`;
    // Add include relationships between related use cases
    if (scenarios.length > 0) {
      if (useCases.length >= 3) {
        code += `${useCases[2]?.id} ..> ${useCases[3]?.id || useCases[0]?.id} : <<include>>\n`;  // Third includes fourth/first
      }
      if (useCases.length >= 5) {
        code += `${useCases[4]?.id} ..> ${useCases[3]?.id || useCases[0]?.id} : <<include>>\n`;  // Fifth includes fourth/first
      }
    } else {
      // Default relationships for default use cases
      code += `UC3 ..> UC4 : <<include>>\n`;  // Upload includes Validate
      code += `UC5 ..> UC4 : <<include>>\n`;  // Generate includes Validate
    }

    // Extend relationships (dashed arrows pointing TO the base use case)
    code += `' Extend relationships (dashed arrows pointing to base use case)\n`;
    if (scenarios.length > 0) {
      if (useCases.length >= 2) {
        code += `${useCases[1]?.id} ..> ${useCases[0]?.id} : <<extend>>\n`;  // Second extends first
      }
      if (useCases.length >= 6) {
        code += `${useCases[5]?.id} ..> ${useCases[4]?.id || useCases[0]?.id} : <<extend>>\n`;  // Sixth extends fifth/first
      }
    } else {
      // Default extend relationships for default use cases
      code += `UC6 ..> UC5 : <<extend>>\n`;  // View Results extends Generate
    }

    code += `\n@enduml`;

    return {
      title: 'Online Shopping System - Use Case Diagram',
      code: code,
      description: 'UML 2.5 compliant use case diagram showing actors and their interactions with system functions.',
      actors: ['Requirements Analyst (Student/Developer)', 'QA Manager (Supervisor/Auditor)'],
      useCases: useCases.map(uc => uc.name)
    };
  };

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
    // In a real app, this would download the diagram
    alert('Downloading diagram as PNG...');
  };

  const handleExportMermaid = () => {
    // Export the current diagram as Mermaid code
    const currentDiagram = diagramType === 'sequence' 
      ? diagramData.sequence[selectedScenario] 
      : diagramData.usecase;
    
    if (currentDiagram) {
      const element = document.createElement('a');
      const file = new Blob([currentDiagram.code], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `${currentDiagram.title.replace(/\s+/g, '_')}.mermaid`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  const handleExportAllAsPDF = () => {
    // In a real app, this would generate a PDF with all diagrams
    alert('Generating PDF report with all diagrams...');
  };

  // Get current diagram data
  const getCurrentDiagram = () => {
    if (diagramType === 'sequence') {
      if (selectedScenario && diagramData.sequence[selectedScenario]) {
        return diagramData.sequence[selectedScenario];
      }
      // If no scenario selected, return the first one
      const sequenceScenarios = Object.keys(diagramData.sequence);
      if (sequenceScenarios.length > 0) {
        const firstScenarioId = sequenceScenarios[0];
        return diagramData.sequence[firstScenarioId] || null;
      }
      return null;
    } else {
      return diagramData.usecase;
    }
  };

  // Effect to handle scenario selection when diagram data changes
  useEffect(() => {
    if (diagramType === 'sequence' && !selectedScenario) {
      const sequenceScenarios = Object.keys(diagramData.sequence);
      if (sequenceScenarios.length > 0) {
        setSelectedScenario(sequenceScenarios[0]);
      }
    }
  }, [diagramType, diagramData, selectedScenario]);

  const currentDiagram = getCurrentDiagram();

  // Check if current diagram has too many steps
  const hasTooManySteps = currentDiagram && currentDiagram.steps > 15;

  // Check if no scenarios were detected
  const noScenariosDetected = scenarios.length === 0;

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header Section */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              {/* Back Button */}
              <button
                onClick={() => navigate('/analysis-results')}
                className="p-2 rounded-lg hover:bg-[var(--card-bg)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>

              {/* Title Group */}
              <div className="flex flex-col">
                <h1 className="text-2xl font-bold text-[var(--text-primary)]">
                  {diagramType === 'sequence' ? 'Sequence Diagram Generator' : 'Use Case Diagram Generator'}
                </h1>
                <p className="text-sm text-[var(--text-secondary)]">
                  Automated UML diagram generation from requirements
                </p>
              </div>
            </div>

            {/* Export PDF Button */}
            <button
              onClick={handleExportAllAsPDF}
              className="flex items-center px-4 py-2 bg-[var(--primary-main)] border border-[var(--primary-main)] rounded-lg text-white hover:bg-[var(--primary-hover)] transition-colors"
            >
              <FileText className="h-4 w-4 mr-2" />
              Export PDF
            </button>
          </div>

          {/* Controls */}
          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
              <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
                <div className="flex space-x-1 bg-[var(--card-bg)] p-1 rounded-lg">
                  <button
                    onClick={() => setDiagramType('usecase')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      diagramType === 'usecase'
                        ? 'bg-[var(--primary-main)] text-white shadow-sm'
                        : 'text-[var(--text-secondary)] hover:text-[var(--primary-main)]'
                    }`}
                  >
                    Use Case Diagram
                  </button>
                  <button
                    onClick={() => setDiagramType('sequence')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      diagramType === 'sequence'
                        ? 'bg-[var(--primary-main)] text-white shadow-sm'
                        : 'text-[var(--text-secondary)] hover:text-[var(--primary-main)]'
                    }`}
                  >
                    Sequence Diagram
                  </button>
                </div>

                {/* Scenario dropdown - only show for Sequence Diagram */}
                {diagramType === 'sequence' && !noScenariosDetected && (
                  <div className="flex items-center space-x-3">
                    <label className="text-sm font-medium text-[var(--text-secondary)] flex items-center">
                      <Filter className="h-4 w-4 mr-1" />
                      Select Scenario to Visualize
                    </label>
                    <select
                      value={selectedScenario}
                      onChange={(e) => setSelectedScenario(e.target.value)}
                      className="appearance-none bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg px-4 py-2 pr-8 text-[var(--text-primary)] focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent min-w-[250px]"
                    >
                      {scenarios.map(scenario => (
                        <option key={scenario.id} value={scenario.id}>
                          {scenario.name} ({scenario.steps} steps)
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)] pointer-events-none" />
                  </div>
                )}

                {/* All Scenarios button - only show for Sequence Diagram */}
                {diagramType === 'sequence' && !noScenariosDetected && (
                  <button
                    onClick={() => setAllScenariosView(!allScenariosView)}
                    className="flex items-center px-4 py-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg text-[var(--text-secondary)] hover:bg-[var(--surface-bg)] transition-colors"
                  >
                    <Grid3X3 className="h-4 w-4 mr-2" />
                    {allScenariosView ? 'Back to Single' : 'All Scenarios'}
                  </button>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={handleZoomOut}
                  className="p-2 rounded-lg border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--surface-bg)] hover:text-[var(--primary-main)] transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-[var(--text-secondary)]">{zoomLevel}%</span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 rounded-lg border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--surface-bg)] hover:text-[var(--primary-main)] transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleResetZoom}
                  className="p-2 rounded-lg border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--surface-bg)] hover:text-[var(--primary-main)] transition-colors"
                  title="Reset Zoom"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
                {/* Dark mode toggle removed for consistency */}
              </div>
            </div>
          </div>

          {/* Warning for complex diagrams */}
          {hasTooManySteps && (
            <div className="bg-[var(--warning-light)]/10 border-l-4 border-[var(--warning-main)] p-4 mb-6 rounded">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-3" />
                <div>
                  <p className="text-sm font-medium text-[var(--warning-main)]">
                    ⚠️ Complex diagram detected
                  </p>
                  <p className="text-sm text-[var(--warning-main)]">
                    Contains {currentDiagram.steps} steps. Consider filtering for better readability.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* No scenarios detected warning */}
          {noScenariosDetected && (
            <div className="bg-[var(--warning-light)]/10 border-l-4 border-[var(--warning-main)] p-4 mb-6 rounded">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-[var(--warning-main)] mr-3" />
                <div>
                  <p className="text-sm font-medium text-[var(--warning-main)]">
                    ⚠️ No scenarios detected in document
                  </p>
                  <p className="text-sm text-[var(--warning-main)]">
                    Complex diagram. Filtering recommended. The system could not identify distinct scenarios in the document.
                  </p>
                  <div className="mt-2">
                    <button className="text-xs px-3 py-1 bg-[var(--warning-main)]/20 text-[var(--warning-main)] rounded-full hover:bg-[var(--warning-main)]/30">
                      Manual Scenario Definition
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* All Scenarios View */}
          {allScenariosView && diagramType === 'sequence' && (
            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm overflow-hidden mb-6">
              <div className="p-6 border-b border-[var(--card-border)]">
                <h2 className="text-lg font-semibold text-[var(--text-primary)]">All Scenarios</h2>
                <p className="text-sm text-[var(--text-secondary)]">Click on any scenario to view its diagram</p>
              </div>

              <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Object.entries(diagramData.sequence).map(([id, diagram]) => (
                  <div
                    key={id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedScenario === id
                        ? 'border-[var(--primary-main)] bg-[var(--primary-main)]/5'
                        : 'border-[var(--card-border)] hover:border-[var(--primary-main)]/50 hover:bg-[var(--surface-bg)]'
                    }`}
                    onClick={() => {
                      setSelectedScenario(id);
                      setAllScenariosView(false);
                    }}
                  >
                    <h3 className="font-medium text-[var(--text-primary)]">{diagram.title}</h3>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{diagram.description}</p>
                    <div className="mt-3 flex justify-between items-center">
                      <span className="text-xs px-2 py-1 bg-[var(--accent-main)]/10 text-[var(--accent-main)] rounded-full">
                        {diagram.steps} steps
                      </span>
                      <Eye className="h-4 w-4 text-[var(--text-secondary)]" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Diagram Visualization */}
          {!allScenariosView && (
            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm overflow-hidden">
              <div className="p-6 border-b border-[var(--card-border)]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {diagramType === 'sequence'
                        ? currentDiagram?.description || (noScenariosDetected
                            ? 'Shows the main system flow as no distinct scenarios were detected'
                            : 'Shows the interaction flow between system components')
                        : 'Overview of all actors and their interactions with the system'}
                    </p>
                  </div>

                  {diagramType === 'sequence' && !noScenariosDetected && (
                    <div className="flex items-center space-x-2">
                      <span className="text-xs px-2 py-1 bg-[var(--primary-main)]/10 text-[var(--primary-main)] rounded-full">
                        {selectedScenario
                          ? scenarios.find(s => s.id === selectedScenario)?.name || 'Selected Scenario'
                          : 'All Scenarios'}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-8">
                {loading ? (
                  <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-8 min-h-[500px] flex items-center justify-center">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--primary-main)] mb-4"></div>
                      <p className="text-[var(--text-secondary)]">Generating diagram...</p>
                    </div>
                  </div>
                ) : currentDiagram ? (
                  <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-8 min-h-[500px] flex items-center justify-center overflow-auto">
                    <div className="w-full h-full flex items-center justify-center">
                      <DiagramViewer
                        key={`${diagramType}-${selectedScenario || 'default'}-${currentDiagram?.title || 'diagram'}`}
                        chartString={currentDiagram.code}
                        zoomLevel={zoomLevel}
                        darkMode={darkMode}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-8 min-h-[500px] flex items-center justify-center">
                    <div className="text-center">
                      <AlertCircle className="h-12 w-12 text-[var(--error-main)] mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No Diagram Available</h3>
                      <p className="text-[var(--text-secondary)] max-w-md">
                        {diagramType === 'sequence'
                          ? 'Please select a scenario to visualize'
                          : 'Use case diagram could not be generated'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Business Rules */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Validation Rules</h3>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <div className="bg-[var(--primary-main)]/10 rounded-full p-1 mr-3 mt-0.5">
                    <FileText className="h-4 w-4 text-[var(--primary-main)]" />
                  </div>
                  <div>
                    <p className="font-medium text-[var(--text-primary)]">BR-11: Text-Based Diagrams</p>
                    <p className="text-sm text-[var(--text-secondary)]">Diagrams strictly reflect the text provided; no hallucinated actors</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <div className="bg-[var(--primary-main)]/10 rounded-full p-1 mr-3 mt-0.5">
                    <FileText className="h-4 w-4 text-[var(--primary-main)]" />
                  </div>
                  <div>
                    <p className="font-medium text-[var(--text-primary)]">BR-12: Step Limit</p>
                    <p className="text-sm text-[var(--text-secondary)]">Sequence diagrams limited to 15 steps per scenario for readability</p>
                  </div>
                </li>
              </ul>
            </div>

            <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Scenario Details</h3>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {scenarios.map(scenario => (
                  <div key={scenario.id} className="flex items-center justify-between p-3 bg-[var(--surface-bg)] rounded-lg">
                    <span className="text-[var(--text-primary)]">{scenario.name}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs px-2 py-1 bg-[var(--primary-main)]/10 text-[var(--primary-main)] rounded-full">
                        {scenario.steps} steps
                      </span>
                      <span className="text-xs text-[var(--text-secondary)]">
                        {scenario.actors.length} actors
                      </span>
                    </div>
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

export default VisualizationPage;