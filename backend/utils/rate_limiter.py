"""
Rate limiter for account lockout protection.
Implements: 5 failed attempts → 15-minute lockout (BR-04).
"""
import time
from threading import Lock
from typing import Dict, Optional, Tuple
from core.config import settings


class RateLimiter:
    """In-memory rate limiter for login attempts."""

    def __init__(
        self,
        max_attempts: int = settings.MAX_LOGIN_ATTEMPTS,
        lockout_seconds: int = settings.LOCKOUT_DURATION_MINUTES * 60,
    ):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._attempts: Dict[str, list] = {}
        self._lock = Lock()

    def record_attempt(self, identifier: str) -> None:
        """Record a failed login attempt."""
        with self._lock:
            now = time.time()
            if identifier not in self._attempts:
                self._attempts[identifier] = []
            self._attempts[identifier].append(now)
            # Keep only recent attempts within lockout window
            cutoff = now - self.lockout_seconds
            self._attempts[identifier] = [t for t in self._attempts[identifier] if t > cutoff]

    def is_locked(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if an identifier is locked out.
        Returns (is_locked, seconds_remaining).
        """
        with self._lock:
            attempts = self._attempts.get(identifier, [])
            if len(attempts) >= self.max_attempts:
                elapsed = time.time() - attempts[0]
                remaining = int(self.lockout_seconds - elapsed)
                if remaining > 0:
                    return True, remaining
                # Lockout expired, reset
                self._attempts[identifier] = []
                return False, 0
            return False, 0

    def reset(self, identifier: str) -> None:
        """Reset attempt counter on successful login."""
        with self._lock:
            self._attempts.pop(identifier, None)

    def get_attempts(self, identifier: str) -> int:
        """Get current attempt count."""
        with self._lock:
            return len(self._attempts.get(identifier, []))


# Global rate limiter instance
login_rate_limiter = RateLimiter()
