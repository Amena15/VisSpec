import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { authAPI } from '../services/api';

const ResetPassword = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [error, setError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [tokenValid, setTokenValid] = useState(true);
  const navigate = useNavigate();
  const { token } = useParams();

  // Validate password strength (min 8 chars + at least 1 number + at least 1 special char)
  const validatePassword = (password) => {
    const hasMinLength = password.length >= 8;
    const hasNumber = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    return hasMinLength && hasNumber && hasSpecialChar;
  };

  // Password strength indicator
  const getPasswordStrength = (password) => {
    if (!password) return { label: '', score: 0 };
    
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 1) return { label: 'Weak', score: 1, color: 'bg-red-500' };
    if (score <= 2) return { label: 'Fair', score: 2, color: 'bg-orange-500' };
    if (score <= 3) return { label: 'Good', score: 3, color: 'bg-yellow-500' };
    return { label: 'Strong', score: 4, color: 'bg-green-500' };
  };

  const strength = getPasswordStrength(password);

  // Validate token on component mount
  useEffect(() => {
    const validateToken = async () => {
      try {
        await authAPI.verifyResetToken({
          token: token
        });
      } catch (err) {
        setTokenValid(false);
        setError('This reset link has expired or is invalid. Please request a new one.');
      }
    };

    if (token) {
      validateToken();
    } else {
      setTokenValid(false);
      setError('Invalid reset link. Please request a new one.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setPasswordError('');
    setConfirmPasswordError('');
    
    // Client-side validation
    let isValid = true;
    if (!validatePassword(password)) {
      setPasswordError('Password must be at least 8 characters, include a number, and a special character');
      isValid = false;
    }
    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      isValid = false;
    }

    if (!isValid) return;

    setIsLoading(true);

    try {
      await authAPI.resetPassword({
        token: token,
        new_password: password
      });

      setSuccessMessage('Password updated successfully!');
      
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
        setError('Failed to reset password. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!tokenValid) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-primary p-4">
        <div className="bg-card w-full max-w-md p-8 rounded-2xl shadow-sm border border-theme">
          <div className="text-center mb-8">
            <div className="mx-auto flex items-center justify-center w-12 h-12 rounded-full bg-accent-primary/10 mb-4">
              <div className="w-6 h-6 rounded-full bg-accent-primary"></div>
            </div>
            <h1 className="text-2xl font-bold text-primary">VisSpec</h1>
            <p className="mt-2 text-sm text-secondary">
              Reset Password
            </p>
          </div>

          <div className="mb-6">
            <div className="bg-error/10 border border-error/20 text-error px-4 py-3 rounded-md text-sm" role="alert">
              <span className="block">{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            </div>
          </div>

          <div className="pt-6 border-t border-theme mt-6">
            <div className="text-center text-sm text-secondary">
              <p>Go back to{' '}
                <button
                  onClick={() => navigate('/login')}
                  className="text-accent-primary hover:text-accent-secondary font-medium"
                >
                  Login
                </button>{' '}
                or{' '}
                <button
                  onClick={() => navigate('/forgot-password')}
                  className="text-accent-primary hover:text-accent-secondary font-medium"
                >
                  Request new link
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
            Create new password
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
              <label htmlFor="password" className="block text-sm font-medium text-primary mb-1">
                New Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                className={`w-full px-4 py-3 rounded-lg border ${
                  passwordError ? 'border-error bg-error/5' : 'border-theme bg-surface'
                } focus:ring-2 focus:ring-accent-primary focus:bg-card outline-none transition-all`}
                placeholder="Enter new password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (passwordError && validatePassword(e.target.value)) {
                    setPasswordError('');
                  }
                  if (confirmPasswordError && e.target.value === confirmPassword) {
                    setConfirmPasswordError('');
                  }
                }}
                aria-invalid={!!passwordError}
                aria-describedby={passwordError ? "password-error" : undefined}
              />

              {/* Password Strength Indicator */}
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs text-secondary mb-1">
                  <span>Password strength:</span>
                  <span className={strength.color.replace('bg-', 'text-')}>{strength.label}</span>
                </div>
                <div className="w-full bg-theme rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${strength.color}`}
                    style={{ width: `${(strength.score / 4) * 100}%` }}
                  ></div>
                </div>
              </div>

              {passwordError && (
                <p id="password-error" className="mt-1 text-sm text-error">
                  {passwordError}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-primary mb-1">
                Confirm New Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                className={`w-full px-4 py-3 rounded-lg border ${
                  confirmPasswordError ? 'border-error bg-error/5' : 'border-theme bg-surface'
                } focus:ring-2 focus:ring-accent-primary focus:bg-card outline-none transition-all`}
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (confirmPasswordError && e.target.value === password) {
                    setConfirmPasswordError('');
                  }
                }}
              />
              {confirmPasswordError && (
                <p className="mt-1 text-sm text-error">
                  {confirmPasswordError}
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
                {isLoading ? 'Updating password...' : 'Update Password'}
              </button>
            </div>
          </form>
        )}

        <div className="pt-6 border-t border-theme mt-6">
          <div className="text-center text-sm text-secondary">
            <p>Go back to{' '}
              <button
                onClick={() => navigate('/login')}
                className="text-accent-primary hover:text-accent-secondary font-medium"
              >
                Login
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;