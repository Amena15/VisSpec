import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { TrendingUp, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

const DashboardCharts = ({ documents, stats, loading }) => {
  // Prepare data for charts based on real documents
  const prepareQualityDistribution = () => {
    const qualityRanges = [
      { name: 'Excellent (90-100)', count: 0, color: '#10B981' },
      { name: 'Good (70-89)', count: 0, color: '#3B82F6' },
      { name: 'Fair (50-69)', count: 0, color: '#F59E0B' },
      { name: 'Poor (0-49)', count: 0, color: '#EF4444' }
    ];

    documents.forEach(doc => {
      const score = doc.qualityScore || 0;
      if (score >= 90) qualityRanges[0].count++;
      else if (score >= 70) qualityRanges[1].count++;
      else if (score >= 50) qualityRanges[2].count++;
      else qualityRanges[3].count++;
    });

    return qualityRanges.filter(range => range.count > 0);
  };

  const prepareComplexityData = () => {
    const complexityData = [
      { name: 'Low', count: 0, color: '#10B981' },
      { name: 'Medium', count: 0, color: '#F59E0B' },
      { name: 'High', count: 0, color: '#EF4444' }
    ];

    documents.forEach(doc => {
      const complexity = doc.complexity || 'Medium';
      const index = complexityData.findIndex(item => item.name === complexity);
      if (index !== -1) complexityData[index].count++;
    });

    return complexityData;
  };

  const prepareStatusData = () => {
    const statusData = [
      { name: 'Completed', count: 0, color: '#10B981' },
      { name: 'In Progress', count: 0, color: '#3B82F6' },
      { name: 'Ready for Analysis', count: 0, color: '#F59E0B' }
    ];

    const normalizeToBucket = (rawStatus) => {
      const s = (rawStatus || '').toString().trim().toLowerCase();

      if (
        s === 'completed' ||
        s === 'analyzed & organized' ||
        s === 'validated - issues found' ||
        s === 'validated - minor issues' ||
        s === 'validated'
      ) {
        return 'Completed';
      }

      if (
        s === 'in-progress' ||
        s === 'in progress' ||
        s === 'ready for analysis' ||
        s === 'uploading' ||
        s === 'pending' ||
        s === 'processing' ||
        s === 'in_progress'
      ) {
        return s === 'ready for analysis' || s === 'pending' || s === 'processing' ? 'Ready for Analysis' : 'In Progress';
      }

      // If backend returns plain 'ready'/'pass' etc, treat them as ready.
      if (s === 'ready' || s === 'pass' || s === 'passed') return 'Ready for Analysis';

      // Fallback bucket so we never drop data completely.
      return 'Ready for Analysis';
    };

    documents.forEach(doc => {
      const bucket = normalizeToBucket(doc.status);
      const index = statusData.findIndex(item => item.name === bucket);
      if (index !== -1) statusData[index].count++;
    });

    // Keep buckets with 0 only if you want a fixed axis; here we keep only >0 to avoid clutter.
    return statusData.filter(item => item.count > 0);
  };

  const prepareMonthlyTrend = () => {
    const monthlyData = [];
    const now = new Date();
    
    // Group documents by actual upload date
    const documentsByMonth = {};
    
    documents.forEach(doc => {
      let uploadDate;
      try {
        uploadDate = new Date(doc.uploadedAt || doc.upload_date || Date.now());
      } catch (error) {
        uploadDate = new Date(); // Fallback to current date
      }
      
      const monthKey = uploadDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      
      if (!documentsByMonth[monthKey]) {
        documentsByMonth[monthKey] = {
          documents: 0,
          totalQuality: 0,
          qualityCount: 0
        };
      }
      
      documentsByMonth[monthKey].documents++;
      if (doc.qualityScore) {
        documentsByMonth[monthKey].totalQuality += doc.qualityScore;
        documentsByMonth[monthKey].qualityCount++;
      }
    });
    
    // Generate last 6 months with real data or zeros
    for (let i = 5; i >= 0; i--) {
      const month = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthName = month.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      
      const monthData = documentsByMonth[monthName] || { documents: 0, totalQuality: 0, qualityCount: 0 };
      
      monthlyData.push({
        month: monthName,
        documents: monthData.documents,
        avgQuality: monthData.qualityCount > 0 
          ? Math.round(monthData.totalQuality / monthData.qualityCount)
          : 0
      });
    }
    
    return monthlyData;
  };

  const qualityDistribution = prepareQualityDistribution();
  const complexityData = prepareComplexityData();
  const statusData = prepareStatusData();
  const monthlyTrend = prepareMonthlyTrend();

  // Custom tooltip components
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-slate-800 p-3 border border-gray-200 dark:border-slate-700 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 dark:text-slate-100">{label}</p>

          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-slate-800 p-3 border border-gray-200 dark:border-slate-700 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 dark:text-slate-100">{payload[0].name}</p>

          <p className="text-sm text-gray-600">Count: {payload[0].value}</p>
          <p className="text-sm text-gray-600">
            Percentage: {((payload[0].value / documents.length) * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)] animate-pulse">
            <div className="h-64 bg-gray-200 rounded-lg mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-48"></div>
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="bg-[var(--card-bg)] rounded-xl p-8 shadow-sm border border-[var(--card-border)] text-center">
        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
        <p className="text-gray-600">Upload documents to see analytics and statistics.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Charts Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Analytics & Statistics</h2>
        <div className="flex items-center space-x-4 text-sm text-[var(--text-secondary)]">
          <span>Total Documents: {documents.length}</span>
          <span>•</span>
          <span>Avg Quality: {stats.avgQualityScore}%</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Distribution Pie Chart */}
        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-[var(--text-primary)]">Quality Distribution</h3>
            <TrendingUp className="w-5 h-5 text-[var(--success-main)]" />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={qualityDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {qualityDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Complexity Bar Chart */}
        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-[var(--text-primary)]">Complexity Analysis</h3>
            <FileText className="w-5 h-5 text-[var(--primary-main)]" />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={complexityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280' }} />
              <YAxis tick={{ fill: '#6b7280' }} />

              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#3B82F6" radius={[8, 8, 0, 0]}>

                {complexityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-[var(--text-primary)]">Document Status</h3>
            <CheckCircle className="w-5 h-5 text-[var(--success-main)]" />
          </div>

          {statusData.length === 0 ? (
            <div className="h-[250px] flex flex-col items-center justify-center text-center px-4">
              <div className="w-12 h-12 rounded-full bg-[var(--surface-bg)] border border-[var(--card-border)] flex items-center justify-center mb-3">
                <CheckCircle className="w-6 h-6 text-[var(--success-main)]" />
              </div>
              <h4 className="text-[var(--text-primary)] font-medium mb-1">Ready documents will appear here</h4>
              <p className="text-[var(--text-secondary)] text-sm">No status counts available yet. Upload documents to populate this chart.</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={statusData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                {/* When layout="horizontal", X should be the category labels and Y should be the numeric values */}
                <XAxis dataKey="name" type="category" tick={{ fill: '#6b7280' }} />
                <YAxis dataKey="count" type="number" tick={{ fill: '#6b7280' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" radius={[0, 8, 8, 0]}>
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Monthly Trend */}
        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-[var(--text-primary)]">Monthly Trend</h3>
            <TrendingUp className="w-5 h-5 text-[var(--primary-main)]" />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={monthlyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fill: '#6b7280' }} />
              <YAxis yAxisId="left" tick={{ fill: '#6b7280' }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#6b7280' }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="documents" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 4 }}
                name="Documents"
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="avgQuality" 
                stroke="#10B981" 
                strokeWidth={2}
                dot={{ fill: '#10B981', r: 4 }}
                name="Avg Quality (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/40 dark:to-green-900/20 border border-green-200 dark:border-green-800/60 rounded-lg p-4">

          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-green-900">Completion Rate</p>
              <p className="text-2xl font-bold text-green-900">
                {documents.length > 0 ? Math.round((stats.analyzedDocuments / documents.length) * 100) : 0}%
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/40 dark:to-blue-900/20 border border-blue-200 dark:border-blue-800/60 rounded-lg p-4">

          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-blue-900">Avg Quality Score</p>
              <p className="text-2xl font-bold text-blue-900">{stats.avgQualityScore}%</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-amber-50 to-amber-100 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-amber-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-amber-900">Total Issues</p>
              <p className="text-2xl font-bold text-amber-900">{stats.totalDefects}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardCharts;
