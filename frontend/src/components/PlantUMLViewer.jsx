import React, { useRef } from 'react';
import { Download, Copy, ExternalLink } from 'lucide-react';

const PlantUMLViewer = ({ plantumlSyntax, zoomLevel = 100, darkMode = false }) => {
  const containerRef = useRef(null);

  // Handle copy to clipboard
  const handleCopy = () => {
    navigator.clipboard.writeText(plantumlSyntax);
  };

  // Handle download as PlantUML file
  const handleDownload = () => {
    const blob = new Blob([plantumlSyntax], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'diagram.puml';
    link.click();
    URL.revokeObjectURL(url);
  };

  // Handle open in PlantUML editor (manual copy-paste approach)
  const handleOpenInEditor = () => {
    // Copy to clipboard first
    navigator.clipboard.writeText(plantumlSyntax);
    // Then open the editor
    window.open('https://www.plantuml.com/plantuml/uml/', '_blank');
  };

  if (!plantumlSyntax) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[var(--text-secondary)]">No PlantUML syntax available</p>
      </div>
    );
  }

  return (
    <div className="w-full" style={{ zoom: zoomLevel / 100 }}>
      <div className="relative">
        {/* Toolbar */}
        <div className="absolute top-2 right-2 flex gap-2 z-10">
          <button
            onClick={handleCopy}
            className="p-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg hover:bg-[var(--surface-bg)]"
            title="Copy to Clipboard"
          >
            <Copy className="h-4 w-4" />
          </button>
          <button
            onClick={handleDownload}
            className="p-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg hover:bg-[var(--surface-bg)]"
            title="Download PlantUML"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={handleOpenInEditor}
            className="p-2 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg hover:bg-[var(--surface-bg)]"
            title="Open in PlantUML Editor"
          >
            <ExternalLink className="h-4 w-4" />
          </button>
        </div>

        {/* PlantUML Syntax Display */}
        <div className="bg-[var(--content-bg)] rounded-lg p-4 overflow-auto">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              IEEE-Compliant PlantUML Syntax:
            </span>
          </div>
          <pre className="text-sm text-[var(--text-primary)] whitespace-pre-wrap font-mono bg-[var(--surface-bg)] p-3 rounded border border-[var(--card-border)] max-h-96 overflow-auto">
            {plantumlSyntax}
          </pre>
        </div>

        {/* Instructions */}
        <div className="mt-4 bg-[var(--info-light)]/20 border-l-4 border-[var(--info-main)] p-4 rounded">
          <div className="flex items-start gap-3">
            <Copy className="h-5 w-5 text-[var(--info-main)] mt-0.5" />
            <div className="text-sm text-[var(--info-main)]">
              <p className="font-medium mb-1">How to View Rendered Diagram</p>
              <p>1. Click "Copy to Clipboard" to copy the PlantUML syntax</p>
              <p>2. Click "Open in PlantUML Editor" to open the online editor</p>
              <p>3. Paste the syntax (Ctrl+V) into the editor to view the rendered diagram</p>
              <p className="mt-2 text-xs">The syntax can also be used in any PlantUML-compatible tool or IDE.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlantUMLViewer;
