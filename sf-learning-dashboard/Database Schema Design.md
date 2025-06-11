# Database Schema Design

## Overview
This document outlines the database schema design for storing data extracted from the SAP SuccessFactors Learning API. The schema is designed to efficiently store and query learning completion data and employee organizational data.

## Schema Design

### Core Tables

#### 1. Users
```sql
CREATE TABLE users (
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
    last_updated TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);
```

#### 2. Learning Items
```sql
CREATE TABLE learning_items (
    item_id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL, -- Course, Assessment, Certification, Program
    duration INTEGER, -- in minutes
    credit_hours DECIMAL(10,2),
    cpe_hours DECIMAL(10,2),
    created_date TIMESTAMP,
    last_updated TIMESTAMP
);
```

#### 3. Learning Completions
```sql
CREATE TABLE learning_completions (
    completion_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- Completed, In Progress, Not Started
    completion_date TIMESTAMP,
    expiration_date TIMESTAMP,
    score DECIMAL(5,2),
    credit_hours_earned DECIMAL(10,2),
    cpe_hours_earned DECIMAL(10,2),
    comments TEXT,
    last_updated TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES learning_items(item_id)
);
```

#### 4. Learning Assignments
```sql
CREATE TABLE learning_assignments (
    assignment_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    assigned_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    assigned_by VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- Assigned, Completed, Overdue
    last_updated TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES learning_items(item_id),
    FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);
```

#### 5. Organizational Structure
```sql
CREATE TABLE organizational_structure (
    org_id VARCHAR(255) PRIMARY KEY,
    parent_org_id VARCHAR(255),
    org_name VARCHAR(255) NOT NULL,
    org_type VARCHAR(50), -- Department, Division, Team
    manager_id VARCHAR(255),
    created_date TIMESTAMP,
    last_updated TIMESTAMP,
    FOREIGN KEY (parent_org_id) REFERENCES organizational_structure(org_id),
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);
```

#### 6. User Organization Mapping
```sql
CREATE TABLE user_organization_mapping (
    mapping_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    org_id VARCHAR(255) NOT NULL,
    primary_org BOOLEAN DEFAULT FALSE,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    last_updated TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (org_id) REFERENCES organizational_structure(org_id)
);
```

### Supporting Tables

#### 7. Learning Curricula
```sql
CREATE TABLE learning_curricula (
    curriculum_id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_date TIMESTAMP,
    last_updated TIMESTAMP
);
```

#### 8. Curriculum Items
```sql
CREATE TABLE curriculum_items (
    curriculum_item_id SERIAL PRIMARY KEY,
    curriculum_id VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    sequence_number INTEGER,
    required BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP,
    last_updated TIMESTAMP,
    FOREIGN KEY (curriculum_id) REFERENCES learning_curricula(curriculum_id),
    FOREIGN KEY (item_id) REFERENCES learning_items(item_id)
);
```

#### 9. Curriculum Assignments
```sql
CREATE TABLE curriculum_assignments (
    assignment_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    curriculum_id VARCHAR(255) NOT NULL,
    assigned_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    assigned_by VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- Assigned, In Progress, Completed, Overdue
    last_updated TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (curriculum_id) REFERENCES learning_curricula(curriculum_id),
    FOREIGN KEY (assigned_by) REFERENCES users(user_id)
);
```

#### 10. API Sync Logs
```sql
CREATE TABLE api_sync_logs (
    log_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(50) NOT NULL, -- Success, Partial, Failed
    records_processed INTEGER,
    error_message TEXT,
    created_by VARCHAR(255)
);
```

## Indexes

```sql
-- Users table indexes
CREATE INDEX idx_users_manager_id ON users(manager_id);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_job_title ON users(job_title);

-- Learning items indexes
CREATE INDEX idx_learning_items_type ON learning_items(type);

-- Learning completions indexes
CREATE INDEX idx_learning_completions_user_id ON learning_completions(user_id);
CREATE INDEX idx_learning_completions_item_id ON learning_completions(item_id);
CREATE INDEX idx_learning_completions_status ON learning_completions(status);
CREATE INDEX idx_learning_completions_completion_date ON learning_completions(completion_date);

-- Learning assignments indexes
CREATE INDEX idx_learning_assignments_user_id ON learning_assignments(user_id);
CREATE INDEX idx_learning_assignments_item_id ON learning_assignments(item_id);
CREATE INDEX idx_learning_assignments_status ON learning_assignments(status);
CREATE INDEX idx_learning_assignments_due_date ON learning_assignments(due_date);

-- Organizational structure indexes
CREATE INDEX idx_org_structure_parent_id ON organizational_structure(parent_org_id);
CREATE INDEX idx_org_structure_manager_id ON organizational_structure(manager_id);

-- User organization mapping indexes
CREATE INDEX idx_user_org_mapping_user_id ON user_organization_mapping(user_id);
CREATE INDEX idx_user_org_mapping_org_id ON user_organization_mapping(org_id);
```

## Data Relationships

1. **User Hierarchy**: Users have a self-referential relationship through the manager_id field
2. **Organizational Hierarchy**: Organizations have a self-referential relationship through parent_org_id
3. **User-Organization**: Many-to-many relationship through user_organization_mapping
4. **Learning Assignments**: Links users to learning items
5. **Learning Completions**: Records completion status of learning items by users
6. **Curriculum Structure**: Curricula contain multiple learning items through curriculum_items
7. **Curriculum Assignments**: Links users to curricula

## ETL Considerations

1. **Incremental Updates**: Use last_updated timestamps to track changes
2. **Data Validation**: Enforce referential integrity through foreign keys
3. **Historical Tracking**: Maintain historical completion and assignment data
4. **Performance**: Optimize for reporting queries with appropriate indexes
5. **Audit Trail**: Log all data synchronization activities in api_sync_logs

## Reporting Views

```sql
-- Learning completion summary by user
CREATE VIEW vw_user_learning_summary AS
SELECT 
    u.user_id,
    u.first_name,
    u.last_name,
    u.department,
    COUNT(DISTINCT lc.item_id) AS completed_items,
    COUNT(DISTINCT la.item_id) AS assigned_items,
    COUNT(DISTINCT CASE WHEN la.status = 'Overdue' THEN la.item_id END) AS overdue_items
FROM 
    users u
LEFT JOIN 
    learning_completions lc ON u.user_id = lc.user_id AND lc.status = 'Completed'
LEFT JOIN 
    learning_assignments la ON u.user_id = la.user_id
GROUP BY 
    u.user_id, u.first_name, u.last_name, u.department;

-- Department learning completion rates
CREATE VIEW vw_department_completion_rates AS
SELECT 
    u.department,
    COUNT(DISTINCT u.user_id) AS total_users,
    COUNT(DISTINCT lc.user_id) AS users_with_completions,
    COUNT(DISTINCT lc.completion_id) AS total_completions,
    COUNT(DISTINCT lc.completion_id) / NULLIF(COUNT(DISTINCT u.user_id), 0) AS completions_per_user
FROM 
    users u
LEFT JOIN 
    learning_completions lc ON u.user_id = lc.user_id AND lc.status = 'Completed'
GROUP BY 
    u.department;
```

## Data Migration Strategy

1. **Initial Load**: Full extraction of all data from SuccessFactors API
2. **Delta Updates**: Incremental updates based on last_updated timestamps
3. **Data Validation**: Validate data integrity after each sync
4. **Error Handling**: Log errors and continue processing where possible
5. **Rollback Capability**: Maintain ability to restore previous state in case of issues
