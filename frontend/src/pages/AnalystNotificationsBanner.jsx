import React, { useEffect, useState, useCallback } from 'react';
import { Bell, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { toast } from 'sonner';

import { apiClient } from '../services/api';

const typeToUI = (type) => {
  if (type === 'review_approved') {
    return {
      bg: 'bg-[var(--success-light)]',
      text: 'text-[var(--success-hover)]',
      Icon: CheckCircle,
      label: 'Approved',
    };
  }
  if (type === 'review_changes_requested') {
    return {
      bg: 'bg-[var(--warning-light)]',
      text: 'text-[var(--warning-hover)]',
      Icon: AlertTriangle,
      label: 'Changes Requested',
    };
  }

  return {
    bg: 'bg-[var(--surface-bg)]',
    text: 'text-[var(--text-secondary)]',
    Icon: Bell,
    label: 'Update',
  };
};

const AnalystNotificationsBanner = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadUnread = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/api/notifications/unread');
      setNotifications(res.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUnread();
  }, [loadUnread]);

  const markAllRead = async () => {
    if (!notifications.length) return;
    const ids = notifications.map((n) => n.id);

    try {
      await apiClient.post('/api/notifications/mark-read', { notification_ids: ids });
      toast.success('Notifications marked as read');
      setNotifications([]);
    } catch (err) {
      console.error(err);
      toast.error('Failed to mark notifications as read');
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--surface-bg)] p-4 text-sm text-[var(--text-secondary)]">
        Loading notifications...
      </div>
    );
  }

  if (!notifications.length) return null;

  // Show the most recent one as the banner; keep others accessible via toast text.
  const latest = notifications[0];
  const ui = typeToUI(latest.type);

  return (
    <div className={`rounded-xl border border-[var(--card-border)] ${ui.bg} p-4`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${ui.text}`}>
            <ui.Icon className="h-5 w-5" />
          </div>
          <div>
            <div className={`text-sm font-semibold ${ui.text}`}>{ui.label}</div>
            <div className="text-xs text-[var(--text-secondary)] mt-1">
              {latest.content}
            </div>
            <div className="text-[10px] text-[var(--text-secondary)] mt-1">{latest.created_at}</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={markAllRead}
            className="px-3 py-1.5 bg-[var(--surface-bg)] border border-[var(--card-border)] text-[var(--text-secondary)] rounded-lg text-xs hover:bg-[var(--card-border)]"
          >
            Mark read
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnalystNotificationsBanner;

