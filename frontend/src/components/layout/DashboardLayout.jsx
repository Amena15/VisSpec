import React from 'react';

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen w-screen bg-[var(--content-bg)] text-[var(--text-primary)] transition-colors duration-300">
      {children}
    </div>
  );
}

