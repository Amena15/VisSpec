import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Auth from '../src/pages/Auth';
import { AuthProvider } from '../src/contexts/AuthContext';

// Mock the API calls
jest.mock('../src/services/api', () => ({
  login: jest.fn(),
  register: jest.fn(),
  forgotPassword: jest.fn(),
  resetPassword: jest.fn(),
}));

import { login, register, forgotPassword, resetPassword } from '../src/services/api';

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Authentication Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('Login Form', () => {
    test('renders login form correctly', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    });

    test('shows validation errors for empty fields', async () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const loginButton = screen.getByRole('button', { name: /login/i });
      
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    test('shows validation error for invalid email', async () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email/i)).toBeInTheDocument();
      });
    });

    test('successful login redirects to dashboard', async () => {
      const mockUser = testUtils.createMockUser();
      const mockToken = 'test-jwt-token';
      
      login.mockResolvedValue({
        access_token: mockToken,
        token_type: 'bearer',
        user: mockUser
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(login).toHaveBeenCalledWith('test@example.com', 'password123');
        expect(localStorage.setItem).toHaveBeenCalledWith('token', mockToken);
        expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
      });
    });

    test('shows error message on login failure', async () => {
      login.mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } }
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    test('disables login button during submission', async () => {
      login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      expect(loginButton).toBeDisabled();
      expect(screen.getByText(/logging in/i)).toBeInTheDocument();
    });
  });

  describe('Registration Form', () => {
    test('switches to registration form when clicking register link', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const registerLink = screen.getByText(/sign up/i);
      fireEvent.click(registerLink);

      expect(screen.getByText('Register')).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
    });

    test('shows validation error for password mismatch', async () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Switch to registration form
      fireEvent.click(screen.getByText(/sign up/i));

      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const registerButton = screen.getByRole('button', { name: /register/i });

      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'different' } });
      fireEvent.click(registerButton);

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });
    });

    test('successful registration', async () => {
      const mockUser = testUtils.createMockUser();
      const mockToken = 'test-jwt-token';
      
      register.mockResolvedValue({
        access_token: mockToken,
        token_type: 'bearer',
        user: mockUser
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Switch to registration form
      fireEvent.click(screen.getByText(/sign up/i));

      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const registerButton = screen.getByRole('button', { name: /register/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(registerButton);

      await waitFor(() => {
        expect(register).toHaveBeenCalledWith({
          username: 'testuser',
          email: 'test@example.com',
          password: 'password123',
          role: 'analyst'
        });
        expect(localStorage.setItem).toHaveBeenCalledWith('token', mockToken);
        expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
      });
    });

    test('shows error message on registration failure', async () => {
      register.mockRejectedValue({
        response: { data: { detail: 'Email already registered' } }
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Switch to registration form
      fireEvent.click(screen.getByText(/sign up/i));

      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const registerButton = screen.getByRole('button', { name: /register/i });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(emailInput, { target: { value: 'existing@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(registerButton);

      await waitFor(() => {
        expect(screen.getByText(/email already registered/i)).toBeInTheDocument();
      });
    });
  });

  describe('Forgot Password Form', () => {
    test('switches to forgot password form when clicking forgot password link', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const forgotPasswordLink = screen.getByText(/forgot password/i);
      fireEvent.click(forgotPasswordLink);

      expect(screen.getByText('Reset Password')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });

    test('successful forgot password request', async () => {
      forgotPassword.mockResolvedValue({
        message: 'If email exists, reset instructions sent'
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Switch to forgot password form
      fireEvent.click(screen.getByText(/forgot password/i));

      const emailInput = screen.getByLabelText(/email/i);
      const sendButton = screen.getByRole('button', { name: /send reset link/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(forgotPassword).toHaveBeenCalledWith('test@example.com');
        expect(screen.getByText(/reset instructions sent/i)).toBeInTheDocument();
      });
    });

    test('shows error message on forgot password failure', async () => {
      forgotPassword.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Switch to forgot password form
      fireEvent.click(screen.getByText(/forgot password/i));

      const emailInput = screen.getByLabelText(/email/i);
      const sendButton = screen.getByRole('button', { name: /send reset link/i });

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Navigation', () => {
    test('can switch between login and registration forms', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Initially on login form
      expect(screen.getByText('Login')).toBeInTheDocument();

      // Switch to registration
      fireEvent.click(screen.getByText(/sign up/i));
      expect(screen.getByText('Register')).toBeInTheDocument();

      // Switch back to login
      fireEvent.click(screen.getByText(/already have an account/i));
      expect(screen.getByText('Login')).toBeInTheDocument();
    });

    test('can switch from login to forgot password and back', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Initially on login form
      expect(screen.getByText('Login')).toBeInTheDocument();

      // Switch to forgot password
      fireEvent.click(screen.getByText(/forgot password/i));
      expect(screen.getByText('Reset Password')).toBeInTheDocument();

      // Switch back to login
      fireEvent.click(screen.getByText(/back to login/i));
      expect(screen.getByText('Login')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Check form elements have proper labels
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      
      // Check buttons have proper roles
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
      
      // Check links are accessible
      expect(screen.getByRole('link', { name: /forgot password/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /sign up/i })).toBeInTheDocument();
    });

    test('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      // Tab navigation
      emailInput.focus();
      expect(document.activeElement).toBe(emailInput);

      fireEvent.tab();
      expect(document.activeElement).toBe(passwordInput);

      fireEvent.tab();
      expect(document.activeElement).toBe(loginButton);

      // Enter key submission
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.keyDown(loginButton, { key: 'Enter', code: 'Enter' });

      expect(login).toHaveBeenCalled();
    });
  });

  describe('Responsive Design', () => {
    test('renders correctly on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Should still render all elements
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    test('renders correctly on desktop viewport', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1920,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 1080,
      });

      render(
        <TestWrapper>
          <Auth />
        </TestWrapper>
      );

      // Should still render all elements
      expect(screen.getByText('Login')).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });
  });
});
