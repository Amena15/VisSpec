import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AnalysisResults from '../src/pages/AnalysisResults';
import { AuthProvider } from '../src/contexts/AuthContext';
import { ProjectProvider } from '../src/contexts/ProjectContext';

// Mock the API calls
jest.mock('../src/services/api', () => ({
  getDocument: jest.fn(),
  getValidationResults: jest.fn(),
  applySuggestion: jest.fn(),
  markDefectAsFalsePositive: jest.fn(),
  runValidation: jest.fn(),
}));

import { 
  getDocument, 
  getValidationResults, 
  applySuggestion, 
  markDefectAsFalsePositive,
  runValidation 
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

describe('AnalysisResults Component', () => {
  const mockDocument = testUtils.createMockDocument({
    status: 'Validated',
    word_count: 100,
    requirements_count: 5
  });

  const mockValidationResults = {
    validation_id: 'test-validation-id',
    overall_score: 85,
    total_requirements: 5,
    defect_count: 3,
    defects: [
      {
        defect_id: 'defect-1',
        req_id: 'req-1',
        defect_type: 'ambiguity',
        severity: 'medium',
        confidence: 0.8,
        description: 'Requirement is ambiguous',
        suggestion: 'Clarify the requirement',
        ai_suggestion: 'The system shall allow authenticated users to login'
      },
      {
        defect_id: 'defect-2',
        req_id: 'req-2',
        defect_type: 'incompleteness',
        severity: 'high',
        confidence: 0.9,
        description: 'Requirement is incomplete',
        suggestion: 'Add more details',
        ai_suggestion: 'The system must validate user credentials against the database'
      }
    ]
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
    test('renders analysis results page correctly', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/analysis results/i)).toBeInTheDocument();
        expect(screen.getByText(mockDocument.filename)).toBeInTheDocument();
        expect(screen.getByText(/quality score/i)).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });

    test('shows loading state while fetching data', () => {
      getDocument.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    test('shows error state when API call fails', async () => {
      getDocument.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading document/i)).toBeInTheDocument();
      });
    });

    test('shows empty state when no validation results exist', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(null);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no validation results/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /run validation/i })).toBeInTheDocument();
      });
    });
  });

  describe('Quality Score Display', () => {
    test('displays quality score with correct color coding', async () => {
      const validationResults = { ...mockValidationResults, overall_score: 95 };
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(validationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('95%')).toBeInTheDocument();
        expect(screen.getByText('95%')).toHaveClass('text-green-600');
      });
    });

    test('shows medium quality score in yellow', async () => {
      const validationResults = { ...mockValidationResults, overall_score: 70 };
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(validationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('70%')).toBeInTheDocument();
        expect(screen.getByText('70%')).toHaveClass('text-yellow-600');
      });
    });

    test('shows low quality score in red', async () => {
      const validationResults = { ...mockValidationResults, overall_score: 45 };
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(validationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('45%')).toBeInTheDocument();
        expect(screen.getByText('45%')).toHaveClass('text-red-600');
      });
    });
  });

  describe('Defects List', () => {
    test('displays defects list correctly', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
        
        // Check individual defects
        expect(screen.getByText(/ambiguity/i)).toBeInTheDocument();
        expect(screen.getByText(/incompleteness/i)).toBeInTheDocument();
        expect(screen.getByText(/requirement is ambiguous/i)).toBeInTheDocument();
        expect(screen.getByText(/requirement is incomplete/i)).toBeInTheDocument();
      });
    });

    test('filters defects by severity', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Filter by high severity
      const severityFilter = screen.getByLabelText(/severity/i);
      fireEvent.change(severityFilter, { target: { value: 'high' } });

      await waitFor(() => {
        expect(screen.getByText(/incompleteness/i)).toBeInTheDocument();
        expect(screen.queryByText(/ambiguity/i)).not.toBeInTheDocument();
      });
    });

    test('filters defects by type', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Filter by ambiguity type
      const typeFilter = screen.getByLabelText(/defect type/i);
      fireEvent.change(typeFilter, { target: { value: 'ambiguity' } });

      await waitFor(() => {
        expect(screen.getByText(/ambiguity/i)).toBeInTheDocument();
        expect(screen.queryByText(/incompleteness/i)).not.toBeInTheDocument();
      });
    });

    test('sorts defects by confidence', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Sort by confidence (high to low)
      const sortFilter = screen.getByLabelText(/sort by/i);
      fireEvent.change(sortFilter, { target: { value: 'confidence_desc' } });

      await waitFor(() => {
        const defects = screen.getAllByTestId(/defect-item/);
        expect(defects[0]).toHaveTextContent('90%'); // Higher confidence first
        expect(defects[1]).toHaveTextContent('80%');
      });
    });
  });

  describe('Defect Actions', () => {
    test('can apply AI suggestion to fix defect', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);
      applySuggestion.mockResolvedValue({ success: true });

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Click apply suggestion button
      const applyButton = screen.getByRole('button', { name: /apply suggestion/i });
      fireEvent.click(applyButton);

      await waitFor(() => {
        expect(applySuggestion).toHaveBeenCalledWith('defect-1', true);
        expect(screen.getByText(/suggestion applied successfully/i)).toBeInTheDocument();
      });
    });

    test('can mark defect as false positive', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);
      markDefectAsFalsePositive.mockResolvedValue({ success: true });

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Click false positive button
      const falsePositiveButton = screen.getByRole('button', { name: /false positive/i });
      fireEvent.click(falsePositiveButton);

      // Add note
      const noteInput = screen.getByLabelText(/note/i);
      const confirmButton = screen.getByRole('button', { name: /mark as false positive/i });

      fireEvent.change(noteInput, { target: { value: 'This is clear enough' } });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(markDefectAsFalsePositive).toHaveBeenCalledWith('defect-1', {
          is_false_positive: true,
          user_note: 'This is clear enough'
        });
        expect(screen.getByText(/marked as false positive/i)).toBeInTheDocument();
      });
    });

    test('shows error when applying suggestion fails', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);
      applySuggestion.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      const applyButton = screen.getByRole('button', { name: /apply suggestion/i });
      fireEvent.click(applyButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to apply suggestion/i)).toBeInTheDocument();
      });
    });
  });

  describe('Validation Actions', () => {
    test('can run new validation', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(null);
      runValidation.mockResolvedValue({
        validation_id: 'new-validation-id',
        status: 'running'
      });

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /run validation/i })).toBeInTheDocument();
      });

      const runValidationButton = screen.getByRole('button', { name: /run validation/i });
      fireEvent.click(runValidationButton);

      await waitFor(() => {
        expect(runValidation).toHaveBeenCalledWith('test-doc-id');
        expect(screen.getByText(/validation started/i)).toBeInTheDocument();
      });
    });

    test('shows validation progress', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue({
        validation_id: 'running-validation-id',
        status: 'running',
        progress: 50
      });

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/validation in progress/i)).toBeInTheDocument();
        expect(screen.getByText('50%')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    test('can export results as PDF', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      // Mock document.createElement for download
      const mockLink = { click: jest.fn(), href: '', download: '' };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export pdf/i })).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export pdf/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockLink.download).toMatch(/\.pdf$/);
      });
    });

    test('can export results as Excel', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      // Mock document.createElement for download
      const mockLink = { click: jest.fn(), href: '', download: '' };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export excel/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockLink.download).toMatch(/\.xlsx$/);
      });
    });
  });

  describe('Search and Filter', () => {
    test('can search defects by keyword', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Search for "ambiguous"
      const searchInput = screen.getByLabelText(/search defects/i);
      fireEvent.change(searchInput, { target: { value: 'ambiguous' } });

      await waitFor(() => {
        expect(screen.getByText(/ambiguity/i)).toBeInTheDocument();
        expect(screen.queryByText(/incompleteness/i)).not.toBeInTheDocument();
      });
    });

    test('can filter by confidence threshold', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      // Filter by confidence >= 85%
      const confidenceFilter = screen.getByLabelText(/min confidence/i);
      fireEvent.change(confidenceFilter, { target: { value: '85' } });

      await waitFor(() => {
        expect(screen.getByText(/incompleteness/i)).toBeInTheDocument(); // 90% confidence
        expect(screen.queryByText(/ambiguity/i)).not.toBeInTheDocument(); // 80% confidence
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check form elements have proper labels
        expect(screen.getByLabelText(/search defects/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/severity/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/defect type/i)).toBeInTheDocument();
        
        // Check buttons have proper roles
        expect(screen.getByRole('button', { name: /export pdf/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /apply suggestion/i })).toBeInTheDocument();
      });
    });

    test('supports keyboard navigation', async () => {
      getDocument.mockResolvedValue(mockDocument);
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/defects found/i)).toBeInTheDocument();
      });

      const searchInput = screen.getByLabelText(/search defects/i);
      const exportButton = screen.getByRole('button', { name: /export pdf/i });

      // Tab navigation
      searchInput.focus();
      expect(document.activeElement).toBe(searchInput);

      fireEvent.tab();
      expect(document.activeElement).toBe(exportButton);

      // Enter key on buttons
      fireEvent.keyDown(exportButton, { key: 'Enter', code: 'Enter' });
      // Should trigger export functionality
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
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/analysis results/i)).toBeInTheDocument();
        // Should have mobile-specific layout
        expect(screen.getByTestId('mobile-layout')).toBeInTheDocument();
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
      getValidationResults.mockResolvedValue(mockValidationResults);

      render(
        <TestWrapper>
          <AnalysisResults />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/analysis results/i)).toBeInTheDocument();
        // Should have desktop-specific layout
        expect(screen.getByTestId('desktop-layout')).toBeInTheDocument();
      });
    });
  });
});
