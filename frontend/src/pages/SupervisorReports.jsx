import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  BarChart3,
  Users,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Calendar,
  Filter,
  Loader2,
  Search,
  ArrowUp,
  ArrowDown,
  ChevronRight
} from 'lucide-react';
import { apiClient } from '../services/api';

const SupervisorReports = () => {
  const navigate = useNavigate();
  const [reportsData, setReportsData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  
  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('all');
  const [minQuality, setMinQuality] = useState('');
  const [maxQuality, setMaxQuality] = useState('');
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  
  // Sorting states
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    loadReports();
  }, [currentPage, searchTerm, reviewStatusFilter, minQuality, maxQuality]);

  const loadReports = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        ...(searchTerm && { search: searchTerm }),
        ...(reviewStatusFilter !== 'all' && { review_status: reviewStatusFilter }),
        ...(minQuality && { min_quality: minQuality }),
        ...(maxQuality && { max_quality: maxQuality })
      });

      const response = await apiClient.get(`/api/supervisor/reports?${params}`);
      setReportsData(response.data);
      setSummary(response.data.summary);
    } catch (error) {
      console.error('Failed to load reports:', error);
      toast.error('Failed to load supervisor reports');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    setCurrentPage(1); // Reset to first page when sorting
  };

  const getSortIcon = (field) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />;
  };

  const getQualityColor = (score) => {
    if (score >= 70) return 'bg-green-100 text-green-800';
    if (score >= 40) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getReviewStatusColor = (status) => {
    switch(status) {
      case 'not_reviewed': return 'bg-gray-100 text-gray-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'changes_requested': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getComplexityColor = (level) => {
    switch(level) {
      case 'High': return 'bg-red-100 text-red-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportCSV = async () => {
    try {
      setIsExporting(true);
      
      // Create CSV content
      const headers = [
        'Project Name',
        'Owner Email',
        'Created Date',
        'Total Requirements',
        'Quality Score',
        'Defect Count',
        'Complexity Level',
        'Review Status',
        'Last Validation Date'
      ];

      const csvContent = [
        headers.join(','),
        ...(reportsData.projects || []).map(project => [
          `"${project.name}"`,
          `"${project.owner_email}"`,
          project.created_at || '',
          project.total_requirements || 0,
          project.quality_score || 0,
          project.defect_count || 0,
          project.complexity_level || 'Unknown',
          project.review_status || 'Unknown',
          project.latest_validation_date || ''
        ].join(','))
      ].join('\n');

      // Create download link
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `supervisor_reports_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('CSV exported successfully');
    } catch (error) {
      console.error('Failed to export CSV:', error);
      toast.error('Failed to export CSV');
    } finally {
      setIsExporting(false);
    }
  };

  const exportPDF = async () => {
    try {
      setIsExporting(true);
      
      const reportData = {
        report_type: 'supervisor_reports',
        title: 'Supervisor Reports',
        subtitle: `Generated on ${new Date().toLocaleDateString()}`,
        summary_stats: summary,
        projects: reportsData.projects,
        filters: {
          search: searchTerm,
          review_status: reviewStatusFilter,
          quality_range: minQuality && maxQuality ? `${minQuality}-${maxQuality}` : 'All'
        }
      };

      const response = await apiClient.post('/api/reports/export', reportData);
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `supervisor_reports_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('PDF exported successfully');
    } catch (error) {
      console.error('Failed to export PDF:', error);
      toast.error('Failed to export PDF');
    } finally {
      setIsExporting(false);
    }
  };

  const handleProjectClick = (projectId) => {
    navigate(`/supervisor/review/${projectId}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Supervisor Reports</h1>
              <p className="text-gray-600 mt-2">Aggregated view of all student projects with quality metrics and review status</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={exportCSV}
                disabled={isExporting || !reportsData?.projects?.length}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="h-4 w-4" />
                Export CSV
              </button>
              <button
                onClick={exportPDF}
                disabled={isExporting || !reportsData?.projects?.length}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExporting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Export PDF
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-blue-100 mr-4">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{summary.total_projects}</div>
                  <div className="text-sm text-gray-600">Total Projects</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-green-100 mr-4">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{summary.average_quality_score}%</div>
                  <div className="text-sm text-gray-600">Avg Quality Score</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-red-100 mr-4">
                  <XCircle className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">{summary.total_defects}</div>
                  <div className="text-sm text-gray-600">Total Defects</div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-lg bg-purple-100 mr-4">
                  <CheckCircle className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">{summary.approved_projects}</div>
                  <div className="text-sm text-gray-600">
                    {summary.pending_review} pending / {summary.changes_requested} changes
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search projects or owners..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <select
              value={reviewStatusFilter}
              onChange={(e) => {
                setReviewStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="not_reviewed">Not Reviewed</option>
              <option value="approved">Approved</option>
              <option value="changes_requested">Changes Requested</option>
            </select>

            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={minQuality}
                onChange={(e) => {
                  setMinQuality(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-20 px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
                max="100"
              />
              <span className="text-gray-500">-</span>
              <input
                type="number"
                placeholder="Max"
                value={maxQuality}
                onChange={(e) => {
                  setMaxQuality(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-20 px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min="0"
                max="100"
              />
              <span className="text-sm text-gray-600">Quality</span>
            </div>
          </div>
        </div>

        {/* Projects Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('name')}>
                    <div className="flex items-center gap-1">
                      Project Name
                      {getSortIcon('name')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('owner_email')}>
                    <div className="flex items-center gap-1">
                      Owner
                      {getSortIcon('owner_email')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('created_at')}>
                    <div className="flex items-center gap-1">
                      Created
                      {getSortIcon('created_at')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('total_requirements')}>
                    <div className="flex items-center gap-1">
                      Requirements
                      {getSortIcon('total_requirements')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('quality_score')}>
                    <div className="flex items-center gap-1">
                      Quality Score
                      {getSortIcon('quality_score')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('defect_count')}>
                    <div className="flex items-center gap-1">
                      Defects
                      {getSortIcon('defect_count')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('complexity_level')}>
                    <div className="flex items-center gap-1">
                      Complexity
                      {getSortIcon('complexity_level')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('review_status')}>
                    <div className="flex items-center gap-1">
                      Status
                      {getSortIcon('review_status')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('latest_validation_date')}>
                    <div className="flex items-center gap-1">
                      Last Validation
                      {getSortIcon('latest_validation_date')}
                    </div>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reportsData?.projects?.map((project) => (
                  <tr key={project.project_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer" onClick={() => handleProjectClick(project.project_id)}>
                        {project.name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{project.owner_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{project.created_at?.split('T')[0] || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{project.total_requirements || 0}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getQualityColor(project.quality_score)}`}>
                        {project.quality_score || 0}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{project.defect_count || 0}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getComplexityColor(project.complexity_level)}`}>
                        {project.complexity_level || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getReviewStatusColor(project.review_status)}`}>
                        {project.review_status?.replace('_', ' ') || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{project.latest_validation_date?.split('T')[0] || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => handleProjectClick(project.project_id)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                      >
                        Review
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {reportsData?.pagination && reportsData.pagination.total_pages > 1 && (
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-3 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {((reportsData.pagination.page - 1) * reportsData.pagination.page_size) + 1} to{' '}
                {Math.min(reportsData.pagination.page * reportsData.pagination.page_size, reportsData.pagination.total_count)} of{' '}
                {reportsData.pagination.total_count} projects
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(reportsData.pagination.page - 1)}
                  disabled={reportsData.pagination.page === 1}
                  className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700">
                  Page {reportsData.pagination.page} of {reportsData.pagination.total_pages}
                </span>
                <button
                  onClick={() => setCurrentPage(reportsData.pagination.page + 1)}
                  disabled={reportsData.pagination.page === reportsData.pagination.total_pages}
                  className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupervisorReports;
