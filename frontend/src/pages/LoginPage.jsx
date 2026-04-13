import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { Brain } from 'lucide-react';

const LoginPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',  // Will be derived from email during registration
    email: '',
    password: '',
    confirmPassword: '',
    role: 'analyst' // Default to analyst role for all users
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  // Validation states
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [usernameError, setUsernameError] = useState('');

  // Validate email format
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  // Validate password strength according to backend requirements
  const validatePassword = (password) => {
    if (password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;  // At least one uppercase
    if (!/[a-z]/.test(password)) return false;  // At least one lowercase
    if (!/\d/.test(password)) return false;     // At least one digit
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return false;  // At least one special character
    return true;
  };

  // Validate username format according to backend requirements
  const validateUsername = (username) => {
    if (username.length < 3) return false;
    return /^[a-zA-Z0-9_-]+$/.test(username);  // Only letters, numbers, underscores, and hyphens
  };

  // Handle input changes with validation
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });

    // Real-time validation
    if (name === 'email') {
      if (value && !validateEmail(value)) {
        setEmailError('Please enter a valid email address');
      } else {
        setEmailError('');
      }
    }

    if (name === 'password') {
      if (value && !validatePassword(value)) {
        setPasswordError('Password must be 8+ chars with uppercase, lowercase, number & special char');
      } else {
        setPasswordError('');
      }
    }

    if (name === 'username') {
      if (value && !validateUsername(value)) {
        setUsernameError('Username must be 3+ chars with letters, numbers, underscore, hyphen');
      } else {
        setUsernameError('');
      }
    }
  };

  // Enhanced submit handler with validation
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setEmailError('');
    setPasswordError('');

    // Client-side validation
    let isValid = true;
    if (!validateEmail(formData.email)) {
      setEmailError('Please enter a valid email address');
      isValid = false;
    }
    if (!validatePassword(formData.password)) {
      setPasswordError('Password must be 8+ chars with uppercase, lowercase, number & special char');
      isValid = false;
    }
    if (!isLogin && !validateUsername(formData.username)) {
      setUsernameError('Username must be 3+ chars with letters, numbers, underscore, hyphen');
      isValid = false;
    }
    if (!isLogin && formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      isValid = false;
    }

    if (!isValid) {
      setIsLoading(false);
      return;
    }

    try {
      if (isLogin) {
        // Login - need to send as form URL-encoded for OAuth2PasswordRequestForm
        const response = await authAPI.login({
          username: formData.email,  // Use email as the username field for login
          password: formData.password
        });

        if (response.data.access_token) {
          onLogin(response.data.access_token);
        } else {
          throw new Error('Login response did not contain access token');
        }
      } else {
        // Registration
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          setIsLoading(false);
          return;
        }

        const response = await authAPI.register({
          username: formData.username || formData.email.split('@')[0],  // Use provided username or derive from email
          email: formData.email,
          password: formData.password,
          role: 'analyst'  // All new registrations are analysts
        });

        // Check if registration was successful
        if (response.data.access_token) {
          // If registration returns a token directly, use it
          onLogin(response.data.access_token);
        } else {
          // Otherwise, try to log in after registration
          const loginResponse = await authAPI.login({
            username: formData.email,  // Use email for login
            password: formData.password
          });

          if (loginResponse.data.access_token) {
            onLogin(loginResponse.data.access_token);
          }
        }
      }
    } catch (err) {
      console.error('Auth error:', err); // Debug logging
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || (isLogin ? 'Login failed' : 'Registration failed');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[var(--content-bg)] p-4">
      <div className="bg-[var(--card-bg)] w-full max-w-md p-8 rounded-2xl shadow-sm border border-[var(--card-border)]">
        {/* Logo Area */}
        <div className="text-center mb-8">
          <div className="mx-auto flex items-center justify-center w-12 h-12 rounded-full bg-[var(--primary-main)]/10 mb-4">
            <Brain className="h-6 w-6 text-[var(--primary-main)]" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--neutral-900)]">VisSpec</h1>
          <p className="mt-2 text-sm text-[var(--neutral-500)]">
            {isLogin ? 'Welcome back to VisSpec' : 'Join VisSpec Today'}
          </p>
        </div>

        {/* Segmented Control */}
        <div className="flex bg-[var(--surface-bg)] p-1 rounded-lg flex mb-6">
          <button
            type="button"
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              isLogin
                ? 'bg-[var(--card-bg)] text-[var(--primary-main)] shadow-sm'
                : 'text-[var(--neutral-500)] hover:text-[var(--primary-main)]'
            }`}
            onClick={() => setIsLogin(true)}
            aria-selected={isLogin}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              !isLogin
                ? 'bg-[var(--card-bg)] text-[var(--primary-main)] shadow-sm'
                : 'text-[var(--neutral-500)] hover:text-[var(--primary-main)]'
            }`}
            onClick={() => setIsLogin(false)}
            aria-selected={!isLogin}
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form className="space-y-5" onSubmit={handleSubmit}>
          {(error || usernameError) && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm" role="alert">
              {error && <span className="block">{typeof error === 'string' ? error : error.detail || 'An error occurred'}</span>}
              {usernameError && <span className="block">{usernameError}</span>}
            </div>
          )}

          {isLogin ? (
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[var(--neutral-700)] mb-1">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className={`w-full px-4 py-3 rounded-lg border ${
                  emailError ? 'border-[var(--error-main)] bg-[var(--error-light)]' : 'border-[var(--card-border)] bg-[var(--surface-bg)]'
                } focus:ring-2 focus:ring-[var(--primary-main)] focus:bg-[var(--card-bg)] outline-none transition-all`}
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleInputChange}
                aria-invalid={!!emailError}
                aria-describedby={emailError ? "email-error" : undefined}
              />
              {emailError && (
                <p id="email-error" className="mt-1 text-sm text-rose-600">
                  {emailError}
                </p>
              )}
            </div>
          ) : (
            <>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-[var(--neutral-700)] mb-1">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required={!isLogin}
                  className={`w-full px-4 py-3 rounded-lg border ${
                    emailError ? 'border-[var(--error-main)] bg-[var(--error-light)]' : 'border-[var(--card-border)] bg-[var(--surface-bg)]'
                  } focus:ring-2 focus:ring-[var(--primary-main)] focus:bg-[var(--card-bg)] outline-none transition-all`}
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                  aria-invalid={!!emailError}
                  aria-describedby={emailError ? "email-error" : undefined}
                />
                {emailError && (
                  <p id="email-error" className="mt-1 text-sm text-rose-600">
                    {emailError}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="username" className="block text-sm font-medium text-[var(--neutral-700)] mb-1">
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required={!isLogin}
                  className={`w-full px-4 py-3 rounded-lg border ${
                    usernameError ? 'border-[var(--error-main)] bg-[var(--error-light)]' : 'border-[var(--card-border)] bg-[var(--surface-bg)]'
                  } focus:ring-2 focus:ring-[var(--primary-main)] focus:bg-[var(--card-bg)] outline-none transition-all`}
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={handleInputChange}
                  aria-invalid={!!usernameError}
                  aria-describedby={usernameError ? "username-error" : undefined}
                />
                {usernameError && (
                  <p id="username-error" className="mt-1 text-sm text-rose-600">
                    {usernameError}
                  </p>
                )}
              </div>

            </>
          )}

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-[var(--neutral-700)] mb-1">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              required
              className={`w-full px-4 py-3 rounded-lg border ${
                passwordError ? 'border-[var(--error-main)] bg-[var(--error-light)]' : 'border-[var(--card-border)] bg-[var(--surface-bg)]'
              } focus:ring-2 focus:ring-[var(--primary-main)] focus:bg-[var(--card-bg)] outline-none transition-all`}
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleInputChange}
              aria-invalid={!!passwordError}
              aria-describedby={passwordError ? "password-error" : undefined}
            />
            {passwordError && (
              <p id="password-error" className="mt-1 text-sm text-rose-600">
                {passwordError}
              </p>
            )}
          </div>

          {!isLogin && (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--neutral-700)] mb-1">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required={!isLogin}
                className={`w-full px-4 py-3 rounded-lg border ${
                  formData.password !== formData.confirmPassword && formData.confirmPassword
                    ? 'border-[var(--error-main)] bg-[var(--error-light)]' : 'border-[var(--card-border)] bg-[var(--surface-bg)]'
                } focus:ring-2 focus:ring-[var(--primary-main)] focus:bg-[var(--card-bg)] outline-none transition-all`}
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
              />
              {formData.password !== formData.confirmPassword && formData.confirmPassword && (
                <p className="mt-1 text-sm text-rose-600">
                  Passwords do not match
                </p>
              )}
            </div>
          )}


          <div>
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-3 rounded-lg text-white font-medium transition-all ${
                isLoading
                  ? 'bg-[var(--btn-primary-bg)]/50 cursor-not-allowed'
                  : 'bg-[var(--btn-primary-bg)] hover:bg-[var(--btn-primary-hover)]'
              }`}
            >
              {isLoading
                ? (isLogin ? 'Signing in...' : 'Creating account...')
                : (isLogin ? 'Sign in' : 'Create Account')}
            </button>
          </div>

          {isLogin && (
            <div className="text-right text-sm mt-2">
              <button
                onClick={() => navigate('/forgot-password')}
                className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] font-medium"
              >
                Forgot Password?
              </button>
            </div>
          )}
        </form>

        {isLogin && (
          <div className="pt-6 border-t border-[var(--card-border)] mt-6">
            <div className="text-center text-sm text-[var(--neutral-500)]">
              <p>Don't have an account? <button
                onClick={() => setIsLogin(false)}
                className="text-[var(--primary-main)] hover:text-[var(--primary-hover)] font-medium"
              >
                Register here
              </button></p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;