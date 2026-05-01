import React, { useState, useEffect } from 'react';
import { Sun, Moon, Bell, Monitor, Globe, Lock, User } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '../services/api';
import PasswordChangeForm from '../components/PasswordChangeForm';

const Settings = () => {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);
  const [language, setLanguage] = useState('en');
  const [timezone, setTimezone] = useState('UTC');
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Load user settings from backend on component mount
  useEffect(() => {
    const fetchUserSettings = async () => {
      try {
        // Get token from localStorage
        const token = localStorage.getItem('token');
        if (!token) {
          toast.error('Not authenticated');
          return;
        }

        const response = await fetch('http://localhost:8000/api/users/settings', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const settings = await response.json();
          setEmailNotifications(settings.email_notifications || true);
          setPushNotifications(settings.push_notifications || false);
          setLanguage(settings.language || 'en');
          setTimezone(settings.timezone || 'UTC');
        } else {
          // If settings don't exist, use defaults
          setEmailNotifications(true);
          setPushNotifications(false);
          setLanguage('en');
          setTimezone('UTC');
        }
      } catch (error) {
        console.error('Error fetching user settings:', error);
        toast.error('Failed to load settings');

        // Use defaults on error
        setEmailNotifications(true);
        setPushNotifications(false);
        setLanguage('en');
        setTimezone('UTC');
      }
    };

    const fetchUserProfile = async () => {
      try {
        setProfileLoading(true);
        const response = await authAPI.getProfile();
        setUserProfile(response.data); // axios returns data in response.data
      } catch (error) {
        console.error('Error fetching user profile:', error);
        toast.error('Failed to load user profile');
      } finally {
        setProfileLoading(false);
      }
    };

    fetchUserSettings();
    fetchUserProfile();
  }, []);

  const handleSaveSettings = async () => {
    setLoading(true);

    try {
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        toast.error('Not authenticated');
        setLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/api/users/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email_notifications: emailNotifications,
          push_notifications: pushNotifications,
          language,
          timezone
        })
      });

      if (response.ok) {
        toast.success('Settings saved successfully');
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('An error occurred while saving settings');
    } finally {
      setLoading(false);
    }
  };

  const handleResetSettings = () => {
    // Reset to default values
    setEmailNotifications(defaultSettings.emailNotifications);
    setPushNotifications(defaultSettings.pushNotifications);
    setLanguage(defaultSettings.language);
    setTimezone(defaultSettings.timezone);

    // Show success message
    toast.success('Settings reset to default values successfully');
  };

  // Reusable Section Card Component
  const SectionCard = ({ title, description, children }) => (
    <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-[var(--card-border)]">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
        <p className="text-sm text-[var(--text-secondary)] mt-1">{description}</p>
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      <div className="py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">Account Settings</h1>
            <p className="text-[var(--text-secondary)] mt-2">Manage your account settings and preferences</p>
          </div>

          <div className="space-y-6">
            {/* Account Details */}
            <SectionCard
              title="Account Details"
              description="View your account information"
            >
              {profileLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary-main)]"></div>
                </div>
              ) : userProfile ? (
                <div className="space-y-6">
                  {/* User Profile Header */}
                  <div className="flex items-center space-x-4 pb-6 border-b border-[var(--card-border)]">
                    <div className="flex-shrink-0">
                      <div className="w-16 h-16 bg-[var(--primary-main)] rounded-full flex items-center justify-center">
                        <User className="w-8 h-8 text-white" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-[var(--text-primary)]">{userProfile.username}</h3>
                      <p className="text-sm text-[var(--text-secondary)]">{userProfile.email}</p>
                      <p className="text-sm text-[var(--text-secondary)] capitalize">{userProfile.role}</p>
                    </div>
                  </div>

                  {/* Detailed Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">User ID</label>
                      <p className="text-sm text-[var(--text-primary)] font-mono">{userProfile.user_id}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Username</label>
                      <p className="text-sm text-[var(--text-primary)]">{userProfile.username}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Email Address</label>
                      <p className="text-sm text-[var(--text-primary)]">{userProfile.email}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Role</label>
                      <p className="text-sm text-[var(--text-primary)] capitalize">{userProfile.role}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Account Status</label>
                      <p className="text-sm">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          userProfile.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {userProfile.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Member Since</label>
                      <p className="text-sm text-[var(--text-primary)]">
                        {new Date(userProfile.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-[var(--text-secondary)]">Unable to load account details</p>
                </div>
              )}
            </SectionCard>

            {/* Notification Preferences */}
            <SectionCard
              title="Notification Preferences"
              description="Configure how you receive notifications"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Bell className="h-5 w-5 text-[var(--text-secondary)] mr-3" />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">Email Notifications</p>
                      <p className="text-sm text-[var(--text-secondary)]">Receive notifications via email</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setEmailNotifications(!emailNotifications)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)] focus:ring-offset-2 ${
                      emailNotifications ? 'bg-[var(--primary-main)]' : 'bg-[var(--surface-bg)]'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        emailNotifications ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Monitor className="h-5 w-5 text-[var(--text-secondary)] mr-3" />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">Push Notifications</p>
                      <p className="text-sm text-[var(--text-secondary)]">Receive notifications on this device</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setPushNotifications(!pushNotifications)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)] focus:ring-offset-2 ${
                      pushNotifications ? 'bg-[var(--primary-main)]' : 'bg-[var(--surface-bg)]'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        pushNotifications ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </SectionCard>


            {/* Security (Change Password) */}
            <SectionCard
              title="Security"
              description="Change your password and manage account security"
            >
              <PasswordChangeForm />
            </SectionCard>
          </div>
        </div>
      </div>

      {/* Save and Reset Settings Buttons */}
      <div className="mt-8 flex justify-end space-x-4">
        <button
          onClick={handleResetSettings}
          disabled={loading}
          className="bg-[var(--surface-bg)] text-[var(--text-primary)] px-6 py-3 rounded-lg hover:bg-[var(--card-border)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Reset to Default
        </button>
        <button
          onClick={handleSaveSettings}
          disabled={loading}
          className="bg-[var(--primary-main)] text-white px-6 py-3 rounded-lg hover:bg-[var(--primary-hover)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary-main)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default Settings;