import React, { useState, useEffect, useRef } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Download,
  Play
} from 'lucide-react';
import PlantUML from 'react-plantuml';
import plantumlEncoder from 'plantuml-encoder';

const DiagramViewer = ({ chartString, zoomLevel = 100, darkMode = false }) => {
  const diagramRef = useRef(null);

  // Determine if the diagram is PlantUML or Mermaid
  const isPlantUML = chartString.includes('@startuml') && chartString.includes('@enduml');

  // Initialize Mermaid with proper configuration for alignment
  useEffect(() => {
    if (!isPlantUML) {
      const initializeMermaid = async () => {
        if (typeof window !== 'undefined') {
          try {
            const mermaidModule = await import('mermaid');
            const mermaid = mermaidModule.default || mermaidModule;

            mermaid.initialize({
              startOnLoad: false,
              theme: darkMode ? 'dark' : 'default',
              themeVariables: {
                primaryColor: '#F7F9FB',       // Background of Actor/Participant boxes
                primaryTextColor: '#1F2933',   // Text color inside boxes
                primaryBorderColor: '#4F46E5', // Border color of boxes (Slate Blue)
                lineColor: '#64748B',          // Color of the arrows/lines
                secondaryColor: '#E2E8F0',     // Background of the "Alt" loop boxes
                tertiaryColor: '#FFFFFF',      // Background of the main canvas
                noteBkgColor: '#FEF3C7',       // Background for Note boxes
                noteTextColor: '#92400E'       // Text for Note boxes
              },
              sequence: {
                diagramMarginX: 50,
                diagramMarginY: 20,
                actorMargin: 100,
                width: 180,
                height: 80,
                boxMargin: 15,
                boxTextMargin: 8,
                noteMargin: 15,
                messageMargin: 50,
                mirrorActors: false,
                bottomMarginAdj: 1,
                useMaxWidth: true,
                rightAngles: false,
                showSequenceNumbers: true
              },
              fontFamily: 'Inter, sans-serif'
            });
          } catch (error) {
            console.error('Error initializing mermaid:', error);
          }
        }
      };

      initializeMermaid();
    }
  }, [isPlantUML, darkMode]); // Only initialize once when component mounts

  // Render the diagram when chartString changes
  useEffect(() => {
    if (!isPlantUML) {
      const renderDiagram = async () => {
        console.log('Rendering diagram...', { chartString, darkMode }); // Debug log
        if (diagramRef.current && chartString) {
          try {
            const mermaidModule = await import('mermaid');
            const mermaid = mermaidModule.default || mermaidModule;

            // Reinitialize mermaid with the correct theme when darkMode changes
            mermaid.initialize({
              startOnLoad: false,
              theme: darkMode ? 'dark' : 'default',
              themeVariables: {
                primaryColor: '#F7F9FB',       // Background of Actor/Participant boxes
                primaryTextColor: '#1F2933',   // Text color inside boxes
                primaryBorderColor: '#4F46E5', // Border color of boxes (Slate Blue)
                lineColor: '#64748B',          // Color of the arrows/lines
                secondaryColor: '#E2E8F0',     // Background of the "Alt" loop boxes
                tertiaryColor: '#FFFFFF',      // Background of the main canvas
                noteBkgColor: '#FEF3C7',       // Background for Note boxes
                noteTextColor: '#92400E'       // Text for Note boxes
              },
              sequence: {
                diagramMarginX: 50,
                diagramMarginY: 20,
                actorMargin: 100,
                width: 180,
                height: 80,
                boxMargin: 15,
                boxTextMargin: 8,
                noteMargin: 15,
                messageMargin: 50,
                mirrorActors: false,
                bottomMarginAdj: 1,
                useMaxWidth: true,
                rightAngles: false,
                showSequenceNumbers: true
              },
              fontFamily: 'Inter, sans-serif'
            });

            // Clear the diagram container
            diagramRef.current.innerHTML = '';

            // Generate a unique ID for the diagram
            const diagramId = 'diagram-' + Date.now();

            console.log('About to render mermaid diagram with ID:', diagramId); // Debug log
            console.log('Chart string:', chartString); // Debug log

            // Render the diagram to SVG
            const { svg } = await mermaid.render(diagramId, chartString);
            console.log('SVG generated successfully'); // Debug log

            diagramRef.current.innerHTML = svg;
          } catch (error) {
            console.error('Error rendering diagram:', error);
            console.error('Chart string:', chartString); // Debug log

            // Fallback to showing a visual representation of the diagram
            diagramRef.current.innerHTML = `
              <div class="flex flex-col items-center justify-center min-h-[400px] text-center p-4">
                <div class="inline-block bg-[#E0E7FF] p-4 rounded-lg mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-[#4F46E5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 002-2v6a2 2 0 002-2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 002-2v10m-6 0a2 2 0 002-2h2a2 2 0 012-2v14a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 class="text-lg font-semibold text-[#1F2933] mb-2">
                  ${isPlantUML ? 'PlantUML Diagram' : 'Mermaid Diagram'}
                </h3>
                <p class="text-[#6B7280] max-w-md">
                  ${isPlantUML ? 
                    'PlantUML syntax detected. Check console for details.' : 
                    'Interactive diagram with zoom, pan, and export features.'}
                </p>
                ${error ? `
                  <div class="mt-4 p-3 bg-[var(--surface-bg)] rounded border border-[var(--card-border)]">
                    <h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Rendering Error</h4>
                    <p class="text-sm text-[var(--text-secondary)] mb-2">Error: ${error.message}</p>
                    <div class="mt-4 p-3 bg-[var(--surface-bg)] rounded border border-[var(--card-border)]">
                      <h4 class="text-sm font-semibold text-[var(--text-primary)] mb-2">Diagram Syntax</h4>
                      <pre class="text-xs text-[var(--text-secondary)] overflow-x-auto whitespace-pre-wrap bg-[var(--content-bg)] p-2 rounded">${chartString}</pre>
                    </div>
                  </div>
                ` : ''}
              </div>
            `;
          }
        } else {
          console.log('Diagram conditions not met', { hasRef: !!diagramRef.current, hasChartString: !!chartString }); // Debug log
        }
      };

      renderDiagram();
    }
  }, [chartString, darkMode, isPlantUML]); // Only re-run when chartString or darkMode changes

  // Function to generate PlantUML image URL
  const generatePlantUMLImage = (plantUMLCode) => {
    try {
      const encoded = plantumlEncoder.encode(plantUMLCode);
      return `https://www.planttext.com/api/plantuml/svg/${encoded}`;
    } catch (error) {
      console.error('Error encoding PlantUML:', error);
      return '';
    }
  };

  return (
    <div className="w-full h-full flex flex-col">
      {/* Diagram Canvas */}
      <div className={`rounded-lg flex-grow flex items-center justify-center ${darkMode ? 'bg-[#1F2937]' : 'bg-white'} border ${darkMode ? 'border-[#374151]' : 'border-[#E5E7EB]'}`}>
        <div
          ref={diagramRef}
          className="h-full w-full flex justify-center items-center"
          style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'center' }}
        >
          {/* Render PlantUML or Mermaid based on diagram type */}
          {isPlantUML && (
            <div className="mt-4 p-3 bg-[var(--surface-bg)] rounded border border-[var(--card-border)]">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">PlantUML Diagram Export</h4>
                <button
                  onClick={() => {
                    const encoded = plantumlEncoder.encode(chartString);
                    window.open(`https://www.planttext.com/api/plantuml/svg/${encoded}`, '_blank');
                  }}
                  className="px-3 py-1 bg-[var(--primary-main)] text-white rounded hover:bg-[var(--primary-dark)] transition-colors"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export as Image
                </button>
              </div>
              <div className="mt-2">
                <p className="text-xs text-[var(--text-secondary)] mb-2">PlantUML syntax detected. Check console for details.</p>
              </div>
            </div>
          )}
          {isPlantUML ? (
            <div className="w-full h-full flex justify-center items-center">
              <img
                src={generatePlantUMLImage(chartString)}
                alt="Use Case Diagram"
                className="max-w-full max-h-full object-contain"
                onError={(e) => {
                  e.target.onerror = null; // Prevent infinite loop
                  e.target.src = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400"><rect width="600" height="400" fill="%23F3F4F6"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="16" fill="%236B7280">PlantUML diagram failed to load</text></svg>`;
                }}
              />
            </div>
          ) : (
            // The diagram will be rendered here by Mermaid
            null
          )}
        </div>
      </div>
    </div>
  );
};

export default DiagramViewer;