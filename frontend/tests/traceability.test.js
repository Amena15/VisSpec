import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Traceability from '../src/pages/Traceability';
import { AuthProvider } from '../src/contexts/AuthContext';
import { ProjectProvider } from '../src/contexts/ProjectContext';

// Mock the API calls
jest.mock('../src/services/api', () => ({
  getTraceabilityMatrix: jest.fn(),
  addTraceabilityNote: jest.fn(),
  editTraceabilityNote: jest.fn(),
  deleteTraceabilityNote: jest.fn(),
  getRequirementNotes: jest.fn(),
}));

import { 
  getTraceabilityMatrix, 
  addTraceabilityNote, 
  editTraceabilityNote, 
  deleteTraceabilityNote,
  getRequirementNotes 
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
const mockParams = { projectId: 'test-project-id' };

describe('Traceability Component', () => {
  const mockTraceabilityData = {
    requirements: [
      {
        req_id: 'req-1',
        req_identifier: 'REQ-001',
        original_text: 'The system shall allow users to login.',
        current_text: 'The system shall allow users to login.',
        category: 'functional',
        module_name: 'Authentication',
        validation_status: 'validated',
        notes_count: 0,
        semantic_id: 'FR-AUTH-01'
      },
      {
        req_id: 'req-2',
        req_identifier: 'REQ-002',
        original_text: 'The system must validate credentials.',
        current_text: 'The system must validate credentials.',
        category: 'security',
        module_name: 'Authentication',
        validation_status: 'validated',
        notes_count: 1,
        semantic_id: 'SEC-AUTH-01'
      },
      {
        req_id: 'req-3',
        req_identifier: 'REQ-003',
        original_text: 'The system should provide user profiles.',
        current_text: 'The system should provide user profiles.',
        category: 'functional',
        module_name: 'User Management',
        validation_status: 'pending',
        notes_count: 0,
        semantic_id: 'FR-USER-01'
      }
    ],
    matrix: {
      relationships: [
        {
          source_req_id: 'req-1',
          target_req_id: 'req-2',
          relationship_type: 'depends',
          confidence: 0.9
        }
      ],
      coverage_score: 85,
      traceability_gaps: []
    }
  };

  const mockNotes = [
    {
      note_id: 'note-1',
      req_id: 'req-2',
      content: 'This requirement needs clarification on error handling.',
      note_type: 'clarification',
      created_by: 'test-user',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
  ];

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
    test('renders traceability page correctly', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/traceability matrix/i)).toBeInTheDocument();
        expect(screen.getByText(/requirements/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /add note/i })).toBeInTheDocument();
        expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
      });
    });

    test('shows loading state while fetching data', () => {
      getTraceabilityMatrix.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      expect(screen.getByText(/loading traceability data/i)).toBeInTheDocument();
    });

    test('shows error state when API call fails', async () => {
      getTraceabilityMatrix.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/error loading traceability data/i)).toBeInTheDocument();
      });
    });

    test('shows empty state when no requirements exist', async () => {
      getTraceabilityMatrix.mockResolvedValue({
        requirements: [],
        matrix: { relationships: [], coverage_score: 0, traceability_gaps: [] }
      });

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/no requirements found/i)).toBeInTheDocument();
      });
    });
  });

  describe('Requirements Table', () => {
    test('displays requirements table with correct data', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check requirement data
        expect(screen.getByText('REQ-001')).toBeInTheDocument();
        expect(screen.getByText('The system shall allow users to login.')).toBeInTheDocument();
        expect(screen.getByText('functional')).toBeInTheDocument();
        expect(screen.getByText('Authentication')).toBeInTheDocument();
        expect(screen.getByText('validated')).toBeInTheDocument();
        
        expect(screen.getByText('REQ-002')).toBeInTheDocument();
        expect(screen.getByText('The system must validate credentials.')).toBeInTheDocument();
        expect(screen.getByText('security')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument(); // notes count
      });
    });

    test('filters requirements by category', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/filter by category/i)).toBeInTheDocument();
      });

      // Filter by functional requirements
      const categoryFilter = screen.getByLabelText(/filter by category/i);
      fireEvent.change(categoryFilter, { target: { value: 'functional' } });

      await waitFor(() => {
        expect(screen.getByText('REQ-001')).toBeInTheDocument();
        expect(screen.getByText('REQ-003')).toBeInTheDocument();
        expect(screen.queryByText('REQ-002')).not.toBeInTheDocument(); // security requirement
      });
    });

    test('filters requirements by module', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/filter by module/i)).toBeInTheDocument();
      });

      // Filter by Authentication module
      const moduleFilter = screen.getByLabelText(/filter by module/i);
      fireEvent.change(moduleFilter, { target: { value: 'Authentication' } });

      await waitFor(() => {
        expect(screen.getByText('REQ-001')).toBeInTheDocument();
        expect(screen.getByText('REQ-002')).toBeInTheDocument();
        expect(screen.queryByText('REQ-003')).not.toBeInTheDocument(); // User Management
      });
    });

    test('filters requirements by validation status', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/filter by status/i)).toBeInTheDocument();
      });

      // Filter by validated status
      const statusFilter = screen.getByLabelText(/filter by status/i);
      fireEvent.change(statusFilter, { target: { value: 'validated' } });

      await waitFor(() => {
        expect(screen.getByText('REQ-001')).toBeInTheDocument();
        expect(screen.getByText('REQ-002')).toBeInTheDocument();
        expect(screen.queryByText('REQ-003')).not.toBeInTheDocument(); // pending
      });
    });

    test('filters requirements with notes', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('checkbox', { name: /has notes/i })).toBeInTheDocument();
      });

      // Filter requirements with notes
      const hasNotesCheckbox = screen.getByRole('checkbox', { name: /has notes/i });
      fireEvent.click(hasNotesCheckbox);

      await waitFor(() => {
        expect(screen.getByText('REQ-002')).toBeInTheDocument(); // has 1 note
        expect(screen.queryByText('REQ-001')).not.toBeInTheDocument(); // no notes
        expect(screen.queryByText('REQ-003')).not.toBeInTheDocument(); // no notes
      });
    });

    test('searches requirements by keyword', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
      });

      // Search for "login"
      const searchInput = screen.getByLabelText(/search/i);
      fireEvent.change(searchInput, { target: { value: 'login' } });

      await waitFor(() => {
        expect(screen.getByText('REQ-001')).toBeInTheDocument(); // contains "login"
        expect(screen.queryByText('REQ-002')).not.toBeInTheDocument(); // doesn't contain "login"
        expect(screen.queryByText('REQ-003')).not.toBeInTheDocument(); // doesn't contain "login"
      });
    });
  });

  describe('Notes Management', () => {
    test('opens add note modal when clicking add note button', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add note/i })).toBeInTheDocument();
      });

      // Click add note button
      const addNoteButton = screen.getByRole('button', { name: /add note/i });
      fireEvent.click(addNoteButton);

      await waitFor(() => {
        expect(screen.getByText(/add traceability note/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/select requirement/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/note content/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/note type/i)).toBeInTheDocument();
      });
    });

    test('can add a new note', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);
      addTraceabilityNote.mockResolvedValue({
        note_id: 'new-note-id',
        content: 'Test note content',
        note_type: 'clarification'
      });

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      // Open add note modal
      const addNoteButton = screen.getByRole('button', { name: /add note/i });
      fireEvent.click(addNoteButton);

      await waitFor(() => {
        expect(screen.getByText(/add traceability note/i)).toBeInTheDocument();
      });

      // Fill form
      const requirementSelect = screen.getByLabelText(/select requirement/i);
      const contentInput = screen.getByLabelText(/note content/i);
      const typeSelect = screen.getByLabelText(/note type/i);
      const saveButton = screen.getByRole('button', { name: /save note/i });

      fireEvent.change(requirementSelect, { target: { value: 'req-1' } });
      fireEvent.change(contentInput, { target: { value: 'This is a test note.' } });
      fireEvent.change(typeSelect, { target: { value: 'clarification' } });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(addTraceabilityNote).toHaveBeenCalledWith({
          req_id: 'req-1',
          content: 'This is a test note.',
          note_type: 'clarification'
        });
        expect(screen.getByText(/note added successfully/i)).toBeInTheDocument();
      });
    });

    test('shows existing notes for requirement', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);
      getRequirementNotes.mockResolvedValue(mockNotes);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('REQ-002')).toBeInTheDocument();
      });

      // Click on notes count for REQ-002
      const notesLink = screen.getByText('1'); // notes count for REQ-002
      fireEvent.click(notesLink);

      await waitFor(() => {
        expect(getRequirementNotes).toHaveBeenCalledWith('req-2');
        expect(screen.getByText(/traceability notes/i)).toBeInTheDocument();
        expect(screen.getByText('This requirement needs clarification on error handling.')).toBeInTheDocument();
        expect(screen.getByText('clarification')).toBeInTheDocument();
      });
    });

    test('can edit existing note', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);
      getRequirementNotes.mockResolvedValue(mockNotes);
      editTraceabilityNote.mockResolvedValue({
        note_id: 'note-1',
        content: 'Updated note content',
        note_type: 'issue'
      });

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      // View notes for REQ-002
      const notesLink = screen.getByText('1');
      fireEvent.click(notesLink);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /edit note/i })).toBeInTheDocument();
      });

      // Click edit button
      const editButton = screen.getByRole('button', { name: /edit note/i });
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByText(/edit traceability note/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/note content/i)).toBeInTheDocument();
      });

      // Update note
      const contentInput = screen.getByLabelText(/note content/i);
      const updateButton = screen.getByRole('button', { name: /update note/i });

      fireEvent.change(contentInput, { target: { value: 'Updated note content.' } });
      fireEvent.click(updateButton);

      await waitFor(() => {
        expect(editTraceabilityNote).toHaveBeenCalledWith('note-1', {
          content: 'Updated note content.'
        });
        expect(screen.getByText(/note updated successfully/i)).toBeInTheDocument();
      });
    });

    test('can delete note', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);
      getRequirementNotes.mockResolvedValue(mockNotes);
      deleteTraceabilityNote.mockResolvedValue({ success: true });

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      // View notes for REQ-002
      const notesLink = screen.getByText('1');
      fireEvent.click(notesLink);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete note/i })).toBeInTheDocument();
      });

      // Click delete button
      const deleteButton = screen.getByRole('button', { name: /delete note/i });
      fireEvent.click(deleteButton);

      // Confirm deletion
      await waitFor(() => {
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /confirm delete/i })).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm delete/i });
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(deleteTraceabilityNote).toHaveBeenCalledWith('note-1');
        expect(screen.getByText(/note deleted successfully/i)).toBeInTheDocument();
      });
    });
  });

  describe('Traceability Matrix', () => {
    test('displays traceability relationships', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/traceability relationships/i)).toBeInTheDocument();
        expect(screen.getByText(/depends/i)).toBeInTheDocument();
        expect(screen.getByText(/REQ-001 -> REQ-002/i)).toBeInTheDocument();
      });
    });

    test('shows coverage score', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/coverage score/i)).toBeInTheDocument();
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });

    test('highlights traceability gaps', async () => {
      const dataWithGaps = {
        ...mockTraceabilityData,
        matrix: {
          ...mockTraceabilityData.matrix,
          traceability_gaps: [
            {
              req_id: 'req-3',
              gap_type: 'no_upstream_traces',
              description: 'No upstream requirements traced'
            }
          ]
        }
      };

      getTraceabilityMatrix.mockResolvedValue(dataWithGaps);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/traceability gaps/i)).toBeInTheDocument();
        expect(screen.getByText(/no upstream traces/i)).toBeInTheDocument();
        expect(screen.getByText('REQ-003')).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    test('can export traceability matrix as Excel', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      // Mock document.createElement for download
      const mockLink = { click: jest.fn(), href: '', download: '' };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export excel/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockLink.download).toMatch(/traceability_matrix.*\.xlsx$/i);
      });
    });

    test('can export traceability matrix as CSV', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      // Mock document.createElement for download
      const mockLink = { click: jest.fn(), href: '', download: '' };
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /export csv/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockLink.download).toMatch(/traceability_matrix.*\.csv$/i);
      });
    });
  });

  describe('Impact Analysis', () => {
    test('can perform impact analysis for requirement', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /impact analysis/i })).toBeInTheDocument();
      });

      // Click impact analysis button for REQ-001
      const impactButtons = screen.getAllByRole('button', { name: /impact analysis/i });
      fireEvent.click(impactButtons[0]); // First requirement

      await waitFor(() => {
        expect(screen.getByText(/impact analysis/i)).toBeInTheDocument();
        expect(screen.getByText(/affected requirements/i)).toBeInTheDocument();
        expect(screen.getByText(/impact score/i)).toBeInTheDocument();
      });
    });
  });

  describe('Validation', () => {
    test('validates note content length', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      // Open add note modal
      const addNoteButton = screen.getByRole('button', { name: /add note/i });
      fireEvent.click(addNoteButton);

      await waitFor(() => {
        expect(screen.getByText(/add traceability note/i)).toBeInTheDocument();
      });

      // Try to save with empty content
      const contentInput = screen.getByLabelText(/note content/i);
      const saveButton = screen.getByRole('button', { name: /save note/i });

      fireEvent.change(contentInput, { target: { value: '' } });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/note content is required/i)).toBeInTheDocument();
      });
    });

    test('validates requirement selection', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      // Open add note modal
      const addNoteButton = screen.getByRole('button', { name: /add note/i });
      fireEvent.click(addNoteButton);

      await waitFor(() => {
        expect(screen.getByText(/add traceability note/i)).toBeInTheDocument();
      });

      // Try to save without selecting requirement
      const contentInput = screen.getByLabelText(/note content/i);
      const saveButton = screen.getByRole('button', { name: /save note/i });

      fireEvent.change(contentInput, { target: { value: 'Test note content' } });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a requirement/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check form elements have proper labels
        expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/filter by category/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/filter by module/i)).toBeInTheDocument();
        
        // Check buttons have proper roles
        expect(screen.getByRole('button', { name: /add note/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument();
        
        // Check table has proper role
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });

    test('supports keyboard navigation', async () => {
      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText(/search/i)).toBeInTheDocument();
      });

      const searchInput = screen.getByLabelText(/search/i);
      const addNoteButton = screen.getByRole('button', { name: /add note/i });

      // Tab navigation
      searchInput.focus();
      expect(document.activeElement).toBe(searchInput);

      fireEvent.tab();
      expect(document.activeElement).toBe(addNoteButton);

      // Enter key activation
      fireEvent.keyDown(addNoteButton, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText(/add traceability note/i)).toBeInTheDocument();
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

      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/traceability matrix/i)).toBeInTheDocument();
        // Should have mobile-specific layout
        expect(screen.getByTestId('mobile-table')).toBeInTheDocument();
      });
    });

    test('renders correctly on desktop viewport', async () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });

      getTraceabilityMatrix.mockResolvedValue(mockTraceabilityData);

      render(
        <TestWrapper>
          <Traceability />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/traceability matrix/i)).toBeInTheDocument();
        // Should have desktop-specific layout
        expect(screen.getByTestId('desktop-table')).toBeInTheDocument();
      });
    });
  });
});
