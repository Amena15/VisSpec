import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Visualization from '../src/pages/Visualization';
import { AuthProvider } from '../src/contexts/AuthContext';
import { ProjectProvider } from '../src/contexts/ProjectContext';

// Mock the API calls
jest.mock('../src/services/api', () => ({
  getDocument: jest.fn(),
  getUseCaseDiagram: jest.fn(),
  getSequenceDiagram: jest.fn(),
  getActivityDiagram: jest.fn(),
  renderPlantUMLPNG: jest.fn(),
}));

import { 
  getDocument, 
  getUseCaseDiagram, 
  getSequenceDiagram, 
  getActivityDiagram,
  renderPlantUMLPNG 
} from '../src/services/api';

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      <ProjectProvider>
        {children}
      </ProjectProvider>
    </AuthProvider>
  </BrowserRouter>
);

// Mock URL params
const mockParams = { docId: 'test-doc-id' };

describe('Visualization Component', () => {
  const mockDocument = testUtils.createMockDocument({
    status: 'Analyzed & Organized',
    requirements_count: 5
  });

  const mockUseCaseDiagram = {
    mermaid_syntax: 'graph TD\n    User --> Login',
    plantuml_syntax: '@startuml\nUser -> Login\n@enduml',
    actors: ['User', 'System'],
    use_cases: ['Login', 'Logout'],
    relationships: [
      { type: 'association', source: 'User', target: 'Login' }
    ]
  };

  const mockSequenceDiagram = {
    mermaid_syntax: 'sequenceDiagram\n    User->>System: Login',
    plantuml_syntax: '@startuml\nUser -> System: Login\n@enduml',
    steps: 5,
    participants: ['User', 'System'],
    scenarios: ['Login Flow']
  };

  const mockActivityDiagram = {
    mermaid_syntax: 'graph TD\n    Start --> Process',
    plantuml_syntax: '@startuml\nstart --> Process\n@enduml',
    activities: ['Start', 'Process', 'End'],
    flows: ['Start -> Process', 'Process -> End']
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    
    // Mock authenticated user
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('user', JSON.stringify(testUtils.createMockUser()));
    
    // Mock URL params
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useParams: () => mockParams
    }));
  });

  describe('Component Rendering', () => {
    test('renders visualization page correctly', async () => {
      getDocument.mockResolvedValue(mockDocument);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/diagram visualization/i)).toBeInTheDocument();
        expect(screen.getByText(mockDocument.filename)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /use case/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /sequence/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /activity/i })).toBeInTheDocument();
      });
    });

    test('shows loading state while fetching document', () => {
      getDocument.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      expect(screen.getByText(/loading document/i)).toBeInTheDocument();
    });

    test('shows error state when document fetch fails', async () => {
      getDocument.mockRejectedValue(new Error('Document not found'));

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading document/i)).toBeInTheDocument();
      });
    });

    test('shows error when document is not analyzed', async () => {
      const unanalyzedDocument = { ...mockDocument, status: 'Uploaded' };
      getDocument.mockResolvedValue(unanalyzedDocument);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/document must be analyzed first/i)).toBeInTheDocument();
      });
    });
  });

  describe('Use Case Diagram', () => {
    test('generates and displays use case diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /use case/i })).toBeInTheDocument();
      });

      // Click use case diagram button
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(getUseCaseDiagram).toHaveBeenCalledWith('test-doc-id');
        expect(screen.getByText(/use case diagram/i)).toBeInTheDocument();
        expect(screen.getByText(/actors/i)).toBeInTheDocument();
        expect(screen.getByText(/use cases/i)).toBeInTheDocument();
      });
    });

    test('displays Mermaid syntax for use case diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/mermaid syntax/i)).toBeInTheDocument();
        expect(screen.getByText(mockUseCaseDiagram.mermaid_syntax)).toBeInTheDocument();
      });
    });

    test('displays PlantUML syntax for use case diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      // Switch to PlantUML view
      const plantumlTab = screen.getByRole('button', { name: /plantuml/i });
      fireEvent.click(plantumlTab);

      await waitFor(() => {
        expect(screen.getByText(/plantuml syntax/i)).toBeInTheDocument();
        expect(screen.getByText(mockUseCaseDiagram.plantuml_syntax)).toBeInTheDocument();
      });
    });

    test('shows actors and use cases lists', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        // Check actors
        expect(screen.getByText('User')).toBeInTheDocument();
        expect(screen.getByText('System')).toBeInTheDocument();
        
        // Check use cases
        expect(screen.getByText('Login')).toBeInTheDocument();
        expect(screen.getByText('Logout')).toBeInTheDocument();
      });
    });

    test('shows relationships in use case diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/relationships/i)).toBeInTheDocument();
        expect(screen.getByText(/association/i)).toBeInTheDocument();
        expect(screen.getByText(/User -> Login/i)).toBeInTheDocument();
      });
    });
  });

  describe('Sequence Diagram', () => {
    test('generates and displays sequence diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getSequenceDiagram.mockResolvedValue(mockSequenceDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Click sequence diagram button
      const sequenceButton = screen.getByRole('button', { name: /sequence/i });
      fireEvent.click(sequenceButton);

      await waitFor(() => {
        expect(getSequenceDiagram).toHaveBeenCalledWith('test-doc-id', null);
        expect(screen.getByText(/sequence diagram/i)).toBeInTheDocument();
      });
    });

    test('allows scenario selection for sequence diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getSequenceDiagram.mockResolvedValue(mockSequenceDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate sequence diagram
      const sequenceButton = screen.getByRole('button', { name: /sequence/i });
      fireEvent.click(sequenceButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/scenario/i)).toBeInTheDocument();
        expect(screen.getByText('Login Flow')).toBeInTheDocument();
      });

      // Select different scenario
      const scenarioSelect = screen.getByLabelText(/scenario/i);
      fireEvent.change(scenarioSelect, { target: { value: 'Login Flow' } });

      await waitFor(() => {
        expect(getSequenceDiagram).toHaveBeenCalledWith('test-doc-id', 'Login Flow');
      });
    });

    test('shows step count and participants', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getSequenceDiagram.mockResolvedValue(mockSequenceDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate sequence diagram
      const sequenceButton = screen.getByRole('button', { name: /sequence/i });
      fireEvent.click(sequenceButton);

      await waitFor(() => {
        expect(screen.getByText(/steps/i)).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText(/participants/i)).toBeInTheDocument();
        expect(screen.getByText('User')).toBeInTheDocument();
        expect(screen.getByText('System')).toBeInTheDocument();
      });
    });

    test('shows BR-12 warning for diagrams with >15 steps', async () => {
      const longSequenceDiagram = {
        ...mockSequenceDiagram,
        steps: 20,
        truncated: true,
        warning: 'Diagram truncated to 15 steps per BR-12'
      };

      getDocument.mockResolvedValue(mockDocument);
      getSequenceDiagram.mockResolvedValue(longSequenceDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate sequence diagram
      const sequenceButton = screen.getByRole('button', { name: /sequence/i });
      fireEvent.click(sequenceButton);

      await waitFor(() => {
        expect(screen.getByText(/br-12 warning/i)).toBeInTheDocument();
        expect(screen.getByText(/diagram truncated to 15 steps/i)).toBeInTheDocument();
      });
    });
  });

  describe('Activity Diagram', () => {
    test('generates and displays activity diagram', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getActivityDiagram.mockResolvedValue(mockActivityDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Click activity diagram button
      const activityButton = screen.getByRole('button', { name: /activity/i });
      fireEvent.click(activityButton);

      await waitFor(() => {
        expect(getActivityDiagram).toHaveBeenCalledWith('test-doc-id');
        expect(screen.getByText(/activity diagram/i)).toBeInTheDocument();
      });
    });

    test('displays activities and flows', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getActivityDiagram.mockResolvedValue(mockActivityDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate activity diagram
      const activityButton = screen.getByRole('button', { name: /activity/i });
      fireEvent.click(activityButton);

      await waitFor(() => {
        // Check activities
        expect(screen.getByText('Start')).toBeInTheDocument();
        expect(screen.getByText('Process')).toBeInTheDocument();
        expect(screen.getByText('End')).toBeInTheDocument();
        
        // Check flows
        expect(screen.getByText(/flows/i)).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    test('can export PlantUML as PNG', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);
      renderPlantUMLPNG.mockResolvedValue(new Blob(['image data'], { type: 'image/png' }));

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export png/i })).toBeInTheDocument();
      });

      // Export as PNG
      const exportButton = screen.getByRole('button', { name: /export png/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(renderPlantUMLPNG).toHaveBeenCalledWith(mockUseCaseDiagram.plantuml_syntax);
        expect(screen.getByText(/png exported successfully/i)).toBeInTheDocument();
      });
    });

    test('can export Mermaid as SVG', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      // Mock SVG download
      const mockLink = { click: jest.fn(), href: '', download: '' };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export svg/i })).toBeInTheDocument();
      });

      // Export as SVG
      const exportButton = screen.getByRole('button', { name: /export svg/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockLink.download).toMatch(/\.svg$/);
      });
    });

    test('can copy syntax to clipboard', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      // Mock clipboard API
      const mockWriteText = jest.fn();
      Object.assign(navigator, {
        clipboard: {
          writeText: mockWriteText,
        },
      });

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy syntax/i })).toBeInTheDocument();
      });

      // Copy syntax
      const copyButton = screen.getByRole('button', { name: /copy syntax/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(mockWriteText).toHaveBeenCalledWith(mockUseCaseDiagram.mermaid_syntax);
        expect(screen.getByText(/syntax copied to clipboard/i)).toBeInTheDocument();
      });
    });
  });

  describe('Diagram Rendering', () => {
    test('renders Mermaid diagram in preview', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByTestId('mermaid-diagram')).toBeInTheDocument();
        expect(screen.getByTestId('mermaid-diagram')).toHaveTextContent(mockUseCaseDiagram.mermaid_syntax);
      });
    });

    test('shows error when diagram generation fails', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockRejectedValue(new Error('Generation failed'));

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to generate diagram/i)).toBeInTheDocument();
      });
    });

    test('shows loading state during diagram generation', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/generating diagram/i)).toBeInTheDocument();
      });
    });
  });

  describe('Diagram Settings', () => {
    test('can toggle between Mermaid and PlantUML views', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /mermaid/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /plantuml/i })).toBeInTheDocument();
      });

      // Switch to PlantUML
      const plantumlTab = screen.getByRole('button', { name: /plantuml/i });
      fireEvent.click(plantumlTab);

      await waitFor(() => {
        expect(screen.getByText(mockUseCaseDiagram.plantuml_syntax)).toBeInTheDocument();
      });

      // Switch back to Mermaid
      const mermaidTab = screen.getByRole('button', { name: /mermaid/i });
      fireEvent.click(mermaidTab);

      await waitFor(() => {
        expect(screen.getByText(mockUseCaseDiagram.mermaid_syntax)).toBeInTheDocument();
      });
    });

    test('can adjust diagram zoom level', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/zoom/i)).toBeInTheDocument();
      });

      // Increase zoom
      const zoomSlider = screen.getByLabelText(/zoom/i);
      fireEvent.change(zoomSlider, { target: { value: '150' } });

      await waitFor(() => {
        const diagram = screen.getByTestId('mermaid-diagram');
        expect(diagram).toHaveStyle('transform: scale(1.5)');
      });
    });
  });

  describe('BR-11 Compliance', () => {
    test('shows BR-11 compliance check for actors', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/br-11 compliance/i)).toBeInTheDocument();
        expect(screen.getByText(/no hallucinated actors/i)).toBeInTheDocument();
        expect(screen.getByText(/✓ pass/i)).toBeInTheDocument();
      });
    });

    test('shows BR-11 failure when extra actors detected', async () => {
      const nonCompliantDiagram = {
        ...mockUseCaseDiagram,
        br11_compliant: false,
        extra_actors: ['Ghost Actor']
      };

      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(nonCompliantDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      // Generate use case diagram
      const useCaseButton = screen.getByRole('button', { name: /use case/i });
      fireEvent.click(useCaseButton);

      await waitFor(() => {
        expect(screen.getByText(/br-11 compliance/i)).toBeInTheDocument();
        expect(screen.getByText(/extra actors detected/i)).toBeInTheDocument();
        expect(screen.getByText('Ghost Actor')).toBeInTheDocument();
        expect(screen.getByText(/✗ fail/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check form elements have proper labels
        expect(screen.getByLabelText(/scenario/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/zoom/i)).toBeInTheDocument();
        
        // Check buttons have proper roles
        expect(screen.getByRole('button', { name: /use case/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /export png/i })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /mermaid/i })).toBeInTheDocument();
      });
    });

    test('supports keyboard navigation', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /use case/i })).toBeInTheDocument();
      });

      const useCaseButton = screen.getByRole('button', { name: /use case/i });

      // Tab navigation
      useCaseButton.focus();
      expect(document.activeElement).toBe(useCaseButton);

      fireEvent.tab();
      // Should move to next focusable element

      // Enter key activation
      fireEvent.keyDown(useCaseButton, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(getUseCaseDiagram).toHaveBeenCalled();
      });
    });
  });

  describe('Responsive Design', () => {
    test('renders correctly on mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/diagram visualization/i)).toBeInTheDocument();
        // Should have mobile-specific layout
        expect(screen.getByTestId('mobile-diagram-view')).toBeInTheDocument();
      });
    });

    test('renders correctly on desktop viewport', async () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      getDocument.mockResolvedValue(mockDocument);
      getUseCaseDiagram.mockResolvedValue(mockUseCaseDiagram);

      render(
        <TestWrapper>
          <Visualization />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/diagram visualization/i)).toBeInTheDocument();
        // Should have desktop-specific layout
        expect(screen.getByTestId('desktop-diagram-view')).toBeInTheDocument();
      });
    });
  });
});
