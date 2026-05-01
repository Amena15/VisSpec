import React, { useState } from 'react';
import { toast } from 'sonner';
import { authAPI } from '../services/api';

const PasswordChangeForm = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Validate password strength according to backend requirements
  const validatePassword = (password) => {
    if (password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;  // At least one uppercase
    if (!/[a-z]/.test(password)) return false;  // At least one lowercase
    if (!/\d/.test(password)) return false;     // At least one digit
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) return false;  // At least one special character
    return true;
  };

  const handleSubmitPassword = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validate passwords match
      if (newPassword !== confirmPassword) {
        toast.error('New passwords do not match');
        setLoading(false);
        return;
      }

      // Validate password strength
      if (!validatePassword(newPassword)) {
        toast.error('Password must be 8+ chars with uppercase, lowercase, number & special char');
        setLoading(false);
        return;
      }

      // Call backend API to change password
      const response = await authAPI.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });

      // Show success message
      toast.success('Password changed successfully');

      // Reset form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || 'An error occurred while changing password';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmitPassword} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Current Password</label>
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          placeholder="Enter current password"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">New Password</label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          placeholder="Enter new password"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Confirm New Password</label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          placeholder="Confirm new password"
        />
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg hover:bg-[var(--primary-hover)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Changing...' : 'Change Password'}
        </button>
      </div>
    </form>
  );
};

export default PasswordChangeForm;
