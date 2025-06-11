# Frontend Implementation for SuccessFactors Learning Dashboard

This document outlines the implementation of key frontend components for the SuccessFactors Learning dashboard application.

## Core Components

### 1. Authentication Component

```tsx
// src/components/auth/LoginForm.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { useAuth } from '../../hooks/useAuth';

export const LoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Sign In</CardTitle>
        <CardDescription>
          Enter your credentials to access the Learning Dashboard
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
          </div>
        </form>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={() => navigate('/forgot-password')}>
          Forgot Password
        </Button>
        <Button type="submit" disabled={isLoading} onClick={handleSubmit}>
          {isLoading ? 'Signing in...' : 'Sign In'}
        </Button>
      </CardFooter>
    </Card>
  );
};
```

### 2. Dashboard Layout Component

```tsx
// src/components/layout/DashboardLayout.tsx
import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar open={sidebarOpen} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header toggleSidebar={toggleSidebar} />
        <main className="flex-1 overflow-y-auto p-4">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
```

### 3. Dashboard Overview Component

```tsx
// src/components/dashboard/DashboardOverview.tsx
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { MetricCard } from './MetricCard';
import { CompletionRateChart } from './CompletionRateChart';
import { RecentActivities } from './RecentActivities';
import { fetchDashboardSummary } from '../../lib/api';

interface DashboardSummary {
  totalUsers: number;
  totalCourses: number;
  completionRate: number;
  complianceRate: number;
  recentActivities: Array<{
    id: string;
    user: string;
    action: string;
    item: string;
    timestamp: string;
  }>;
  completionTrend: Array<{
    month: string;
    completions: number;
  }>;
}

export const DashboardOverview: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setIsLoading(true);
        const data = await fetchDashboardSummary();
        setSummary(data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading dashboard data...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-8">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Learning Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Total Users" 
          value={summary?.totalUsers || 0} 
          icon="users" 
        />
        <MetricCard 
          title="Total Courses" 
          value={summary?.totalCourses || 0} 
          icon="book-open" 
        />
        <MetricCard 
          title="Completion Rate" 
          value={`${summary?.completionRate || 0}%`} 
          icon="check-circle" 
          trend="up" 
        />
        <MetricCard 
          title="Compliance Rate" 
          value={`${summary?.complianceRate || 0}%`} 
          icon="shield" 
          trend={summary?.complianceRate > 90 ? "up" : "down"} 
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Completion Trends</CardTitle>
            <CardDescription>Monthly learning completion trends</CardDescription>
          </CardHeader>
          <CardContent>
            <CompletionRateChart data={summary?.completionTrend || []} />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Recent Activities</CardTitle>
            <CardDescription>Latest learning activities</CardDescription>
          </CardHeader>
          <CardContent>
            <RecentActivities activities={summary?.recentActivities || []} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
```

### 4. Learning Completion Analytics Component

```tsx
// src/components/analytics/LearningCompletionAnalytics.tsx
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { CompletionByDepartmentChart } from './CompletionByDepartmentChart';
import { CompletionTrendChart } from './CompletionTrendChart';
import { ComplianceTable } from './ComplianceTable';
import { fetchLearningAnalytics } from '../../lib/api';

interface LearningAnalytics {
  byDepartment: Array<{
    department: string;
    completionRate: number;
    totalUsers: number;
  }>;
  trends: Array<{
    period: string;
    completions: number;
  }>;
  compliance: Array<{
    course: string;
    required: number;
    completed: number;
    compliance: number;
    dueDate: string;
  }>;
}

export const LearningCompletionAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<LearningAnalytics | null>(null);
  const [timeframe, setTimeframe] = useState('month');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadAnalyticsData = async () => {
      try {
        setIsLoading(true);
        const data = await fetchLearningAnalytics(timeframe);
        setAnalytics(data);
      } catch (err) {
        setError('Failed to load analytics data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalyticsData();
  }, [timeframe]);

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading analytics data...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-8">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Learning Completion Analytics</h1>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Timeframe:</span>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select timeframe" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="week">Last Week</SelectItem>
              <SelectItem value="month">Last Month</SelectItem>
              <SelectItem value="quarter">Last Quarter</SelectItem>
              <SelectItem value="year">Last Year</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <Tabs defaultValue="department">
        <TabsList>
          <TabsTrigger value="department">By Department</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
        </TabsList>
        
        <TabsContent value="department">
          <Card>
            <CardHeader>
              <CardTitle>Completion Rates by Department</CardTitle>
              <CardDescription>
                Learning completion rates across different departments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CompletionByDepartmentChart data={analytics?.byDepartment || []} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Completion Trends</CardTitle>
              <CardDescription>
                Learning completion trends over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CompletionTrendChart data={analytics?.trends || []} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="compliance">
          <Card>
            <CardHeader>
              <CardTitle>Compliance Tracking</CardTitle>
              <CardDescription>
                Mandatory training compliance status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ComplianceTable data={analytics?.compliance || []} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
```

### 5. Employee Learning Profile Component

```tsx
// src/components/profiles/EmployeeLearningProfile.tsx
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { LearningHistoryTable } from './LearningHistoryTable';
import { AssignedCoursesTable } from './AssignedCoursesTable';
import { SkillGapChart } from './SkillGapChart';
import { fetchEmployeeProfile } from '../../lib/api';

interface EmployeeProfile {
  id: string;
  name: string;
  email: string;
  department: string;
  manager: string;
  completedCourses: number;
  assignedCourses: number;
  completionRate: number;
  learningHistory: Array<{
    id: string;
    course: string;
    completionDate: string;
    score: number;
    status: string;
  }>;
  assignedLearning: Array<{
    id: string;
    course: string;
    dueDate: string;
    status: string;
    progress: number;
  }>;
  skills: Array<{
    name: string;
    current: number;
    target: number;
  }>;
}

export const EmployeeLearningProfile: React.FC = () => {
  const { employeeId } = useParams<{ employeeId: string }>();
  const [profile, setProfile] = useState<EmployeeProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadProfileData = async () => {
      if (!employeeId) return;
      
      try {
        setIsLoading(true);
        const data = await fetchEmployeeProfile(employeeId);
        setProfile(data);
      } catch (err) {
        setError('Failed to load employee profile');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfileData();
  }, [employeeId]);

  if (isLoading) {
    return <div className="flex justify-center p-8">Loading employee profile...</div>;
  }

  if (error || !profile) {
    return <div className="text-red-500 p-8">{error || 'Employee not found'}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold">{profile.name}'s Learning Profile</h1>
        <div className="flex items-center space-x-2 mt-2 md:mt-0">
          <Badge variant="outline">{profile.department}</Badge>
          <Badge variant="secondary">Manager: {profile.manager}</Badge>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Completed Courses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{profile.completedCourses}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Assigned Courses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{profile.assignedCourses}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{profile.completionRate}%</div>
            <Progress value={profile.completionRate} className="mt-2" />
          </CardContent>
        </Card>
      </div>
      
      <Tabs defaultValue="history">
        <TabsList>
          <TabsTrigger value="history">Learning History</TabsTrigger>
          <TabsTrigger value="assigned">Assigned Learning</TabsTrigger>
          <TabsTrigger value="skills">Skill Gap Analysis</TabsTrigger>
        </TabsList>
        
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle>Learning History</CardTitle>
              <CardDescription>
                Completed learning activities and certifications
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LearningHistoryTable data={profile.learningHistory} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="assigned">
          <Card>
            <CardHeader>
              <CardTitle>Assigned Learning</CardTitle>
              <CardDescription>
                Current and upcoming learning assignments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AssignedCoursesTable data={profile.assignedLearning} />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="skills">
          <Card>
            <CardHeader>
              <CardTitle>Skill Gap Analysis</CardTitle>
              <CardDescription>
                Current skills vs. target proficiency levels
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SkillGapChart data={profile.skills} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
```

### 6. Custom Report Builder Component

```tsx
// src/components/reports/ReportBuilder.tsx
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { ReportPreview } from './ReportPreview';
import { generateReport, saveReportTemplate } from '../../lib/api';

interface ReportField {
  id: string;
  name: string;
  category: string;
  selected: boolean;
}

interface ReportFilter {
  field: string;
  operator: string;
  value: string;
}

export const ReportBuilder: React.FC = () => {
  const [reportName, setReportName] = useState('');
  const [selectedFields, setSelectedFields] = useState<ReportField[]>([
    { id: 'user_name', name: 'User Name', category: 'User', selected: true },
    { id: 'user_email', name: 'Email', category: 'User', selected: true },
    { id: 'user_department', name: 'Department', category: 'User', selected: true },
    { id: 'course_name', name: 'Course Name', category: 'Course', selected: true },
    { id: 'completion_date', name: 'Completion Date', category: 'Completion', selected: true },
    { id: 'completion_status', name: 'Status', category: 'Completion', selected: true },
    { id: 'score', name: 'Score', category: 'Completion', selected: false },
    { id: 'credit_hours', name: 'Credit Hours', category: 'Course', selected: false },
    { id: 'manager_name', name: 'Manager', category: 'User', selected: false },
    { id: 'assignment_date', name: 'Assignment Date', category: 'Assignment', selected: false },
    { id: 'due_date', name: 'Due Date', category: 'Assignment', selected: false },
  ]);
  
  const [filters, setFilters] = useState<ReportFilter[]>([
    { field: 'completion_status', operator: 'equals', value: 'Completed' }
  ]);
  
  const [reportFormat, setReportFormat] = useState('excel');
  const [reportData, setReportData] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const toggleFieldSelection = (fieldId: string) => {
    setSelectedFields(fields => 
      fields.map(field => 
        field.id === fieldId ? { ...field, selected: !field.selected } : field
      )
    );
  };

  const addFilter = () => {
    setFilters([...filters, { field: 'completion_status', operator: 'equals', value: '' }]);
  };

  const updateFilter = (index: number, key: keyof ReportFilter, value: string) => {
    const updatedFilters = [...filters];
    updatedFilters[index] = { ...updatedFilters[index], [key]: value };
    setFilters(updatedFilters);
  };

  const removeFilter = (index: number) => {
    setFilters(filters.filter((_, i) => i !== index));
  };

  const handleGenerateReport = async () => {
    try {
      setIsGenerating(true);
      setError('');
      
      const reportConfig = {
        name: reportName,
        fields: selectedFields.filter(f => f.selected).map(f => f.id),
        filters,
        format: reportFormat
      };
      
      const data = await generateReport(reportConfig);
      setReportData(data);
    } catch (err) {
      setError('Failed to generate report');
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!reportName) {
      setError('Please provide a report name');
      return;
    }
    
    try {
      await saveReportTemplate({
        name: reportName,
        fields: selectedFields.filter(f => f.selected).map(f => f.id),
        filters
      });
      
      alert('Report template saved successfully');
    } catch (err) {
      setError('Failed to save report template');
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Custom Report Builder</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Report Configuration</CardTitle>
              <CardDescription>Define your custom report</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="report-name">Report Name</Label>
                <Input 
                  id="report-name" 
                  value={reportName} 
                  onChange={(e) => setReportName(e.target.value)} 
                  placeholder="Enter report name"
                />
              </div>
              
              <div>
                <Label>Select Fields</Label>
                <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
                  {selectedFields.map((field) => (
                    <div key={field.id} className="flex items-center space-x-2">
                      <Checkbox 
                        id={field.id} 
                        checked={field.selected}
                        onCheckedChange={() => toggleFieldSelection(field.id)}
                      />
                      <Label htmlFor={field.id} className="text-sm">
                        {field.name} <span className="text-gray-500">({field.category})</span>
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <div className="flex justify-between items-center">
                  <Label>Filters</Label>
                  <Button variant="outline" size="sm" onClick={addFilter}>
                    Add Filter
                  </Button>
                </div>
                <div className="mt-2 space-y-3">
                  {filters.map((filter, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center">
                      <div className="col-span-4">
                        <Select 
                          value={filter.field} 
                          onValueChange={(value) => updateFilter(index, 'field', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Field" />
                          </SelectTrigger>
                          <SelectContent>
                            {selectedFields.map((field) => (
                              <SelectItem key={field.id} value={field.id}>
                                {field.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-3">
                        <Select 
                          value={filter.operator} 
                          onValueChange={(value) => updateFilter(index, 'operator', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Operator" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="equals">Equals</SelectItem>
                            <SelectItem value="contains">Contains</SelectItem>
                            <SelectItem value="greater_than">Greater Than</SelectItem>
                            <SelectItem value="less_than">Less Than</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-4">
                        <Input 
                          value={filter.value} 
                          onChange={(e) => updateFilter(index, 'value', e.target.value)} 
                          placeholder="Value"
                        />
                      </div>
                      <div className="col-span-1">
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          onClick={() => removeFilter(index)}
                          className="h-8 w-8"
                        >
                          ✕
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <Label htmlFor="report-format">Report Format</Label>
                <Select value={reportFormat} onValueChange={setReportFormat}>
                  <SelectTrigger id="report-format">
                    <SelectValue placeholder="Select format" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="excel">Excel</SelectItem>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {error && <p className="text-sm text-red-500">{error}</p>}
              
              <div className="flex space-x-2 pt-2">
                <Button onClick={handleSaveTemplate} variant="outline">
                  Save Template
                </Button>
                <Button onClick={handleGenerateReport} disabled={isGenerating}>
                  {isGenerating ? 'Generating...' : 'Generate Report'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Report Preview</CardTitle>
              <CardDescription>
                Preview of your custom report
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ReportPreview data={reportData} isLoading={isGenerating} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
```

## Backend API Implementation

### 1. Main Application Entry Point

```python
# src/main.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import routes
from src.routes.auth import auth_bp
from src.routes.dashboard import dashboard_bp
from src.routes.learning import learning_bp
from src.routes.users import users_bp
from src.routes.organization import organization_bp
from src.routes.reports import reports_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(learning_bp, url_prefix='/api/learning')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(organization_bp, url_prefix='/api/organization')
app.register_blueprint(reports_bp, url_prefix='/api/reports')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 2. Authentication Routes

```python
# src/routes/auth.py
from flask import Blueprint, request, jsonify
import jwt
import datetime
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Secret key for JWT
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'development_secret_key')

# Mock user database (replace with actual database in production)
USERS = {
    'admin': {
        'password': 'admin123',
        'role': 'admin'
    },
    'user': {
        'password': 'user123',
        'role': 'user'
    }
}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = data['username']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401
    
    username = auth.get('username')
    password = auth.get('password')
    
    if username not in USERS or USERS[username]['password'] != password:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate token
    token = jwt.encode({
        'username': username,
        'role': USERS[username]['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY)
    
    return jsonify({
        'token': token,
        'user': {
            'username': username,
            'role': USERS[username]['role']
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    # Generate new token
    token = jwt.encode({
        'username': current_user,
        'role': USERS[current_user]['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY)
    
    return jsonify({'token': token})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # In a stateless JWT setup, the client simply discards the token
    # Server-side we could implement a token blacklist if needed
    return jsonify({'message': 'Logout successful'})
```

### 3. Dashboard Routes

```python
# src/routes/dashboard.py
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import random
from src.routes.auth import token_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
@token_required
def get_dashboard_summary(current_user):
    # Mock data - replace with actual database queries in production
    total_users = random.randint(500, 1500)
    total_courses = random.randint(100, 300)
    completion_rate = random.randint(65, 95)
    compliance_rate = random.randint(70, 98)
    
    # Generate mock recent activities
    recent_activities = []
    for i in range(10):
        activity_types = ['completed', 'started', 'assigned to']
        items = ['Introduction to Python', 'Leadership Skills', 'Compliance Training', 
                'Data Security', 'Project Management', 'Customer Service']
        
        days_ago = random.randint(0, 14)
        activity_date = datetime.now() - timedelta(days=days_ago)
        
        recent_activities.append({
            'id': f'act-{i}',
            'user': f'User {random.randint(1, 100)}',
            'action': random.choice(activity_types),
            'item': random.choice(items),
            'timestamp': activity_date.isoformat()
        })
    
    # Sort activities by timestamp (newest first)
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Generate mock completion trend data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_month = datetime.now().month
    completion_trend = []
    
    for i in range(6):
        month_index = (current_month - i - 1) % 12
        completion_trend.append({
            'month': months[month_index],
            'completions': random.randint(50, 200)
        })
    
    # Reverse to show chronological order
    completion_trend.reverse()
    
    return jsonify({
        'totalUsers': total_users,
        'totalCourses': total_courses,
        'completionRate': completion_rate,
        'complianceRate': compliance_rate,
        'recentActivities': recent_activities,
        'completionTrend': completion_trend
    })

@dashboard_bp.route('/trends', methods=['GET'])
@token_required
def get_dashboard_trends(current_user):
    # Mock data - replace with actual database queries in production
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    
    completion_data = [random.randint(50, 200) for _ in range(6)]
    enrollment_data = [random.randint(70, 250) for _ in range(6)]
    
    return jsonify({
        'labels': months,
        'datasets': [
            {
                'label': 'Completions',
                'data': completion_data
            },
            {
                'label': 'Enrollments',
                'data': enrollment_data
            }
        ]
    })

@dashboard_bp.route('/compliance', methods=['GET'])
@token_required
def get_compliance_metrics(current_user):
    # Mock data - replace with actual database queries in production
    compliance_categories = [
        'Data Security',
        'Ethics Training',
        'Safety Procedures',
        'Harassment Prevention',
        'Regulatory Compliance'
    ]
    
    compliance_data = []
    for category in compliance_categories:
        compliance_data.append({
            'category': category,
            'required': random.randint(80, 150),
            'completed': random.randint(60, 130),
            'dueDate': (datetime.now() + timedelta(days=random.randint(10, 90))).isoformat()
        })
    
    # Calculate overall compliance
    total_required = sum(item['required'] for item in compliance_data)
    total_completed = sum(item['completed'] for item in compliance_data)
    overall_compliance = round((total_completed / total_required) * 100) if total_required > 0 else 0
    
    return jsonify({
        'overallCompliance': overall_compliance,
        'categories': compliance_data
    })
```

### 4. Learning Routes

```python
# src/routes/learning.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random
from src.routes.auth import token_required

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/completions', methods=['GET'])
@token_required
def get_learning_completions(current_user):
    # Parse query parameters
    timeframe = request.args.get('timeframe', 'month')
    department = request.args.get('department')
    
    # Mock data - replace with actual database queries in production
    completions = []
    
    # Generate random completion data
    for i in range(50):
        days_ago = random.randint(0, 90)
        completion_date = datetime.now() - timedelta(days=days_ago)
        
        # Filter by timeframe if specified
        if timeframe == 'week' and days_ago > 7:
            continue
        elif timeframe == 'month' and days_ago > 30:
            continue
        elif timeframe == 'quarter' and days_ago > 90:
            continue
        
        departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
        selected_dept = random.choice(departments)
        
        # Filter by department if specified
        if department and department != selected_dept:
            continue
        
        completions.append({
            'id': f'comp-{i}',
            'userId': f'user-{random.randint(1, 100)}',
            'userName': f'User {random.randint(1, 100)}',
            'department': selected_dept,
            'courseId': f'course-{random.randint(1, 50)}',
            'courseName': f'Course {random.randint(1, 50)}',
            'completionDate': completion_date.isoformat(),
            'score': random.randint(70, 100),
            'status': 'Completed'
        })
    
    return jsonify(completions)

@learning_bp.route('/assignments', methods=['GET'])
@token_required
def get_learning_assignments(current_user):
    # Parse query parameters
    status = request.args.get('status')
    
    # Mock data - replace with actual database queries in production
    assignments = []
    
    # Generate random assignment data
    for i in range(50):
        statuses = ['Assigned', 'In Progress', 'Completed', 'Overdue']
        selected_status = random.choice(statuses)
        
        # Filter by status if specified
        if status and status != selected_status:
            continue
        
        days_ago = random.randint(0, 30)
        assignment_date = datetime.now() - timedelta(days=days_ago)
        
        days_ahead = random.randint(10, 60)
        due_date = datetime.now() + timedelta(days=days_ahead)
        
        # If status is overdue, set due date in the past
        if selected_status == 'Overdue':
            due_date = datetime.now() - timedelta(days=random.randint(1, 10))
        
        assignments.append({
            'id': f'assign-{i}',
            'userId': f'user-{random.randint(1, 100)}',
            'userName': f'User {random.randint(1, 100)}',
            'courseId': f'course-{random.randint(1, 50)}',
            'courseName': f'Course {random.randint(1, 50)}',
            'assignmentDate': assignment_date.isoformat(),
            'dueDate': due_date.isoformat(),
            'status': selected_status,
            'progress': random.randint(0, 100) if selected_status == 'In Progress' else 
                        (100 if selected_status == 'Completed' else 0)
        })
    
    return jsonify(assignments)

@learning_bp.route('/items', methods=['GET'])
@token_required
def get_learning_items(current_user):
    # Parse query parameters
    item_type = request.args.get('type')
    
    # Mock data - replace with actual database queries in production
    items = []
    
    # Generate random learning item data
    for i in range(50):
        types = ['Course', 'Assessment', 'Certification', 'Program']
        selected_type = random.choice(types)
        
        # Filter by type if specified
        if item_type and item_type != selected_type:
            continue
        
        items.append({
            'id': f'item-{i}',
            'title': f'Learning Item {i}',
            'description': f'Description for learning item {i}',
            'type': selected_type,
            'duration': random.randint(30, 240),  # in minutes
            'creditHours': round(random.uniform(0.5, 4.0), 1),
            'createdDate': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
        })
    
    return jsonify(items)

@learning_bp.route('/analytics', methods=['GET'])
@token_required
def get_learning_analytics(current_user):
    # Parse query parameters
    timeframe = request.args.get('timeframe', 'month')
    
    # Mock data - replace with actual database queries in production
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations', 'IT', 'Customer Support']
    
    # Generate department completion data
    by_department = []
    for dept in departments:
        by_department.append({
            'department': dept,
            'completionRate': random.randint(60, 95),
            'totalUsers': random.randint(20, 100)
        })
    
    # Generate trend data
    trends = []
    periods = []
    
    if timeframe == 'week':
        # Last 7 days
        for i in range(7):
            day = datetime.now() - timedelta(days=i)
            periods.append(day.strftime('%a'))
        periods.reverse()
        
        for period in periods:
            trends.append({
                'period': period,
                'completions': random.randint(5, 30)
            })
    elif timeframe == 'month':
        # Last 4 weeks
        for i in range(4):
            week = datetime.now() - timedelta(weeks=i)
            periods.append(f'Week {4-i}')
        periods.reverse()
        
        for period in periods:
            trends.append({
                'period': period,
                'completions': random.randint(20, 80)
            })
    elif timeframe == 'quarter':
        # Last 3 months
        current_month = datetime.now().month
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(3):
            month_index = (current_month - i - 1) % 12
            periods.append(months[month_index])
        periods.reverse()
        
        for period in periods:
            trends.append({
                'period': period,
                'completions': random.randint(50, 200)
            })
    else:  # year
        # Last 6 months
        current_month = datetime.now().month
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(6):
            month_index = (current_month - i - 1) % 12
            periods.append(months[month_index])
        periods.reverse()
        
        for period in periods:
            trends.append({
                'period': period,
                'completions': random.randint(50, 200)
            })
    
    # Generate compliance data
    compliance = []
    courses = [
        'Data Security Training',
        'Ethics and Compliance',
        'Workplace Safety',
        'Harassment Prevention',
        'Code of Conduct',
        'Privacy Regulations',
        'Information Security'
    ]
    
    for course in courses:
        required = random.randint(50, 200)
        completed = random.randint(30, required)
        compliance_rate = round((completed / required) * 100)
        
        compliance.append({
            'course': course,
            'required': required,
            'completed': completed,
            'compliance': compliance_rate,
            'dueDate': (datetime.now() + timedelta(days=random.randint(10, 90))).isoformat()
        })
    
    return jsonify({
        'byDepartment': by_department,
        'trends': trends,
        'compliance': compliance
    })
```

### 5. User Routes

```python
# src/routes/users.py
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import random
from src.routes.auth import token_required

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@token_required
def get_users(current_user):
    # Parse query parameters
    department = request.args.get('department')
    search = request.args.get('search', '')
    
    # Mock data - replace with actual database queries in production
    users = []
    
    # Generate random user data
    for i in range(1, 101):
        departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
        selected_dept = random.choice(departments)
        
        # Filter by department if specified
        if department and department != selected_dept:
            continue
        
        user_name = f'User {i}'
        
        # Filter by search term if specified
        if search and search.lower() not in user_name.lower():
            continue
        
        users.append({
            'id': f'user-{i}',
            'name': user_name,
            'email': f'user{i}@example.com',
            'department': selected_dept,
            'jobTitle': f'Job Title {i}',
            'manager': f'Manager {random.randint(1, 10)}',
            'hireDate': (datetime.now() - timedelta(days=random.randint(30, 1825))).isoformat()
        })
    
    return jsonify(users)

@users_bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user_details(current_user, user_id):
    # Mock data - replace with actual database queries in production
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
    
    user = {
        'id': user_id,
        'name': f'User {user_id.split("-")[1]}',
        'email': f'{user_id}@example.com',
        'department': random.choice(departments),
        'jobTitle': f'Job Title {user_id.split("-")[1]}',
        'manager': f'Manager {random.randint(1, 10)}',
        'location': f'Location {random.randint(1, 5)}',
        'hireDate': (datetime.now() - timedelta(days=random.randint(30, 1825))).isoformat(),
        'phone': f'+1 555-{random.randint(100, 999)}-{random.randint(1000, 9999)}'
    }
    
    return jsonify(user)

@users_bp.route('/<user_id>/learning', methods=['GET'])
@token_required
def get_user_learning(current_user, user_id):
    # Mock data - replace with actual database queries in production
    learning_history = []
    
    # Generate random learning history
    for i in range(10):
        completion_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        learning_history.append({
            'id': f'hist-{i}',
            'course': f'Course {random.randint(1, 50)}',
            'completionDate': completion_date.isoformat(),
            'score': random.randint(70, 100),
            'status': 'Completed'
        })
    
    # Sort by completion date (newest first)
    learning_history.sort(key=lambda x: x['completionDate'], reverse=True)
    
    return jsonify(learning_history)

@users_bp.route('/<user_id>/assignments', methods=['GET'])
@token_required
def get_user_assignments(current_user, user_id):
    # Mock data - replace with actual database queries in production
    assignments = []
    
    # Generate random assignments
    for i in range(5):
        statuses = ['Assigned', 'In Progress', 'Completed', 'Overdue']
        selected_status = random.choice(statuses)
        
        assignment_date = datetime.now() - timedelta(days=random.randint(1, 30))
        due_date = datetime.now() + timedelta(days=random.randint(1, 60))
        
        # If status is overdue, set due date in the past
        if selected_status == 'Overdue':
            due_date = datetime.now() - timedelta(days=random.randint(1, 10))
        
        assignments.append({
            'id': f'assign-{i}',
            'course': f'Course {random.randint(1, 50)}',
            'assignmentDate': assignment_date.isoformat(),
            'dueDate': due_date.isoformat(),
            'status': selected_status,
            'progress': random.randint(0, 100) if selected_status == 'In Progress' else 
                        (100 if selected_status == 'Completed' else 0)
        })
    
    return jsonify(assignments)

@users_bp.route('/<user_id>/profile', methods=['GET'])
@token_required
def get_employee_profile(current_user, user_id):
    # Mock data - replace with actual database queries in production
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance']
    selected_dept = random.choice(departments)
    
    # Basic profile information
    profile = {
        'id': user_id,
        'name': f'User {user_id.split("-")[1]}',
        'email': f'{user_id}@example.com',
        'department': selected_dept,
        'manager': f'Manager {random.randint(1, 10)}',
        'completedCourses': random.randint(5, 20),
        'assignedCourses': random.randint(3, 10),
        'completionRate': random.randint(60, 95)
    }
    
    # Learning history
    learning_history = []
    for i in range(10):
        completion_date = datetime.now() - timedelta(days=random.randint(1, 365))
        
        learning_history.append({
            'id': f'hist-{i}',
            'course': f'Course {random.randint(1, 50)}',
            'completionDate': completion_date.isoformat(),
            'score': random.randint(70, 100),
            'status': 'Completed'
        })
    
    # Sort by completion date (newest first)
    learning_history.sort(key=lambda x: x['completionDate'], reverse=True)
    
    # Assigned learning
    assigned_learning = []
    for i in range(5):
        statuses = ['Assigned', 'In Progress', 'Overdue']
        selected_status = random.choice(statuses)
        
        assignment_date = datetime.now() - timedelta(days=random.randint(1, 30))
        due_date = datetime.now() + timedelta(days=random.randint(1, 60))
        
        # If status is overdue, set due date in the past
        if selected_status == 'Overdue':
            due_date = datetime.now() - timedelta(days=random.randint(1, 10))
        
        assigned_learning.append({
            'id': f'assign-{i}',
            'course': f'Course {random.randint(1, 50)}',
            'dueDate': due_date.isoformat(),
            'status': selected_status,
            'progress': random.randint(0, 100) if selected_status == 'In Progress' else 0
        })
    
    # Skills
    skills = []
    skill_names = ['Leadership', 'Communication', 'Technical Knowledge', 
                  'Problem Solving', 'Project Management', 'Teamwork']
    
    for skill in skill_names:
        current = random.randint(1, 5)
        target = min(5, current + random.randint(0, 2))
        
        skills.append({
            'name': skill,
            'current': current,
            'target': target
        })
    
    # Add all data to profile
    profile['learningHistory'] = learning_history
    profile['assignedLearning'] = assigned_learning
    profile['skills'] = skills
    
    return jsonify(profile)
```

## API Integration Layer

```typescript
// src/lib/api.ts
import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication
export const login = async (username: string, password: string) => {
  const response = await api.post('/auth/login', { username, password });
  const { token, user } = response.data;
  
  // Store token in localStorage
  localStorage.setItem('token', token);
  
  return user;
};

export const logout = async () => {
  await api.post('/auth/logout');
  localStorage.removeItem('token');
};

// Dashboard
export const fetchDashboardSummary = async () => {
  const response = await api.get('/dashboard/summary');
  return response.data;
};

export const fetchDashboardTrends = async () => {
  const response = await api.get('/dashboard/trends');
  return response.data;
};

export const fetchComplianceMetrics = async () => {
  const response = await api.get('/dashboard/compliance');
  return response.data;
};

// Learning
export const fetchLearningCompletions = async (params = {}) => {
  const response = await api.get('/learning/completions', { params });
  return response.data;
};

export const fetchLearningAssignments = async (params = {}) => {
  const response = await api.get('/learning/assignments', { params });
  return response.data;
};

export const fetchLearningItems = async (params = {}) => {
  const response = await api.get('/learning/items', { params });
  return response.data;
};

export const fetchLearningAnalytics = async (timeframe = 'month') => {
  const response = await api.get('/learning/analytics', { params: { timeframe } });
  return response.data;
};

// Users
export const fetchUsers = async (params = {}) => {
  const response = await api.get('/users', { params });
  return response.data;
};

export const fetchUserDetails = async (userId: string) => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};

export const fetchUserLearning = async (userId: string) => {
  const response = await api.get(`/users/${userId}/learning`);
  return response.data;
};

export const fetchUserAssignments = async (userId: string) => {
  const response = await api.get(`/users/${userId}/assignments`);
  return response.data;
};

export const fetchEmployeeProfile = async (userId: string) => {
  const response = await api.get(`/users/${userId}/profile`);
  return response.data;
};

// Reports
export const generateReport = async (reportConfig: any) => {
  const response = await api.post('/reports/generate', reportConfig);
  return response.data;
};

export const saveReportTemplate = async (template: any) => {
  const response = await api.post('/reports/templates', template);
  return response.data;
};

export const fetchReportTemplates = async () => {
  const response = await api.get('/reports/templates');
  return response.data;
};

export default api;
```

## Main App Component

```tsx
// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LoginForm } from './components/auth/LoginForm';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { DashboardOverview } from './components/dashboard/DashboardOverview';
import { LearningCompletionAnalytics } from './components/analytics/LearningCompletionAnalytics';
import { EmployeeLearningProfile } from './components/profiles/EmployeeLearningProfile';
import { ReportBuilder } from './components/reports/ReportBuilder';
import { AuthProvider, useAuth } from './hooks/useAuth';
import './App.css';

// Protected route component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardOverview />} />
            <Route path="analytics" element={<LearningCompletionAnalytics />} />
            <Route path="employees/:employeeId" element={<EmployeeLearningProfile />} />
            <Route path="reports" element={<ReportBuilder />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
```

This implementation provides a comprehensive foundation for the SuccessFactors Learning dashboard web application, including:

1. **Frontend Components**: React components for authentication, dashboard, analytics, employee profiles, and reporting
2. **Backend API**: Flask routes for authentication, dashboard data, learning data, user data, and report generation
3. **API Integration**: TypeScript service for connecting the frontend to the backend API

The implementation follows best practices for:
- Component-based architecture
- Type safety with TypeScript
- Responsive design
- Authentication and authorization
- Error handling
- Data visualization

The next steps would be to:
1. Implement the remaining UI components
2. Connect to the actual database instead of mock data
3. Implement testing for both frontend and backend
4. Set up deployment procedures
