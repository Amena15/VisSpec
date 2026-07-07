import React, { useEffect, useRef, useState } from 'react';
import plantumlEncoder from 'plantuml-encoder';

const DiagramViewer = ({ chartString, zoomLevel = 100, darkMode = false }) => {
  const diagramRef = useRef(null);
  const [plantUMLUrl, setPlantUMLUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [fallbackTried, setFallbackTried] = useState(false);

  // Determine if the diagram is PlantUML or Mermaid
  const isPlantUML = chartString?.includes('@startuml') && chartString?.includes('@enduml');

  // Generate PlantUML image URL (with cache busting)
  useEffect(() => {
    if (isPlantUML && chartString) {
      try {
        const encoded = plantumlEncoder.encode(chartString);
        // Use planttext.com (more reliable) with cache buster
        const url = `https://www.planttext.com/api/plantuml/svg/${encoded}?t=${Date.now()}`;
        setPlantUMLUrl(url);
        setLoading(true);
        setError(false);
        setFallbackTried(false);
      } catch (err) {
        console.error('PlantUML encoding error:', err);
        setError(true);
        setLoading(false);
      }
    }
  }, [chartString, isPlantUML]);

  // Initialize Mermaid only when NOT PlantUML
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
                primaryColor: '#F7F9FB',
                primaryTextColor: '#1F2933',
                primaryBorderColor: '#4F46E5',
                lineColor: '#64748B',
                secondaryColor: '#E2E8F0',
                tertiaryColor: '#FFFFFF',
                noteBkgColor: '#FEF3C7',
                noteTextColor: '#92400E'
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
  }, [isPlantUML, darkMode]);

  // Render Mermaid diagram when chartString changes (only for non-PlantUML)
  useEffect(() => {
    if (!isPlantUML && chartString) {
      const renderDiagram = async () => {
        if (diagramRef.current) {
          try {
            const mermaidModule = await import('mermaid');
            const mermaid = mermaidModule.default || mermaidModule;

            diagramRef.current.innerHTML = '';
            const diagramId = 'diagram-' + Date.now();
            const { svg } = await mermaid.render(diagramId, chartString);
            diagramRef.current.innerHTML = svg;

            // Attach click handler: if Mermaid nodes include data-element-id attributes
            // then we can pass them to the parent.
            // NOTE: Mermaid doesn't automatically know our element_id; the IEEE diagram generator
            // must embed it in the Mermaid string.
            const svgRoot = diagramRef.current.querySelector('svg');
            if (svgRoot && svgRoot.dataset && svgRoot.dataset.elementId) {
              // No-op: element_id on root not expected.
            }

            // Delegate click events from within the SVG
            svgRoot?.addEventListener('click', (evt) => {
              const target = evt.target;
              if (!target) return;

              const el = target.closest?.('[data-element-id]');
              if (!el) return;

              const elementId = el.getAttribute('data-element-id');
              if (!elementId) return;

              // Fire a custom event that the page can listen to.
              const event = new CustomEvent('diagram-node-click', {
                detail: { elementId },
              });
              window.dispatchEvent(event);
            });

            // If Mermaid doesn't produce data-element-id, no clicks will be mapped.

          } catch (error) {
            console.error('Error rendering diagram:', error);
            diagramRef.current.innerHTML = `
              <div class="flex flex-col items-center justify-center min-h-[400px] text-center p-4">
                <div class="inline-block bg-[#E0E7FF] p-4 rounded-full mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-[#4F46E5]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 class="text-lg font-semibold text-[#1F2933] mb-2">Rendering Error</h3>
                <p class="text-[#6B7280] max-w-md text-sm mb-4">Could not render Mermaid diagram.</p>
              </div>
            `;
          }
        }
      };
      renderDiagram();
    }
  }, [chartString, isPlantUML]);


  // Handle PlantUML image load success/failure
  const handleImageLoad = () => {
    setLoading(false);
    setError(false);
  };
  const handleImageError = () => {
    if (!fallbackTried) {
      setFallbackTried(true);
      // Fallback: try using plantuml.com as alternative
      const encoded = plantumlEncoder.encode(chartString);
      setPlantUMLUrl(`https://www.plantuml.com/plantuml/svg/${encoded}?t=${Date.now()}`);
      return;
    }

    setLoading(false);
    setError(true);
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className={`rounded-lg flex-grow flex items-center justify-center overflow-hidden ${darkMode ? 'bg-[#1F2937]' : 'bg-transparent'}`}>
        <div
          ref={diagramRef}
          className="h-full w-full flex justify-center items-center transition-transform duration-200 ease-out"
          style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'center' }}
        >
          {isPlantUML ? (
            <div className="w-full h-full flex justify-center items-center p-8 relative">
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-10 h-10 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
                </div>
              )}
              <img
                src={plantUMLUrl}
                alt="IEEE UML Diagram"
                className="max-w-full max-h-full object-contain"
                onLoad={handleImageLoad}
                onError={handleImageError}
                style={{ opacity: loading ? 0.5 : 1 }}
              />
              {error && (
                <div className="text-center text-red-600 p-4">
                  <p>Failed to load PlantUML diagram.</p>
                  <p className="text-sm text-gray-500">Please export as text or try again.</p>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default DiagramViewer;