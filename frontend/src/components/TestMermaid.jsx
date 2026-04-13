import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const TestMermaid = () => {
  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center mb-8">
            <Link to="/analysis" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] mr-4">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-[var(--text-primary)]">Mermaid Test Page</h1>
              <p className="text-[var(--text-secondary)]">Testing mermaid diagram generation functionality</p>
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6 mb-8">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">Mermaid Diagram Testing</h2>
            <p className="text-[var(--text-secondary)] mb-6">
              This page is used to test the mermaid diagram generation functionality. 
              In a real implementation, this would render UML diagrams based on requirements.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[var(--surface-bg)] p-6 rounded-lg">
                <h3 className="font-medium text-[var(--text-primary)] mb-3">Use Case Diagram</h3>
                <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 h-64 flex items-center justify-center">
                  <p className="text-[var(--text-secondary)] text-center">
                    Use Case Diagram would render here<br />
                    <span className="text-sm">(Requirements Analyst interacts with system functions)</span>
                  </p>
                </div>
              </div>

              <div className="bg-[var(--surface-bg)] p-6 rounded-lg">
                <h3 className="font-medium text-[var(--text-primary)] mb-3">Sequence Diagram</h3>
                <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-lg p-4 h-64 flex items-center justify-center">
                  <p className="text-[var(--text-secondary)] text-center">
                    Sequence Diagram would render here<br />
                    <span className="text-sm">(Interaction flow between system components)</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-xl shadow-sm p-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">Test Controls</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
                Generate Use Case
              </button>
              <button className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors">
                Generate Sequence
              </button>
              <button className="bg-[var(--surface-bg)] text-[var(--text-primary)] px-4 py-2 rounded-lg hover:bg-[var(--card-bg)] transition-colors">
                Clear Diagrams
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestMermaid;