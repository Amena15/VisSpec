// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();

// Mock window.location
delete window.location;
window.location = { href: '' };

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup test environment
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Reset localStorage
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
  
  // Reset fetch
  fetch.mockClear();
});

// Global test utilities
global.testUtils = {
  // Create a mock user
  createMockUser: (overrides = {}) => ({
    user_id: 'test-user-id',
    username: 'testuser',
    email: 'test@example.com',
    role: 'analyst',
    created_at: '2024-01-01T00:00:00Z',
    ...overrides
  }),
  
  // Create a mock project
  createMockProject: (overrides = {}) => ({
    project_id: 'test-project-id',
    name: 'Test Project',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    document_count: 0,
    ...overrides
  }),
  
  // Create a mock document
  createMockDocument: (overrides = {}) => ({
    doc_id: 'test-doc-id',
    project_id: 'test-project-id',
    filename: 'test.txt',
    file_extension: 'txt',
    file_size_bytes: 100,
    status: 'Ready for Analysis',
    word_count: 10,
    upload_date: '2024-01-01T00:00:00Z',
    ...overrides
  }),
  
  // Create a mock requirement
  createMockRequirement: (overrides = {}) => ({
    req_id: 'test-req-id',
    doc_id: 'test-doc-id',
    project_id: 'test-project-id',
    req_identifier: 'REQ-001',
    original_text: 'The system shall allow users to login.',
    current_text: 'The system shall allow users to login.',
    word_count: 7,
    validation_status: 'pending',
    category: 'functional',
    ...overrides
  }),
  
  // Mock API responses
  mockApiResponse: (data, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  }),
  
  // Mock API error
  mockApiError: (message, status = 400) => ({
    ok: false,
    status,
    json: async () => ({ detail: message }),
    text: async () => message,
  }),
  
  // Wait for async operations
  waitFor: (ms = 0) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Create a file object for testing
  createMockFile: (name = 'test.txt', content = 'test content', type = 'text/plain') => {
    const file = new File([content], name, { type });
    Object.defineProperty(file, 'size', { value: content.length });
    return file;
  }
};
