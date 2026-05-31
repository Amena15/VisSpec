import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, MessageSquare, Clock, User, FileText, AlertTriangle, ArrowLeft, Shield, Eye } from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../services/api';
import { toast } from 'sonner';

const SupervisorReview = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [reviewDecision, setReviewDecision] = useState('');
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [projectData, setProjectData] = useState(null);
  const [requirements, setRequirements] = useState([]);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const loadProjectData = async () => {
      try {
        const response = await apiClient.get(`/api/supervisor/review/${projectId}`);
        setProjectData(response.data.project);
        setRequirements(response.data.traceability || []);
        setMetrics(response.data.metrics);
      } catch (error) {
        console.error('Failed to load project data:', error);
        toast.error('Failed to load project data');
      }
    };

    if (projectId) {
      loadProjectData();
    }
  }, [projectId]);

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!reviewDecision) {
      toast.error('Please select a review decision');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post(`/api/supervisor/review/${projectId}`, {
        decision: reviewDecision,
        comments: feedback
      });
      
      toast.success('Review submitted successfully');
      navigate('/supervisor/dashboard');
    } catch (error) {
      console.error('Error submitting review:', error);
      toast.error('Failed to submit review. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!projectData) {
    return (
      <div className="min-h-screen bg-[var(--content-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-main)]"></div>
          <p className="mt-4 text-[var(--text-secondary)]">Loading project data...</p>
        </div>
      </div>
    );
  }

  const qualityScore = metrics?.quality_score || 0;
  const totalDefects = requirements.reduce((sum, req) => sum + (req.defect_count || 0), 0);
  const validRequirements = requirements.filter(req => req.validation_status === 'passed').length;

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/supervisor/dashboard')}
          className="flex items-center text-[var(--neutral-500)] hover:text-[var(--neutral-900)] mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </button>

        <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[var(--neutral-900)]">{projectData.name}</h1>
              <div className="flex items-center mt-2 text-sm text-[var(--neutral-500)]">
                <User className="w-4 h-4 mr-2" />
                <span>Project ID: {projectData.project_id}</span>
                <Clock className="w-4 h-4 ml-4 mr-2" />
                <span>Status: {projectData.status}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-[var(--neutral-500)]">Quality Score</div>
              <div className="text-2xl font-bold text-[var(--success-main)]">{qualityScore.toFixed(1)}%</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Requirements Panel - Read Only */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
            <h2 className="text-lg font-semibold text-[var(--neutral-900)] mb-4">Requirements Review</h2>

            <div className="space-y-4">
              {requirements.map((req) => (
                <div
                  key={req.req_id}
                  className={`p-4 rounded-lg border ${
                    req.validation_status === 'passed'
                      ? 'border-[var(--success-light)] bg-[var(--success-light)]/30'
                      : 'border-[var(--error-light)] bg-[var(--error-light)]/30'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="font-medium text-[var(--neutral-900)] mr-3">{req.identifier}</span>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          req.validation_status === 'passed'
                            ? 'bg-[var(--success-light)] text-[var(--success-hover)]'
                            : 'bg-[var(--error-light)] text-[var(--error-hover)]'
                        }`}>
                          {req.validation_status === 'passed' ? (
                            <>
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Valid
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              {req.validation_status}
                            </>
                          )}
                        </span>
                      </div>

                      <p className="text-sm text-[var(--neutral-700)] mb-3">{req.text}</p>

                      {req.defects && req.defects.length > 0 && (
                        <div className="space-y-2">
                          {req.defects.map((defect, idx) => (
                            <div key={idx} className="bg-[var(--card-bg)] rounded p-2 border border-[var(--card-border)]">
                              <div className="flex items-center text-xs font-medium text-[var(--error-hover)] mb-1">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                {defect.type.charAt(0).toUpperCase() + defect.type.slice(1)}
                              </div>
                              <p className="text-xs text-[var(--neutral-500)]">{defect.description}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Add Note button - visible to supervisors */}
                    <Link
                      to={`/traceability/${projectData.project_id}`}
                      className="ml-4 p-2 text-[var(--primary-main)] hover:bg-[var(--primary-50)] rounded"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Review Panel */}
        <div className="space-y-6">
          {/* Review Form */}
          <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)] sticky top-6">
            <h3 className="text-lg font-semibold text-[var(--neutral-900)] mb-4">Submit Review</h3>

            <form onSubmit={handleSubmitReview} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--neutral-700)] mb-2">
                  Review Decision
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="approved"
                      checked={reviewDecision === 'approved'}
                      onChange={(e) => setReviewDecision(e.target.value)}
                      className="mr-3"
                    />
                    <CheckCircle className="w-4 h-4 text-[var(--success-main)] mr-2" />
                    <span>Approve</span>
                  </label>

                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="changes_requested"
                      checked={reviewDecision === 'changes_requested'}
                      onChange={(e) => setReviewDecision(e.target.value)}
                      className="mr-3"
                    />
                    <XCircle className="w-4 h-4 text-[var(--warning-main)] mr-2" />
                    <span>Request Changes</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--neutral-700)] mb-2">
                  Feedback (Optional)
                </label>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Provide specific feedback for the author..."
                  rows={4}
                  className="w-full px-3 py-2 border border-[var(--card-border)] rounded-lg focus:ring-2 focus:ring-[var(--primary-main)] focus:border-transparent resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={loading || !reviewDecision}
                className="w-full py-3 bg-[var(--primary-main)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </>
                ) : (
                  'Submit Review'
                )}
              </button>
            </form>
          </div>

          {/* Project Summary */}
          <div className="bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)]">
            <h3 className="text-lg font-semibold text-[var(--neutral-900)] mb-4">Project Summary</h3>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Total Requirements:</span>
                <span className="text-sm font-medium">{requirements.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Valid Requirements:</span>
                <span className="text-sm font-medium text-[var(--success-main)]">{validRequirements}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Defective Requirements:</span>
                <span className="text-sm font-medium text-[var(--error-main)]">{requirements.length - validRequirements}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Total Defects:</span>
                <span className="text-sm font-medium text-[var(--error-main)]">{totalDefects}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-[var(--neutral-500)]">Quality Score:</span>
                <span className="text-sm font-medium">{qualityScore.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Business Rule Notice */}
      <div className="mt-6 bg-[var(--info-light)] border border-[var(--info-main)] rounded-lg p-4">
        <div className="flex items-start">
          <Shield className="w-5 h-5 text-[var(--info-dark)] mt-0.5 mr-2 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-[var(--neutral-900)] text-sm">Supervisor Review Guidelines</h4>
            <ul className="text-xs text-[var(--neutral-700)] mt-1 space-y-1">
              <li>• Reviews are read-only for supervisors (BR-18)</li>
              <li>• All feedback is visible to students (BR-19)</li>
              <li>• Approved projects are marked as finalized</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupervisorReview;