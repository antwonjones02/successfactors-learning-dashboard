# SuccessFactors Learning Dashboard - Maintenance Guide

## Overview

This maintenance guide provides instructions for ongoing operation, troubleshooting, and maintenance of the SuccessFactors Learning Dashboard application. It is intended for system administrators and technical staff responsible for maintaining the system.

## System Architecture

The SuccessFactors Learning Dashboard consists of the following components:

1. **Frontend Application**: React.js with TypeScript
2. **Backend API**: Flask (Python)
3. **Database**: MySQL
4. **Web Server**: Nginx
5. **Application Server**: Gunicorn
6. **Process Manager**: Systemd

## Routine Maintenance Tasks

### Daily Maintenance

| Task | Description | Command/Location |
|------|-------------|-----------------|
| Check system logs | Review logs for errors or warnings | `/var/log/sf-learning-api/` |
| Monitor API synchronization | Verify successful data synchronization | Admin dashboard or logs |
| Verify database backups | Ensure automated backups completed successfully | Backup logs |

### Weekly Maintenance

| Task | Description | Command/Location |
|------|-------------|-----------------|
| Review performance metrics | Check system performance and resource usage | Monitoring dashboard |
| Verify user access | Review user access logs for unusual activity | Security logs |
| Test system availability | Verify all components are functioning | Health check endpoints |
| Rotate logs | Archive and rotate log files | `logrotate` configuration |

### Monthly Maintenance

| Task | Description | Command/Location |
|------|-------------|-----------------|
| Apply security updates | Update system packages and dependencies | `apt update && apt upgrade` |
| Database optimization | Run database maintenance operations | MySQL maintenance scripts |
| SSL certificate check | Verify SSL certificates are not expiring soon | `/etc/letsencrypt/live/` |
| Review system usage | Analyze system usage patterns and growth | Analytics dashboard |

### Quarterly Maintenance

| Task | Description | Command/Location |
|------|-------------|-----------------|
| Dependency updates | Update application dependencies | `pip install --upgrade` |
| Full system backup | Perform complete system backup | Backup scripts |
| Security audit | Review security settings and access controls | Security configuration |
| Performance tuning | Optimize system based on usage patterns | Configuration files |

## Backup and Recovery

### Backup Strategy

The system employs a comprehensive backup strategy:

1. **Database Backups**:
   - Daily full backups
   - Hourly incremental backups
   - 30-day retention period

2. **Application Backups**:
   - Weekly full application backups
   - Configuration file backups after any changes
   - 90-day retention period

3. **Log Backups**:
   - Daily log archiving
   - 180-day retention period

### Backup Procedures

#### Database Backup

```bash
#!/bin/bash
# /usr/local/bin/backup_database.sh

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/database"
BACKUP_FILE="$BACKUP_DIR/sf_learning_db_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform database backup
mysqldump -u sf_learning_user -p'secure_password' sf_learning_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "sf_learning_db_*.sql.gz" -type f -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

#### Application Backup

```bash
#!/bin/bash
# /usr/local/bin/backup_application.sh

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/application"
BACKUP_FILE="$BACKUP_DIR/sf_learning_app_$TIMESTAMP.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup frontend application
tar -czf $BACKUP_FILE /var/www/sf-learning-dashboard /var/www/sf-learning-api

# Remove backups older than 90 days
find $BACKUP_DIR -name "sf_learning_app_*.tar.gz" -type f -mtime +90 -delete

echo "Application backup completed: $BACKUP_FILE"
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# /usr/local/bin/restore_database.sh

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Error: Backup file not provided"
    echo "Usage: ./restore_database.sh <backup_file>"
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Extract backup if compressed
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE > ${BACKUP_FILE%.gz}
    BACKUP_FILE=${BACKUP_FILE%.gz}
fi

# Restore database
mysql -u sf_learning_user -p'secure_password' sf_learning_db < $BACKUP_FILE

echo "Database restored successfully from: $BACKUP_FILE"
```

#### Application Recovery

```bash
#!/bin/bash
# /usr/local/bin/restore_application.sh

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Error: Backup file not provided"
    echo "Usage: ./restore_application.sh <backup_file>"
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop services
systemctl stop nginx
systemctl stop sf-learning-api

# Backup current application (just in case)
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
TEMP_BACKUP="/tmp/sf_learning_app_current_$TIMESTAMP.tar.gz"
tar -czf $TEMP_BACKUP /var/www/sf-learning-dashboard /var/www/sf-learning-api
echo "Current application backed up to: $TEMP_BACKUP"

# Restore from backup
tar -xzf $BACKUP_FILE -C /

# Set proper permissions
chown -R www-data:www-data /var/www/sf-learning-dashboard
chown -R www-data:www-data /var/www/sf-learning-api
chmod -R 755 /var/www/sf-learning-dashboard
chmod -R 755 /var/www/sf-learning-api

# Start services
systemctl start sf-learning-api
systemctl start nginx

echo "Application restored successfully from: $BACKUP_FILE"
```

## Monitoring and Alerting

### Monitoring Components

The system includes monitoring for:

1. **System Resources**:
   - CPU usage
   - Memory usage
   - Disk space
   - Network traffic

2. **Application Metrics**:
   - API response times
   - Request volume
   - Error rates
   - User sessions

3. **Database Metrics**:
   - Query performance
   - Connection pool usage
   - Table sizes
   - Index efficiency

4. **Integration Status**:
   - API connectivity
   - Authentication status
   - Data synchronization

### Alert Configuration

Alerts are configured for the following conditions:

| Alert | Threshold | Severity | Action |
|-------|-----------|----------|--------|
| High CPU usage | >80% for 5 minutes | Warning | Email notification |
| High CPU usage | >90% for 5 minutes | Critical | Email + SMS |
| Low disk space | <20% free | Warning | Email notification |
| Low disk space | <10% free | Critical | Email + SMS |
| API errors | >5% error rate | Warning | Email notification |
| API errors | >10% error rate | Critical | Email + SMS |
| Database connection issues | >3 failed connections | Critical | Email + SMS |
| Failed data synchronization | Any failure | Critical | Email + SMS |

### Log Management

Logs are stored in the following locations:

| Component | Log Location |
|-----------|--------------|
| Frontend | `/var/log/nginx/sf-learning-dashboard-access.log` |
| Frontend errors | `/var/log/nginx/sf-learning-dashboard-error.log` |
| Backend API | `/var/log/sf-learning-api/access.log` |
| Backend errors | `/var/log/sf-learning-api/error.log` |
| Database | `/var/log/mysql/mysql.log` |
| System | `/var/log/syslog` |

## Troubleshooting

### Common Issues and Solutions

#### Frontend Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| Blank page | JavaScript error, network issue | Check browser console, verify Nginx configuration |
| Slow loading | Large data sets, network latency | Check API response times, optimize queries |
| Authentication failure | Token expiration, invalid credentials | Clear browser cache, verify user credentials |
| Missing data | API errors, data synchronization issues | Check API logs, verify data synchronization status |

#### Backend Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| API timeout | Long-running queries, resource constraints | Optimize queries, check system resources |
| 500 errors | Application exceptions, configuration issues | Check error logs, verify configuration |
| Authentication failures | Invalid tokens, expired credentials | Check authentication logs, verify API credentials |
| Data synchronization failures | API changes, network issues | Check integration logs, verify API connectivity |

#### Database Issues

| Issue | Possible Causes | Solution |
|-------|----------------|----------|
| Slow queries | Missing indexes, large data sets | Analyze query performance, add indexes |
| Connection failures | Resource limits, configuration issues | Check connection settings, verify credentials |
| Data inconsistency | Failed transactions, synchronization issues | Verify transaction logs, check data integrity |
| High disk usage | Large tables, logs, temporary files | Clean up logs, optimize tables, add storage |

### Diagnostic Commands

#### System Diagnostics

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check service status
systemctl status nginx
systemctl status sf-learning-api
systemctl status mysql

# Check network connections
netstat -tuln

# Check log files
tail -f /var/log/sf-learning-api/error.log
```

#### Application Diagnostics

```bash
# Check API health
curl -i http://localhost:5000/api/health

# Test database connection
mysql -u sf_learning_user -p'secure_password' -e "SELECT 1" sf_learning_db

# Check Nginx configuration
nginx -t

# Check application logs
tail -f /var/log/sf-learning-api/error.log
```

## Scaling and Performance Tuning

### Vertical Scaling

To improve performance through vertical scaling:

1. **Increase server resources**:
   - Add more CPU cores
   - Increase RAM
   - Upgrade disk to SSD

2. **Optimize configurations**:
   - Increase Gunicorn workers: Edit `/var/www/sf-learning-api/gunicorn_config.py`
   - Tune MySQL settings: Edit `/etc/mysql/mysql.conf.d/mysqld.cnf`
   - Optimize Nginx: Edit `/etc/nginx/nginx.conf`

### Horizontal Scaling

For horizontal scaling:

1. **Load balancing**:
   - Add multiple application servers
   - Configure Nginx as load balancer
   - Implement sticky sessions if needed

2. **Database scaling**:
   - Implement read replicas
   - Consider database sharding for large datasets
   - Use connection pooling

### Caching Strategy

Implement caching to improve performance:

1. **API response caching**:
   - Configure Redis for API response caching
   - Set appropriate TTL for different endpoints
   - Implement cache invalidation on data updates

2. **Database query caching**:
   - Enable MySQL query cache
   - Implement application-level caching for frequent queries
   - Use prepared statements

## Security Maintenance

### Regular Security Tasks

| Task | Frequency | Description |
|------|-----------|-------------|
| Security updates | Monthly | Apply security patches to all system components |
| User access review | Quarterly | Review and verify user access permissions |
| Password policy enforcement | Ongoing | Ensure password policies are enforced |
| Security log review | Weekly | Review security logs for suspicious activity |
| Vulnerability scanning | Monthly | Scan system for security vulnerabilities |

### SSL Certificate Management

```bash
# Check SSL certificate expiration
openssl x509 -enddate -noout -in /etc/letsencrypt/live/sf-learning-dashboard.example.com/fullchain.pem

# Renew Let's Encrypt certificates
certbot renew

# Test Nginx SSL configuration
curl -k https://www.ssllabs.com/ssltest/analyze.html?d=sf-learning-dashboard.example.com
```

### Firewall Configuration

```bash
# Check firewall status
ufw status

# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp

# Deny all other incoming traffic
ufw default deny incoming
ufw default allow outgoing
```

## Upgrade Procedures

### Frontend Upgrade

```bash
#!/bin/bash
# /usr/local/bin/upgrade_frontend.sh

# Check if source directory is provided
if [ -z "$1" ]; then
    echo "Error: Source directory not provided"
    echo "Usage: ./upgrade_frontend.sh <source_directory>"
    exit 1
fi

SOURCE_DIR=$1

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Create backup of current frontend
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/upgrades"
BACKUP_FILE="$BACKUP_DIR/frontend_$TIMESTAMP.tar.gz"

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_FILE /var/www/sf-learning-dashboard
echo "Current frontend backed up to: $BACKUP_FILE"

# Deploy new frontend
rm -rf /var/www/sf-learning-dashboard/*
cp -r $SOURCE_DIR/* /var/www/sf-learning-dashboard/

# Set proper permissions
chown -R www-data:www-data /var/www/sf-learning-dashboard
chmod -R 755 /var/www/sf-learning-dashboard

# Reload Nginx
systemctl reload nginx

echo "Frontend upgrade completed successfully"
```

### Backend Upgrade

```bash
#!/bin/bash
# /usr/local/bin/upgrade_backend.sh

# Check if source directory is provided
if [ -z "$1" ]; then
    echo "Error: Source directory not provided"
    echo "Usage: ./upgrade_backend.sh <source_directory>"
    exit 1
fi

SOURCE_DIR=$1

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# Create backup of current backend
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/upgrades"
BACKUP_FILE="$BACKUP_DIR/backend_$TIMESTAMP.tar.gz"

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_FILE /var/www/sf-learning-api
echo "Current backend backed up to: $BACKUP_FILE"

# Stop service
systemctl stop sf-learning-api

# Deploy new backend
rm -rf /var/www/sf-learning-api/*
cp -r $SOURCE_DIR/* /var/www/sf-learning-api/

# Update dependencies
cd /var/www/sf-learning-api
source venv/bin/activate
pip install -r requirements.txt

# Set proper permissions
chown -R www-data:www-data /var/www/sf-learning-api
chmod -R 755 /var/www/sf-learning-api

# Start service
systemctl start sf-learning-api

echo "Backend upgrade completed successfully"
```

### Database Schema Upgrade

```bash
#!/bin/bash
# /usr/local/bin/upgrade_database.sh

# Check if schema file is provided
if [ -z "$1" ]; then
    echo "Error: Schema file not provided"
    echo "Usage: ./upgrade_database.sh <schema_file>"
    exit 1
fi

SCHEMA_FILE=$1

# Verify schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "Error: Schema file not found: $SCHEMA_FILE"
    exit 1
fi

# Create backup of current database
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/var/backups/sf-learning-dashboard/upgrades"
BACKUP_FILE="$BACKUP_DIR/database_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR
mysqldump -u sf_learning_user -p'secure_password' sf_learning_db > $BACKUP_FILE
echo "Current database backed up to: $BACKUP_FILE"

# Apply schema changes
mysql -u sf_learning_user -p'secure_password' sf_learning_db < $SCHEMA_FILE

echo "Database schema upgrade completed successfully"
```

## Contact Information

### Support Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| System Administrator | [Admin Name] | admin@example.com | (555) 123-4567 |
| Database Administrator | [DBA Name] | dba@example.com | (555) 123-4568 |
| Security Officer | [Security Name] | security@example.com | (555) 123-4569 |
| Vendor Support | SAP SuccessFactors | support@successfactors.com | (800) 555-1234 |

### Escalation Procedure

1. **Level 1**: System Administrator - First point of contact for all issues
2. **Level 2**: Database Administrator or Security Officer - Escalate based on issue type
3. **Level 3**: Vendor Support - Escalate for API or integration issues
4. **Level 4**: Management - Escalate for critical business impact issues

## Appendices

### Configuration Files

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/sf-learning-dashboard
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
    
    # API proxy
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### Gunicorn Configuration

```python
# /var/www/sf-learning-api/gunicorn_config.py
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
# /etc/systemd/system/sf-learning-api.service
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

### Environment Variables

```bash
# /var/www/sf-learning-api/.env.production
DB_USERNAME=sf_learning_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sf_learning_db
JWT_SECRET_KEY=your_secure_jwt_secret_key
SF_API_BASE_URL=https://api.successfactors.com
SF_API_CLIENT_ID=your_client_id
SF_API_CLIENT_SECRET=your_client_secret
LOG_LEVEL=info
```

### Cron Jobs

```bash
# Crontab entries

# Database backup (daily at 1:00 AM)
0 1 * * * /usr/local/bin/backup_database.sh > /var/log/sf-learning-dashboard/backup_db.log 2>&1

# Application backup (weekly on Sunday at 2:00 AM)
0 2 * * 0 /usr/local/bin/backup_application.sh > /var/log/sf-learning-dashboard/backup_app.log 2>&1

# Log rotation (daily at 3:00 AM)
0 3 * * * /usr/sbin/logrotate /etc/logrotate.d/sf-learning-dashboard

# SSL certificate renewal (twice daily)
0 */12 * * * /usr/bin/certbot renew --quiet

# Data synchronization (hourly)
0 * * * * curl -X POST http://localhost:5000/api/admin/sync > /var/log/sf-learning-dashboard/sync.log 2>&1
```

This maintenance guide provides comprehensive information for the ongoing operation, troubleshooting, and maintenance of the SuccessFactors Learning Dashboard application. System administrators should refer to this guide for routine maintenance tasks, troubleshooting common issues, and performing system upgrades.
