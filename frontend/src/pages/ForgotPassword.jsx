import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');
  const [emailError, setEmailError] = useState('');
  const navigate = useNavigate();

  // Validate email format
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setEmailError('');
    
    // Client-side validation
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      // Send password reset request - email should be sent as query parameter
      const params = new URLSearchParams();
      params.append('email', email);
      await authAPI.forgotPassword(email);

      // Show generic success message to prevent email enumeration
      setSuccessMessage('If an account exists for this email, a reset link has been sent.');
      
      // Clear form
      setEmail('');
      
      // Auto-redirect to login after delay
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      if (err.response?.data?.detail) {
        // Handle simple error message
        setError(err.response.data.detail);
      } else if (err.response?.data?.detail?.length > 0) {
        // Handle validation error array
        const validationErrors = err.response.data.detail;
        if (Array.isArray(validationErrors) && validationErrors.length > 0) {
          const firstError = validationErrors[0];
          setError(firstError.msg || 'Validation error occurred');
        } else {
          setError('Validation error occurred');
        }
      } else {
        setError('Unable to send reset email. Please try again later.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-primary p-4">
      <div className="bg-card w-full max-w-md p-8 rounded-2xl shadow-sm border border-theme">
        {/* Logo Area */}
        <div className="text-center mb-8">
          <div className="mx-auto flex items-center justify-center w-12 h-12 rounded-full bg-accent-primary/10 mb-4">
            <div className="w-6 h-6 rounded-full bg-accent-primary"></div>
          </div>
          <h1 className="text-2xl font-bold text-primary">VisSpec</h1>
          <p className="mt-2 text-sm text-secondary">
            Reset your password
          </p>
        </div>

        {successMessage ? (
          <div className="mb-6">
            <div className="bg-success/10 border border-success/20 text-success px-4 py-3 rounded-md text-sm" role="alert">
              <span className="block">{successMessage}</span>
            </div>
            <p className="mt-4 text-sm text-secondary text-center">
              Redirecting to login...
            </p>
          </div>
        ) : (
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-error/10 border border-error/20 text-error px-4 py-3 rounded-md text-sm" role="alert">
                <span className="block">{typeof error === 'string' ? error : JSON.stringify(error)}</span>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-primary mb-1">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className={`w-full px-4 py-3 rounded-lg border ${
                  emailError ? 'border-error bg-error/5' : 'border-theme bg-surface'
                } focus:ring-2 focus:ring-accent-primary focus:bg-card outline-none transition-all`}
                placeholder="Enter your email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (emailError && validateEmail(e.target.value)) {
                    setEmailError('');
                  }
                }}
                aria-invalid={!!emailError}
                aria-describedby={emailError ? "email-error" : undefined}
              />
              {emailError && (
                <p id="email-error" className="mt-1 text-sm text-error">
                  {emailError}
                </p>
              )}
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className={`w-full py-3 rounded-lg text-white font-medium transition-all ${
                  isLoading
                    ? 'bg-accent-primary/50 cursor-not-allowed'
                    : 'bg-accent-primary hover:bg-accent-secondary'
                }`}
              >
                {isLoading ? 'Sending reset link...' : 'Send Reset Link'}
              </button>
            </div>
          </form>
        )}

        <div className="pt-6 border-t border-theme mt-6">
          <div className="text-center text-sm text-secondary">
            <p>Remember your password?{' '}
              <button
                onClick={() => navigate('/login')}
                className="text-accent-primary hover:text-accent-secondary font-medium"
              >
                Back to Login
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;