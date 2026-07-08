import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { toast } from 'sonner';
import AnalystDashboard from '../../pages/AnalystDashboard';
import { documentAPI, projectAPI } from '../../services/api';

// Mock the API calls
jest.mock('../../services/api');
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

// Mock the custom hook
jest.mock('../../hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    documents: [
      {
        id: '1',
        title: 'Test Document',
        filename: 'test.pdf',
        uploadedAt: '2024-01-01',
        status: 'completed',
        qualityScore: 85,
        complexity: 'Medium',
        defects: 3,
        effortEstimate: '1 week',
        comments: 'Test comments',
      },
    ],
    projects: [
      {
        id: '1',
        name: 'Test Project',
        status: 'ready',
      },
    ],
    stats: {
      totalDocuments: 1,
      analyzedDocuments: 1,
      avgQualityScore: 85,
      totalDefects: 3,
      myProjects: 1,
      completedProjects: 0,
      inProgressProjects: 1,
      totalRequirements: 10,
      avgComplexity: 'Medium',
    },
    loading: {
      documents: false,
      projects: false,
      stats: false,
    },
    error: {
      documents: null,
      projects: null,
      stats: null,
    },
    refreshData: jest.fn(),
    loadDocuments: jest.fn(),
    loadProjects: jest.fn(),
  }),
}));

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('AnalystDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with correct statistics', async () => {
    renderWithRouter(<AnalystDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('My Workspace')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // My Projects
      expect(screen.getByText('1')).toBeInTheDocument(); // Documents
      expect(screen.getByText('1')).toBeInTheDocument(); // Analyzed
      expect(screen.getByText('85%')).toBeInTheDocument(); // Avg Quality
    });
  });

  test('renders documents table when data is available', async () => {
    renderWithRouter(<AnalystDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('test.pdf')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument(); // Quality Score
      expect(screen.getByText('Medium')).toBeInTheDocument(); // Complexity
      expect(screen.getByText('3')).toBeInTheDocument(); // Defects
    });
  });

  test('shows loading skeletons while loading', () => {
    // Override the mock to show loading state
    const { useDashboardData } = require('../../hooks/useDashboardData');
    jest.spyOn(require('react'), 'useState').mockReturnValue([true, jest.fn()]);
    
    renderWithRouter(<AnalystDashboard />);
    
    // Should show skeleton components
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  test('shows empty state when no documents', async () => {
    // Override the mock to return empty documents
    const { useDashboardData } = require('../../hooks/useDashboardData');
    useDashboardData.mockReturnValue({
      documents: [],
      projects: [],
      stats: {
        totalDocuments: 0,
        analyzedDocuments: 0,
        avgQualityScore: 0,
        totalDefects: 0,
        myProjects: 0,
        completedProjects: 0,
        inProgressProjects: 0,
        totalRequirements: 0,
        avgComplexity: 'Low',
      },
      loading: { documents: false, projects: false, stats: false },
      error: { documents: null, projects: null, stats: null },
      refreshData: jest.fn(),
      loadDocuments: jest.fn(),
      loadProjects: jest.fn(),
    });

    renderWithRouter(<AnalystDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('No documents found')).toBeInTheDocument();
      expect(screen.getByText('Upload your first requirements document to get started with analysis.')).toBeInTheDocument();
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });
  });

  test('handles refresh button click', async () => {
    const mockRefreshData = jest.fn();
    const { useDashboardData } = require('../../hooks/useDashboardData');
    useDashboardData.mockReturnValue({
      documents: [],
      projects: [],
      stats: {
        totalDocuments: 0,
        analyzedDocuments: 0,
        avgQualityScore: 0,
        totalDefects: 0,
        myProjects: 0,
        completedProjects: 0,
        inProgressProjects: 0,
        totalRequirements: 0,
        avgComplexity: 'Low',
      },
      loading: { documents: false, projects: false, stats: false },
      error: { documents: null, projects: null, stats: null },
      refreshData: mockRefreshData,
      loadDocuments: jest.fn(),
      loadProjects: jest.fn(),
    });

    renderWithRouter(<AnalystDashboard />);
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(mockRefreshData).toHaveBeenCalled();
      expect(toast.success).toHaveBeenCalledWith('Dashboard data refreshed successfully');
    });
  });

  test('opens comment modal when comment is clicked', async () => {
    renderWithRouter(<AnalystDashboard />);
    
    await waitFor(() => {
      const commentButton = screen.getByText('Test comments');
      fireEvent.click(commentButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Document Comments')).toBeInTheDocument();
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });
  });

  test('shows analysis summary when there are analyzed documents', async () => {
    renderWithRouter(<AnalystDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('System Analysis Summary')).toBeInTheDocument();
      expect(screen.getByText('Based on 1 analyzed documents with 10 total requirements.')).toBeInTheDocument();
      expect(screen.getByText('Documents Analyzed: 1')).toBeInTheDocument();
      expect(screen.getByText('Total Defects: 3')).toBeInTheDocument();
      expect(screen.getByText('Requirements: 10')).toBeInTheDocument();
    });
  });
});
