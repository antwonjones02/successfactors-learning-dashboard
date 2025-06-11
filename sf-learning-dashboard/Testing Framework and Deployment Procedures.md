# Testing Framework and Deployment Procedures

This document outlines the testing framework and deployment procedures for the SuccessFactors Learning Dashboard application.

## Testing Framework

### 1. Frontend Testing

#### Unit Tests

```typescript
// src/components/dashboard/MetricCard.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MetricCard } from './MetricCard';

describe('MetricCard Component', () => {
  test('renders title and value correctly', () => {
    render(<MetricCard title="Total Users" value={500} icon="users" />);
    
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
  });
  
  test('renders trend indicator when provided', () => {
    render(<MetricCard title="Completion Rate" value="85%" icon="check-circle" trend="up" />);
    
    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByTestId('trend-indicator')).toHaveClass('trend-up');
  });
});

// src/hooks/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react-hooks';
import { useAuth, AuthProvider } from './useAuth';
import { login, logout } from '../lib/api';

// Mock the API functions
jest.mock('../lib/api', () => ({
  login: jest.fn(),
  logout: jest.fn(),
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.clearAllMocks();
  });
  
  test('should return isAuthenticated=false when no token exists', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
  
  test('should set isAuthenticated=true after successful login', async () => {
    // Mock successful login
    (login as jest.Mock).mockResolvedValue({ username: 'testuser', role: 'admin' });
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });
    
    await act(async () => {
      await result.current.login('testuser', 'password');
    });
    
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ username: 'testuser', role: 'admin' });
    expect(login).toHaveBeenCalledWith('testuser', 'password');
  });
  
  test('should set isAuthenticated=false after logout', async () => {
    // Setup authenticated state
    localStorage.setItem('token', 'fake-token');
    
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });
    
    // Verify initial authenticated state
    expect(result.current.isAuthenticated).toBe(true);
    
    // Perform logout
    await act(async () => {
      await result.current.logout();
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(logout).toHaveBeenCalled();
    expect(localStorage.getItem('token')).toBeNull();
  });
});

// src/lib/api.test.ts
import axios from 'axios';
import api, { login, logout, fetchDashboardSummary } from './api';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    post: jest.fn(),
    get: jest.fn(),
  })),
}));

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });
  
  test('login should store token in localStorage', async () => {
    const mockResponse = { data: { token: 'fake-token', user: { username: 'testuser' } } };
    (axios.create().post as jest.Mock).mockResolvedValue(mockResponse);
    
    const result = await login('testuser', 'password');
    
    expect(axios.create().post).toHaveBeenCalledWith('/auth/login', { username: 'testuser', password: 'password' });
    expect(localStorage.getItem('token')).toBe('fake-token');
    expect(result).toEqual({ username: 'testuser' });
  });
  
  test('logout should remove token from localStorage', async () => {
    localStorage.setItem('token', 'fake-token');
    
    await logout();
    
    expect(axios.create().post).toHaveBeenCalledWith('/auth/logout');
    expect(localStorage.getItem('token')).toBeNull();
  });
  
  test('fetchDashboardSummary should call the correct endpoint', async () => {
    const mockResponse = { data: { totalUsers: 500 } };
    (axios.create().get as jest.Mock).mockResolvedValue(mockResponse);
    
    const result = await fetchDashboardSummary();
    
    expect(axios.create().get).toHaveBeenCalledWith('/dashboard/summary');
    expect(result).toEqual({ totalUsers: 500 });
  });
});
```

#### Integration Tests

```typescript
// src/components/dashboard/DashboardOverview.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardOverview } from './DashboardOverview';
import { fetchDashboardSummary } from '../../lib/api';

// Mock the API function
jest.mock('../../lib/api', () => ({
  fetchDashboardSummary: jest.fn(),
}));

describe('DashboardOverview Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('displays loading state initially', () => {
    // Mock API call that never resolves
    (fetchDashboardSummary as jest.Mock).mockImplementation(() => new Promise(() => {}));
    
    render(<DashboardOverview />);
    
    expect(screen.getByText(/loading dashboard data/i)).toBeInTheDocument();
  });
  
  test('displays dashboard data when loaded', async () => {
    // Mock successful API response
    const mockData = {
      totalUsers: 500,
      totalCourses: 100,
      completionRate: 85,
      complianceRate: 90,
      recentActivities: [
        { id: '1', user: 'User 1', action: 'completed', item: 'Course 1', timestamp: '2025-05-20T10:00:00Z' }
      ],
      completionTrend: [
        { month: 'Jan', completions: 50 },
        { month: 'Feb', completions: 75 }
      ]
    };
    (fetchDashboardSummary as jest.Mock).mockResolvedValue(mockData);
    
    render(<DashboardOverview />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('500')).toBeInTheDocument();
    });
    
    // Check that metrics are displayed
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('90%')).toBeInTheDocument();
    
    // Check that recent activities are displayed
    expect(screen.getByText('User 1')).toBeInTheDocument();
    expect(screen.getByText('Course 1')).toBeInTheDocument();
  });
  
  test('displays error message when API call fails', async () => {
    // Mock failed API call
    (fetchDashboardSummary as jest.Mock).mockRejectedValue(new Error('API error'));
    
    render(<DashboardOverview />);
    
    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
    });
  });
});

// src/components/auth/LoginForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from './LoginForm';
import { AuthProvider } from '../../hooks/useAuth';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock useAuth hook
const mockLogin = jest.fn();
jest.mock('../../hooks/useAuth', () => ({
  ...jest.requireActual('../../hooks/useAuth'),
  useAuth: () => ({
    login: mockLogin,
  }),
}));

describe('LoginForm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders login form correctly', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });
  
  test('handles successful login', async () => {
    // Mock successful login
    mockLogin.mockResolvedValue({});
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      </BrowserRouter>
    );
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password' } });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check that login was called with correct credentials
    expect(mockLogin).toHaveBeenCalledWith('testuser', 'password');
    
    // Wait for navigation
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
  
  test('displays error message on login failure', async () => {
    // Mock failed login
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LoginForm />
        </AuthProvider>
      </BrowserRouter>
    );
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong-password' } });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    // Check that error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    });
    
    // Check that navigation was not called
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
```

#### End-to-End Tests

```typescript
// cypress/e2e/login.cy.ts
describe('Login Flow', () => {
  beforeEach(() => {
    // Intercept API calls
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        token: 'fake-token',
        user: { username: 'testuser', role: 'admin' }
      }
    }).as('loginRequest');
    
    cy.visit('/login');
  });
  
  it('should login successfully with valid credentials', () => {
    // Fill in login form
    cy.get('input[id="username"]').type('testuser');
    cy.get('input[id="password"]').type('password');
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Wait for API call
    cy.wait('@loginRequest').its('request.body').should('deep.equal', {
      username: 'testuser',
      password: 'password'
    });
    
    // Verify redirect to dashboard
    cy.url().should('include', '/dashboard');
    
    // Verify dashboard is loaded
    cy.get('h1').should('contain', 'Learning Dashboard');
  });
  
  it('should show error message with invalid credentials', () => {
    // Override the intercept for this test
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 401,
      body: { message: 'Invalid credentials' }
    }).as('failedLoginRequest');
    
    // Fill in login form
    cy.get('input[id="username"]').type('testuser');
    cy.get('input[id="password"]').type('wrong-password');
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Wait for API call
    cy.wait('@failedLoginRequest');
    
    // Verify error message
    cy.get('.text-red-500').should('contain', 'Invalid username or password');
    
    // Verify we're still on login page
    cy.url().should('include', '/login');
  });
});

// cypress/e2e/dashboard.cy.ts
describe('Dashboard', () => {
  beforeEach(() => {
    // Mock login
    cy.window().then((win) => {
      win.localStorage.setItem('token', 'fake-token');
    });
    
    // Intercept API calls
    cy.intercept('GET', '/api/dashboard/summary', {
      fixture: 'dashboardSummary.json'
    }).as('dashboardSummary');
    
    cy.visit('/dashboard');
  });
  
  it('should display dashboard metrics', () => {
    // Wait for API call
    cy.wait('@dashboardSummary');
    
    // Verify metrics are displayed
    cy.get('.metric-card').should('have.length', 4);
    cy.contains('Total Users').should('exist');
    cy.contains('Total Courses').should('exist');
    cy.contains('Completion Rate').should('exist');
    cy.contains('Compliance Rate').should('exist');
  });
  
  it('should display completion trends chart', () => {
    // Wait for API call
    cy.wait('@dashboardSummary');
    
    // Verify chart is displayed
    cy.get('.completion-chart').should('exist');
  });
  
  it('should display recent activities', () => {
    // Wait for API call
    cy.wait('@dashboardSummary');
    
    // Verify activities are displayed
    cy.get('.activity-list').should('exist');
    cy.get('.activity-item').should('have.length.at.least', 1);
  });
});

// cypress/e2e/reports.cy.ts
describe('Report Builder', () => {
  beforeEach(() => {
    // Mock login
    cy.window().then((win) => {
      win.localStorage.setItem('token', 'fake-token');
    });
    
    // Intercept API calls
    cy.intercept('POST', '/api/reports/generate', {
      fixture: 'reportData.json'
    }).as('generateReport');
    
    cy.visit('/reports');
  });
  
  it('should allow configuring and generating a report', () => {
    // Enter report name
    cy.get('input[id="report-name"]').type('Test Report');
    
    // Select fields
    cy.get('input[id="user_name"]').should('be.checked');
    cy.get('input[id="score"]').should('not.be.checked');
    cy.get('input[id="score"]').check();
    
    // Add filter
    cy.contains('button', 'Add Filter').click();
    cy.get('select').eq(3).select('completion_status');
    cy.get('select').eq(4).select('equals');
    cy.get('input').eq(4).type('Completed');
    
    // Select format
    cy.get('select[id="report-format"]').select('excel');
    
    // Generate report
    cy.contains('button', 'Generate Report').click();
    
    // Wait for API call
    cy.wait('@generateReport').its('request.body').should('deep.include', {
      name: 'Test Report',
      format: 'excel'
    });
    
    // Verify report preview is displayed
    cy.get('.report-preview').should('exist');
  });
});
```

### 2. Backend Testing

#### Unit Tests

```python
# tests/unit/test_auth.py
import unittest
import jwt
from datetime import datetime, timedelta
from flask import Flask
from src.routes.auth import auth_bp, token_required, SECRET_KEY

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(auth_bp, url_prefix='/api/auth')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        self.app_context.pop()
    
    def test_login_success(self):
        response = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'admin')
        self.assertEqual(data['user']['role'], 'admin')
        
        # Verify token is valid
        token = data['token']
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(decoded['username'], 'admin')
        self.assertEqual(decoded['role'], 'admin')
    
    def test_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrong-password'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Invalid credentials')
    
    def test_login_missing_fields(self):
        response = self.client.post('/api/auth/login', json={
            'username': 'admin'
        })
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Could not verify')
    
    def test_token_required_decorator(self):
        # Create a test route with the decorator
        @self.app.route('/api/test-auth')
        @token_required
        def test_route(current_user):
            return {'username': current_user}
        
        # Test with valid token
        token = jwt.encode({
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY)
        
        response = self.client.get('/api/test-auth', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['username'], 'admin')
        
        # Test with missing token
        response = self.client.get('/api/test-auth')
        self.assertEqual(response.status_code, 401)
        
        # Test with invalid token
        response = self.client.get('/api/test-auth', headers={
            'Authorization': 'Bearer invalid-token'
        })
        self.assertEqual(response.status_code, 401)
        
        # Test with expired token
        expired_token = jwt.encode({
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.utcnow() - timedelta(hours=1)
        }, SECRET_KEY)
        
        response = self.client.get('/api/test-auth', headers={
            'Authorization': f'Bearer {expired_token}'
        })
        self.assertEqual(response.status_code, 401)

# tests/unit/test_dashboard.py
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.dashboard import dashboard_bp
from src.routes.auth import token_required

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        
        # Mock the token_required decorator
        def mock_token_required(f):
            def decorated(*args, **kwargs):
                return f('test_user', *args, **kwargs)
            return decorated
        
        with patch('src.routes.dashboard.token_required', mock_token_required):
            self.app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        self.app_context.pop()
    
    def test_get_dashboard_summary(self):
        response = self.client.get('/api/dashboard/summary')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Check that required fields are present
        self.assertIn('totalUsers', data)
        self.assertIn('totalCourses', data)
        self.assertIn('completionRate', data)
        self.assertIn('complianceRate', data)
        self.assertIn('recentActivities', data)
        self.assertIn('completionTrend', data)
        
        # Check that recent activities have the expected structure
        self.assertIsInstance(data['recentActivities'], list)
        if data['recentActivities']:
            activity = data['recentActivities'][0]
            self.assertIn('id', activity)
            self.assertIn('user', activity)
            self.assertIn('action', activity)
            self.assertIn('item', activity)
            self.assertIn('timestamp', activity)
        
        # Check that completion trend has the expected structure
        self.assertIsInstance(data['completionTrend'], list)
        if data['completionTrend']:
            trend = data['completionTrend'][0]
            self.assertIn('month', trend)
            self.assertIn('completions', trend)
    
    def test_get_dashboard_trends(self):
        response = self.client.get('/api/dashboard/trends')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Check that required fields are present
        self.assertIn('labels', data)
        self.assertIn('datasets', data)
        
        # Check that datasets have the expected structure
        self.assertIsInstance(data['datasets'], list)
        self.assertEqual(len(data['datasets']), 2)  # Should have two datasets
        
        dataset = data['datasets'][0]
        self.assertIn('label', dataset)
        self.assertIn('data', dataset)
        self.assertEqual(len(dataset['data']), len(data['labels']))
    
    def test_get_compliance_metrics(self):
        response = self.client.get('/api/dashboard/compliance')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Check that required fields are present
        self.assertIn('overallCompliance', data)
        self.assertIn('categories', data)
        
        # Check that categories have the expected structure
        self.assertIsInstance(data['categories'], list)
        if data['categories']:
            category = data['categories'][0]
            self.assertIn('category', category)
            self.assertIn('required', category)
            self.assertIn('completed', category)
            self.assertIn('dueDate', category)
```

#### Integration Tests

```python
# tests/integration/test_api_integration.py
import unittest
import json
import jwt
from datetime import datetime, timedelta
from flask import Flask
from src.main import app as flask_app
from src.routes.auth import SECRET_KEY

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.app = flask_app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a valid token for authenticated requests
        self.token = jwt.encode({
            'username': 'admin',
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY)
        
        self.auth_headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_health_check(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_login_flow(self):
        # Test login
        login_response = self.client.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        self.assertEqual(login_response.status_code, 200)
        login_data = json.loads(login_response.data)
        self.assertIn('token', login_data)
        
        # Use the token to access a protected endpoint
        token = login_data['token']
        dashboard_response = self.client.get('/api/dashboard/summary', headers={
            'Authorization': f'Bearer {token}'
        })
        
        self.assertEqual(dashboard_response.status_code, 200)
    
    def test_dashboard_endpoints(self):
        # Test dashboard summary
        summary_response = self.client.get('/api/dashboard/summary', headers=self.auth_headers)
        self.assertEqual(summary_response.status_code, 200)
        
        # Test dashboard trends
        trends_response = self.client.get('/api/dashboard/trends', headers=self.auth_headers)
        self.assertEqual(trends_response.status_code, 200)
        
        # Test compliance metrics
        compliance_response = self.client.get('/api/dashboard/compliance', headers=self.auth_headers)
        self.assertEqual(compliance_response.status_code, 200)
    
    def test_learning_endpoints(self):
        # Test learning completions
        completions_response = self.client.get('/api/learning/completions', headers=self.auth_headers)
        self.assertEqual(completions_response.status_code, 200)
        
        # Test learning assignments
        assignments_response = self.client.get('/api/learning/assignments', headers=self.auth_headers)
        self.assertEqual(assignments_response.status_code, 200)
        
        # Test learning items
        items_response = self.client.get('/api/learning/items', headers=self.auth_headers)
        self.assertEqual(items_response.status_code, 200)
        
        # Test learning analytics
        analytics_response = self.client.get('/api/learning/analytics', headers=self.auth_headers)
        self.assertEqual(analytics_response.status_code, 200)
    
    def test_users_endpoints(self):
        # Test users list
        users_response = self.client.get('/api/users', headers=self.auth_headers)
        self.assertEqual(users_response.status_code, 200)
        
        # Test user details
        user_response = self.client.get('/api/users/user-1', headers=self.auth_headers)
        self.assertEqual(user_response.status_code, 200)
        
        # Test user learning
        learning_response = self.client.get('/api/users/user-1/learning', headers=self.auth_headers)
        self.assertEqual(learning_response.status_code, 200)
        
        # Test user assignments
        assignments_response = self.client.get('/api/users/user-1/assignments', headers=self.auth_headers)
        self.assertEqual(assignments_response.status_code, 200)
        
        # Test employee profile
        profile_response = self.client.get('/api/users/user-1/profile', headers=self.auth_headers)
        self.assertEqual(profile_response.status_code, 200)
    
    def test_unauthorized_access(self):
        # Test accessing protected endpoint without token
        response = self.client.get('/api/dashboard/summary')
        self.assertEqual(response.status_code, 401)
        
        # Test with invalid token
        response = self.client.get('/api/dashboard/summary', headers={
            'Authorization': 'Bearer invalid-token'
        })
        self.assertEqual(response.status_code, 401)
```

### 3. Test Configuration

#### Jest Configuration for Frontend

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/__mocks__/fileMock.js'
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  }
};

// src/setupTests.ts
import '@testing-library/jest-dom';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});
```

#### Pytest Configuration for Backend

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=src --cov-report=term --cov-report=html

# conftest.py
import pytest
import jwt
from datetime import datetime, timedelta
from src.main import app as flask_app
from src.routes.auth import SECRET_KEY

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_token():
    token = jwt.encode({
        'username': 'admin',
        'role': 'admin',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, SECRET_KEY)
    return token

@pytest.fixture
def auth_headers(auth_token):
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
```

### 4. Test Scripts

```json
// package.json (frontend)
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "cypress run",
    "test:e2e:open": "cypress open"
  }
}
```

```bash
# backend/run_tests.sh
#!/bin/bash
set -e

# Activate virtual environment
source venv/bin/activate

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration

# Run coverage report
echo "Generating coverage report..."
python -m pytest --cov=src --cov-report=html

echo "All tests completed successfully!"
```

## Deployment Procedures

### 1. Frontend Deployment

#### Build Script

```bash
#!/bin/bash
# frontend/build.sh
set -e

echo "Building frontend application..."

# Install dependencies
echo "Installing dependencies..."
cd /home/ubuntu/learning_dashboard/frontend/sf-learning-dashboard
pnpm install

# Build for production
echo "Building for production..."
pnpm run build

echo "Frontend build completed successfully!"
```

#### Environment Configuration

```typescript
// .env.production
REACT_APP_API_URL=https://api.sf-learning-dashboard.example.com/api
REACT_APP_VERSION=1.0.0
```

#### Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name sf-learning-dashboard.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name sf-learning-dashboard.example.com;
    
    ssl_certificate /etc/letsencrypt/live/sf-learning-dashboard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sf-learning-dashboard.example.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self' https://api.sf-learning-dashboard.example.com;" always;
    
    # Root directory
    root /var/www/sf-learning-dashboard;
    index index.html;
    
    # Static files
    location /static {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### Deployment Script

```bash
#!/bin/bash
# frontend/deploy.sh
set -e

echo "Deploying frontend application..."

# Build the application
./build.sh

# Create deployment directory if it doesn't exist
sudo mkdir -p /var/www/sf-learning-dashboard

# Copy build files to deployment directory
echo "Copying build files to deployment directory..."
sudo cp -r /home/ubuntu/learning_dashboard/frontend/sf-learning-dashboard/build/* /var/www/sf-learning-dashboard/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/sf-learning-dashboard
sudo chmod -R 755 /var/www/sf-learning-dashboard

# Copy Nginx configuration
echo "Updating Nginx configuration..."
sudo cp nginx.conf /etc/nginx/sites-available/sf-learning-dashboard
sudo ln -sf /etc/nginx/sites-available/sf-learning-dashboard /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

echo "Frontend deployment completed successfully!"
```

### 2. Backend Deployment

#### Environment Configuration

```bash
# backend/.env.production
DB_USERNAME=sf_learning_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sf_learning_db
JWT_SECRET_KEY=your_secure_jwt_secret_key
```

#### Gunicorn Configuration

```python
# gunicorn_config.py
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 120
keepalive = 5
errorlog = "/var/log/sf-learning-api/error.log"
accesslog = "/var/log/sf-learning-api/access.log"
loglevel = "info"
```

#### Systemd Service

```ini
# sf-learning-api.service
[Unit]
Description=SuccessFactors Learning Dashboard API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/sf-learning-api
Environment="PATH=/var/www/sf-learning-api/venv/bin"
EnvironmentFile=/var/www/sf-learning-api/.env.production
ExecStart=/var/www/sf-learning-api/venv/bin/gunicorn --config gunicorn_config.py src.main:app
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
```

#### Deployment Script

```bash
#!/bin/bash
# backend/deploy.sh
set -e

echo "Deploying backend application..."

# Create deployment directory if it doesn't exist
sudo mkdir -p /var/www/sf-learning-api
sudo mkdir -p /var/log/sf-learning-api

# Copy application files
echo "Copying application files..."
sudo cp -r /home/ubuntu/learning_dashboard/backend/sf-learning-api/* /var/www/sf-learning-api/

# Create virtual environment if it doesn't exist
if [ ! -d "/var/www/sf-learning-api/venv" ]; then
    echo "Creating virtual environment..."
    cd /var/www/sf-learning-api
    sudo python3 -m venv venv
fi

# Install dependencies
echo "Installing dependencies..."
cd /var/www/sf-learning-api
sudo venv/bin/pip install -r requirements.txt
sudo venv/bin/pip install gunicorn gevent

# Copy environment file
echo "Copying environment file..."
sudo cp /home/ubuntu/learning_dashboard/backend/.env.production /var/www/sf-learning-api/

# Copy Gunicorn configuration
echo "Copying Gunicorn configuration..."
sudo cp /home/ubuntu/learning_dashboard/backend/gunicorn_config.py /var/www/sf-learning-api/

# Copy systemd service file
echo "Setting up systemd service..."
sudo cp /home/ubuntu/learning_dashboard/backend/sf-learning-api.service /etc/systemd/system/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/sf-learning-api
sudo chown -R www-data:www-data /var/log/sf-learning-api
sudo chmod -R 755 /var/www/sf-learning-api

# Reload systemd and start service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable sf-learning-api
sudo systemctl restart sf-learning-api

echo "Backend deployment completed successfully!"
```

### 3. Database Setup

```sql
-- database_setup.sql
CREATE DATABASE IF NOT EXISTS sf_learning_db;

CREATE USER IF NOT EXISTS 'sf_learning_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON sf_learning_db.* TO 'sf_learning_user'@'localhost';
FLUSH PRIVILEGES;

USE sf_learning_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    manager_id VARCHAR(255),
    department VARCHAR(255),
    division VARCHAR(255),
    location VARCHAR(255),
    job_title VARCHAR(255),
    hire_date DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);

-- Learning items table
CREATE TABLE IF NOT EXISTS learning_items (
    item_id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    duration INTEGER,
    credit_hours DECIMAL(10,2),
    cpe_hours DECIMAL(10,2),
    created_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Learning completions table
CREATE TABLE IF NOT EXISTS learning_completions (
    completion_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    completion_date TIMESTAMP,
    expiration_date TIMESTAMP NULL,
    score DECIMAL(5,2),
    credit_hours_earned DECIMAL(10,2),
    cpe_hours_earned DECIMAL(10,2),
    comments TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES learning_items(item_id)
);

-- Learning assignments table
CREATE TABLE IF NOT EXISTS learning_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    assigned_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP NULL,
    assigned_by VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES learning_items(item_id),
    FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);

-- Create indexes
CREATE INDEX idx_users_manager_id ON users(manager_id);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_learning_items_type ON learning_items(type);
CREATE INDEX idx_learning_completions_user_id ON learning_completions(user_id);
CREATE INDEX idx_learning_completions_item_id ON learning_completions(item_id);
CREATE INDEX idx_learning_completions_status ON learning_completions(status);
CREATE INDEX idx_learning_assignments_user_id ON learning_assignments(user_id);
CREATE INDEX idx_learning_assignments_item_id ON learning_assignments(item_id);
CREATE INDEX idx_learning_assignments_status ON learning_assignments(status);
```

```bash
#!/bin/bash
# setup_database.sh
set -e

echo "Setting up database..."

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "MySQL is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y mysql-server
fi

# Start MySQL service if not running
if ! systemctl is-active --quiet mysql; then
    echo "Starting MySQL service..."
    sudo systemctl start mysql
fi

# Run SQL script
echo "Creating database and tables..."
sudo mysql < database_setup.sql

echo "Database setup completed successfully!"
```

### 4. CI/CD Pipeline

#### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Install pnpm
      run: npm install -g pnpm
    
    - name: Install dependencies
      run: |
        cd frontend/sf-learning-dashboard
        pnpm install
    
    - name: Run tests
      run: |
        cd frontend/sf-learning-dashboard
        pnpm test
    
    - name: Build
      if: github.event_name == 'push'
      run: |
        cd frontend/sf-learning-dashboard
        pnpm build
    
    - name: Upload build artifacts
      if: github.event_name == 'push'
      uses: actions/upload-artifact@v2
      with:
        name: frontend-build
        path: frontend/sf-learning-dashboard/build
  
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
          MYSQL_DATABASE: sf_learning_db
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend/sf-learning-api
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend/sf-learning-api
        source venv/bin/activate
        python -m pytest
    
    - name: Upload test artifacts
      uses: actions/upload-artifact@v2
      with:
        name: backend-test-results
        path: backend/sf-learning-api/htmlcov
  
  deploy:
    needs: [test-frontend, test-backend]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Download frontend build
      uses: actions/download-artifact@v2
      with:
        name: frontend-build
        path: frontend-build
    
    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.5.3
      with:
        ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
    
    - name: Deploy to production
      run: |
        # Add server to known hosts
        ssh-keyscan -H ${{ secrets.SERVER_IP }} >> ~/.ssh/known_hosts
        
        # Create deployment directory on server
        ssh ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }} "mkdir -p /tmp/deployment"
        
        # Copy files to server
        scp -r frontend-build/* ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }}:/tmp/deployment/
        scp -r backend/sf-learning-api/* ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }}:/tmp/deployment/
        scp deployment/deploy.sh ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }}:/tmp/deployment/
        
        # Run deployment script
        ssh ${{ secrets.SSH_USER }}@${{ secrets.SERVER_IP }} "cd /tmp/deployment && chmod +x deploy.sh && ./deploy.sh"
```

#### Master Deployment Script

```bash
#!/bin/bash
# deployment/deploy.sh
set -e

echo "Starting deployment process..."

# Deploy frontend
echo "Deploying frontend..."
cd /tmp/deployment
sudo mkdir -p /var/www/sf-learning-dashboard
sudo cp -r frontend-build/* /var/www/sf-learning-dashboard/
sudo chown -R www-data:www-data /var/www/sf-learning-dashboard
sudo chmod -R 755 /var/www/sf-learning-dashboard

# Deploy backend
echo "Deploying backend..."
sudo mkdir -p /var/www/sf-learning-api
sudo cp -r backend/* /var/www/sf-learning-api/

# Create virtual environment if it doesn't exist
if [ ! -d "/var/www/sf-learning-api/venv" ]; then
    echo "Creating virtual environment..."
    cd /var/www/sf-learning-api
    sudo python3 -m venv venv
fi

# Install dependencies
echo "Installing backend dependencies..."
cd /var/www/sf-learning-api
sudo venv/bin/pip install -r requirements.txt
sudo venv/bin/pip install gunicorn gevent

# Set proper permissions
sudo chown -R www-data:www-data /var/www/sf-learning-api
sudo chmod -R 755 /var/www/sf-learning-api

# Restart services
echo "Restarting services..."
sudo systemctl restart nginx
sudo systemctl restart sf-learning-api

echo "Deployment completed successfully!"
```

### 5. Rollback Procedure

```bash
#!/bin/bash
# rollback.sh
set -e

# Check if backup version is provided
if [ -z "$1" ]; then
    echo "Error: Backup version not provided"
    echo "Usage: ./rollback.sh <backup_version>"
    exit 1
fi

BACKUP_VERSION=$1
BACKUP_DIR="/var/backups/sf-learning-dashboard/$BACKUP_VERSION"

# Check if backup exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup version $BACKUP_VERSION not found"
    echo "Available backups:"
    ls -l /var/backups/sf-learning-dashboard/
    exit 1
fi

echo "Rolling back to version $BACKUP_VERSION..."

# Rollback frontend
echo "Rolling back frontend..."
sudo rm -rf /var/www/sf-learning-dashboard/*
sudo cp -r $BACKUP_DIR/frontend/* /var/www/sf-learning-dashboard/
sudo chown -R www-data:www-data /var/www/sf-learning-dashboard
sudo chmod -R 755 /var/www/sf-learning-dashboard

# Rollback backend
echo "Rolling back backend..."
sudo systemctl stop sf-learning-api
sudo rm -rf /var/www/sf-learning-api/*
sudo cp -r $BACKUP_DIR/backend/* /var/www/sf-learning-api/
sudo chown -R www-data:www-data /var/www/sf-learning-api
sudo chmod -R 755 /var/www/sf-learning-api

# Restart services
echo "Restarting services..."
sudo systemctl restart nginx
sudo systemctl start sf-learning-api

echo "Rollback to version $BACKUP_VERSION completed successfully!"
```

### 6. Backup Procedure

```bash
#!/bin/bash
# backup.sh
set -e

# Create backup version based on timestamp
BACKUP_VERSION=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/$BACKUP_VERSION"

echo "Creating backup version $BACKUP_VERSION..."

# Create backup directory
sudo mkdir -p $BACKUP_DIR/frontend
sudo mkdir -p $BACKUP_DIR/backend
sudo mkdir -p $BACKUP_DIR/database

# Backup frontend
echo "Backing up frontend..."
sudo cp -r /var/www/sf-learning-dashboard/* $BACKUP_DIR/frontend/

# Backup backend
echo "Backing up backend..."
sudo cp -r /var/www/sf-learning-api/* $BACKUP_DIR/backend/

# Backup database
echo "Backing up database..."
sudo mysqldump -u root sf_learning_db > $BACKUP_DIR/database/sf_learning_db.sql

# Set proper permissions
sudo chown -R $(whoami):$(whoami) $BACKUP_DIR
sudo chmod -R 755 $BACKUP_DIR

echo "Backup version $BACKUP_VERSION created successfully!"
```

## Security Considerations

### 1. Authentication and Authorization

- JWT tokens with proper expiration
- Role-based access control
- Secure password storage with hashing
- Token refresh mechanism
- HTTPS for all communications

### 2. Data Protection

- Input validation on both client and server
- Parameterized SQL queries to prevent injection
- Content Security Policy headers
- CORS configuration
- XSS protection

### 3. Infrastructure Security

- Firewall configuration
- Regular security updates
- Principle of least privilege
- Secure environment variable handling
- Monitoring and alerting for security events

### 4. Compliance

- GDPR considerations for user data
- Audit logging for sensitive operations
- Data retention policies
- Privacy policy implementation

## Monitoring and Maintenance

### 1. Application Monitoring

- Error logging and alerting
- Performance metrics collection
- User activity tracking
- API usage monitoring

### 2. Infrastructure Monitoring

- Server resource utilization
- Database performance
- Network traffic analysis
- Service health checks

### 3. Maintenance Procedures

- Regular database backups
- Log rotation
- Dependency updates
- Security patches

This comprehensive testing framework and deployment procedures ensure that the SuccessFactors Learning Dashboard application is thoroughly tested, securely deployed, and properly maintained. The testing covers all aspects of the application, from unit tests for individual components to integration tests for API endpoints and end-to-end tests for user flows. The deployment procedures provide a reliable and repeatable process for deploying the application to production, with proper security measures and rollback capabilities.
