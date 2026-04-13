// Utility functions for authentication

// Key for storing login attempts in localStorage
const LOGIN_ATTEMPTS_KEY = 'login_attempts';
const LOCKOUT_TIME_KEY = 'lockout_time';

// Maximum number of allowed failed attempts
const MAX_FAILED_ATTEMPTS = 5;

// Lockout duration in minutes
const LOCKOUT_DURATION = 15;

// Session timeout duration in minutes
const SESSION_TIMEOUT = 60;

/**
 * Record a failed login attempt
 */
export const recordFailedAttempt = () => {
  const attemptsData = JSON.parse(localStorage.getItem(LOGIN_ATTEMPTS_KEY) || '{}');
  const now = new Date().getTime();
  
  // Clean up old attempts (older than lockout duration)
  const cleanedAttempts = {};
  for (const [timestamp, count] of Object.entries(attemptsData)) {
    if (now - parseInt(timestamp) < LOCKOUT_DURATION * 60 * 1000) {
      cleanedAttempts[timestamp] = count;
    }
  }
  
  // Add new attempt
  const currentTimestamp = new Date().getTime();
  cleanedAttempts[currentTimestamp] = (cleanedAttempts[currentTimestamp] || 0) + 1;
  
  localStorage.setItem(LOGIN_ATTEMPTS_KEY, JSON.stringify(cleanedAttempts));

  // Check if user should be locked out
  const recentAttempts = Object.values(cleanedAttempts).reduce((sum, count) => sum + count, 0);
  if (recentAttempts >= MAX_FAILED_ATTEMPTS) {
    localStorage.setItem(LOCKOUT_TIME_KEY, currentTimestamp.toString());
    return true; // User should be locked out
  }

  return false; // User should not be locked out
};

/**
 * Check if user is currently locked out
 */
export const isLockedOut = () => {
  const lockoutTime = localStorage.getItem(LOCKOUT_TIME_KEY);
  if (!lockoutTime) {
    return false;
  }

  const now = new Date().getTime();
  const lockoutTimeMs = parseInt(lockoutTime);

  if (now - lockoutTimeMs >= LOCKOUT_DURATION * 60 * 1000) {
    // Lockout period has expired, remove the lockout
    localStorage.removeItem(LOCKOUT_TIME_KEY);
    return false;
  }

  return true;
};

/**
 * Get remaining lockout time in minutes
 */
export const getRemainingLockoutTime = () => {
  const lockoutTime = localStorage.getItem(LOCKOUT_TIME_KEY);
  if (!lockoutTime) {
    return 0;
  }

  const now = new Date().getTime();
  const lockoutTimeMs = parseInt(lockoutTime);
  const elapsed = now - lockoutTimeMs;
  const remainingMs = LOCKOUT_DURATION * 60 * 1000 - elapsed;

  return Math.max(0, Math.ceil(remainingMs / (60 * 1000)));
};

/**
 * Get number of failed attempts in the last lockout period
 */
export const getFailedAttempts = () => {
  const attemptsData = JSON.parse(localStorage.getItem(LOGIN_ATTEMPTS_KEY) || '{}');
  const now = new Date().getTime();

  let totalAttempts = 0;
  for (const [timestamp, count] of Object.entries(attemptsData)) {
    if (now - parseInt(timestamp) < LOCKOUT_DURATION * 60 * 1000) {
      totalAttempts += count;
    } else {
      // Clean up old attempts
      delete attemptsData[timestamp];
    }
  }

  localStorage.setItem(LOGIN_ATTEMPTS_KEY, JSON.stringify(attemptsData));
  return totalAttempts;
};

/**
 * Clear all login attempt records (on successful login)
 */
export const clearLoginAttempts = () => {
  localStorage.removeItem(LOGIN_ATTEMPTS_KEY);
  localStorage.removeItem(LOCKOUT_TIME_KEY);
};

/**
 * Check if session has expired
 */
export const isSessionExpired = (lastActivityTime) => {
  if (!lastActivityTime) {
    return true;
  }
  
  const now = new Date().getTime();
  const lastActivity = new Date(lastActivityTime).getTime();
  
  return now - lastActivity > SESSION_TIMEOUT * 60 * 1000;
};

/**
 * Update last activity time
 */
export const updateLastActivity = () => {
  localStorage.setItem('last_activity', new Date().toISOString());
};