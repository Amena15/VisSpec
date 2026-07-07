/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional Blue-Gray Palette
        'primary': '#2563EB',       // Professional Blue - Main brand
        'primary-hover': '#1D4ED8', // Hover states
        'primary-dark': '#1E40AF',  // Pressed states, darker borders
        'primary-50': '#EFF6FF',    // Very light backgrounds

        'accent': '#7C3AED',        // Purple - Accent only
        'accent-light': '#8B5CF6',
        'accent-dark': '#6D28D9',

        // Neutral Colors
        'neutral-50': '#F9FAFB',    // Lightest (main background)
        'neutral-100': '#F3F4F6',   // Card backgrounds
        'neutral-200': '#E5E7EB',   // Borders, dividers
        'neutral-300': '#D1D5DB',   // Subtle borders
        'neutral-400': '#9CA3AF',   // Placeholder text
        'neutral-500': '#6B7280',   // Icons, disabled
        'neutral-600': '#4B5563',   // Secondary text
        'neutral-700': '#374151',   // Body text
        'neutral-800': '#1F2937',   // Headings
        'neutral-900': '#111827',   // Darkest (primary headings)

        // Semantic Colors
        'success': '#10B981',       // Emerald Green - Success
        'success-light': '#D1FAE5', // Success backgrounds
        'success-hover': '#059669', // Hover states for success

        'warning': '#F59E0B',       // Amber Yellow - Attention
        'warning-light': '#FEF3C7', // Warning backgrounds
        'warning-hover': '#D97706', // Hover states for warning

        'error': '#EF4444',         // Red - Critical
        'error-light': '#FEE2E2',   // Error backgrounds
        'error-hover': '#DC2626',   // Hover states for error

        'info': '#3B82F6',          // Blue - General info
        'info-light': '#DBEAFE',    // Info backgrounds
        'info-dark': '#2563EB',     // Info borders/text

        // Interface Elements
        'background': '#F9FAFB',    // Main content area
        'card': '#FFFFFF',          // Card/panel background
        'card-border': '#E5E7EB',   // Card borders
        'surface': '#F3F4F6',       // Surface backgrounds
        'text-primary': '#111827',  // Primary text
        'text-secondary': '#6B7280', // Secondary text
        'theme': '#E5E7EB',         // Theme borders
        'sidebar': '#FFFFFF',       // Sidebar background
        'sidebar-border': '#E5E7EB', // Sidebar border
        'header': '#FFFFFF',        // Header background
        'header-border': '#E5E7EB', // Header border

        // Button Colors
        'btn-primary-bg': '#2563EB',      // Main CTA buttons
        'btn-primary-hover': '#1D4ED8',   // Hover state for primary
        'btn-primary-text': '#FFFFFF',
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}

