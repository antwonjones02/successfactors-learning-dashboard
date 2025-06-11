# Data Pipeline Implementation

This document outlines the implementation of the data pipeline, ETL processes, and monitoring systems for the SuccessFactors Learning dashboard application.

## Project Structure

```
learning_dashboard/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # OAuth authentication implementation
│   │   ├── client.py         # API client with rate limiting
│   │   └── endpoints/        # Endpoint-specific modules
│   │       ├── __init__.py
│   │       ├── learning.py   # Learning completion endpoints
│   │       └── users.py      # User and org structure endpoints
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── extractors/       # Data extraction modules
│   │   │   ├── __init__.py
│   │   │   ├── learning_extractor.py
│   │   │   └── user_extractor.py
│   │   ├── transformers/     # Data transformation modules
│   │   │   ├── __init__.py
│   │   │   ├── learning_transformer.py
│   │   │   └── user_transformer.py
│   │   ├── loaders/          # Database loading modules
│   │   │   ├── __init__.py
│   │   │   ├── learning_loader.py
│   │   │   └── user_loader.py
│   │   └── pipeline.py       # Pipeline orchestration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schema.py         # Database schema
│   │   └── connection.py     # Database connection management
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── logging.py        # Logging configuration
│   │   ├── metrics.py        # Metrics collection
│   │   └── alerts.py         # Alert system
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py       # Application settings
│   └── app.py                # Main application entry point
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_etl/
│   └── test_monitoring/
├── requirements.txt
└── README.md
```

## Authentication Implementation

```python
# src/api/auth.py
import base64
import requests
import time
import logging
from typing import Dict, Optional
from ..config.settings import settings

logger = logging.getLogger(__name__)

class OAuthTokenManager:
    """
    Manages OAuth token lifecycle for SuccessFactors API authentication.
    """
    def __init__(self):
        self.client_id = settings.SF_CLIENT_ID
        self.client_secret = settings.SF_CLIENT_SECRET
        self.token_url = settings.SF_TOKEN_URL
        self._token = None
        self._token_expiry = 0
        self._refresh_buffer = 300  # Refresh token 5 minutes before expiry

    def get_token(self) -> str:
        """
        Get a valid OAuth token, refreshing if necessary.
        """
        if not self._is_token_valid():
            self._refresh_token()
        return self._token

    def _is_token_valid(self) -> bool:
        """
        Check if the current token is valid and not near expiry.
        """
        if not self._token:
            return False
        current_time = time.time()
        return current_time < (self._token_expiry - self._refresh_buffer)

    def _refresh_token(self) -> None:
        """
        Refresh the OAuth token by making a request to the token endpoint.
        """
        try:
            # Concatenate client ID and secret with colon separator
            credentials = f"{self.client_id}:{self.client_secret}"
            
            # Base64 encode the credentials
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Set up headers with encoded credentials
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Set up request body
            data = {
                "grant_type": "client_credentials",
                "scope": "api"
            }
            
            # Make request to token endpoint
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            # Parse response
            token_data = response.json()
            self._token = token_data["access_token"]
            
            # Calculate token expiry time
            self._token_expiry = time.time() + token_data["expires_in"]
            
            logger.info("Successfully refreshed OAuth token")
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {str(e)}")
            raise

    def clear_token(self) -> None:
        """
        Clear the current token, forcing a refresh on next use.
        """
        self._token = None
        self._token_expiry = 0
        logger.info("OAuth token cleared")

# Singleton instance for application-wide use
token_manager = OAuthTokenManager()
```

## API Client Implementation

```python
# src/api/client.py
import requests
import logging
import time
from typing import Dict, Any, Optional
from .auth import token_manager
from ..monitoring.metrics import record_api_call

logger = logging.getLogger(__name__)

class RateLimitExceededError(Exception):
    """Exception raised when API rate limit is exceeded."""
    pass

class APIClient:
    """
    Client for making requests to the SuccessFactors API with rate limiting,
    retries, and error handling.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.rate_limit_window = 60  # seconds
        self.max_requests_per_window = 100
        self.request_timestamps = []

    def _check_rate_limit(self) -> None:
        """
        Check if we're within rate limits, and wait if necessary.
        """
        current_time = time.time()
        
        # Remove timestamps older than the window
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                  if current_time - ts < self.rate_limit_window]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.max_requests_per_window:
            oldest_timestamp = min(self.request_timestamps)
            sleep_time = self.rate_limit_window - (current_time - oldest_timestamp)
            
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.request_timestamps.append(time.time())

    def request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the API with retries and error handling.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token_manager.get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        self._check_rate_limit()
        
        start_time = time.time()
        success = False
        response = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data,
                    timeout=30
                )
                
                # Check for rate limiting response
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    logger.warning(f"Rate limit exceeded, retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                # Check for authentication error
                if response.status_code == 401:
                    logger.warning("Authentication token expired, refreshing")
                    token_manager.clear_token()
                    headers["Authorization"] = f"Bearer {token_manager.get_token()}"
                    continue
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Success
                success = True
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {sleep_time} seconds")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    raise
            finally:
                # Record metrics regardless of success/failure
                duration = time.time() - start_time
                record_api_call(
                    endpoint=endpoint,
                    method=method,
                    status_code=response.status_code if response else 0,
                    duration=duration,
                    success=success
                )
```

## ETL Pipeline Implementation

```python
# src/etl/pipeline.py
import logging
import time
from typing import List, Dict, Any, Callable
from datetime import datetime
from ..db.connection import get_db_session
from ..monitoring.metrics import record_etl_job

logger = logging.getLogger(__name__)

class ETLPipeline:
    """
    Orchestrates the ETL process for SuccessFactors data.
    """
    def __init__(self, name: str):
        self.name = name
        self.extractors = []
        self.transformers = []
        self.loaders = []
        self.validators = []
        self.db_session = get_db_session()

    def add_extractor(self, extractor: Callable) -> None:
        """Add a data extraction function to the pipeline."""
        self.extractors.append(extractor)

    def add_transformer(self, transformer: Callable) -> None:
        """Add a data transformation function to the pipeline."""
        self.transformers.append(transformer)

    def add_loader(self, loader: Callable) -> None:
        """Add a data loading function to the pipeline."""
        self.loaders.append(loader)

    def add_validator(self, validator: Callable) -> None:
        """Add a data validation function to the pipeline."""
        self.validators.append(validator)

    def run(self) -> Dict[str, Any]:
        """
        Execute the full ETL pipeline and return metrics.
        """
        start_time = time.time()
        job_id = f"{self.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Starting ETL pipeline: {self.name} (job_id: {job_id})")
        
        metrics = {
            "job_id": job_id,
            "pipeline_name": self.name,
            "start_time": datetime.now().isoformat(),
            "records_processed": 0,
            "records_loaded": 0,
            "validation_errors": 0,
            "status": "started"
        }
        
        try:
            # Extract data
            logger.info(f"Extracting data for {self.name}")
            extracted_data = []
            for extractor in self.extractors:
                extracted_batch = extractor()
                extracted_data.extend(extracted_batch)
            
            metrics["records_extracted"] = len(extracted_data)
            logger.info(f"Extracted {len(extracted_data)} records")
            
            # Transform data
            logger.info(f"Transforming data for {self.name}")
            transformed_data = extracted_data
            for transformer in self.transformers:
                transformed_data = transformer(transformed_data)
            
            metrics["records_transformed"] = len(transformed_data)
            logger.info(f"Transformed {len(transformed_data)} records")
            
            # Validate data
            logger.info(f"Validating data for {self.name}")
            valid_data = []
            validation_errors = []
            
            for record in transformed_data:
                record_valid = True
                
                for validator in self.validators:
                    is_valid, error = validator(record)
                    if not is_valid:
                        record_valid = False
                        validation_errors.append({
                            "record": record,
                            "error": error
                        })
                        break
                
                if record_valid:
                    valid_data.append(record)
            
            metrics["validation_errors"] = len(validation_errors)
            metrics["records_valid"] = len(valid_data)
            
            if validation_errors:
                logger.warning(f"Found {len(validation_errors)} validation errors")
            
            # Load data
            logger.info(f"Loading data for {self.name}")
            records_loaded = 0
            
            for loader in self.loaders:
                loaded_count = loader(valid_data, self.db_session)
                records_loaded += loaded_count
            
            self.db_session.commit()
            metrics["records_loaded"] = records_loaded
            logger.info(f"Loaded {records_loaded} records")
            
            metrics["status"] = "completed"
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {str(e)}", exc_info=True)
            self.db_session.rollback()
            metrics["status"] = "failed"
            metrics["error"] = str(e)
        finally:
            self.db_session.close()
            
            # Calculate duration
            end_time = time.time()
            duration = end_time - start_time
            metrics["duration_seconds"] = duration
            metrics["end_time"] = datetime.now().isoformat()
            
            # Record metrics
            record_etl_job(
                pipeline_name=self.name,
                job_id=job_id,
                records_processed=metrics.get("records_extracted", 0),
                records_loaded=metrics.get("records_loaded", 0),
                validation_errors=metrics.get("validation_errors", 0),
                duration=duration,
                status=metrics["status"]
            )
            
            logger.info(f"ETL pipeline {self.name} completed in {duration:.2f} seconds with status: {metrics['status']}")
            
            return metrics
```

## Data Extraction Implementation

```python
# src/etl/extractors/learning_extractor.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...api.client import APIClient
from ...config.settings import settings

logger = logging.getLogger(__name__)

class LearningCompletionExtractor:
    """
    Extracts learning completion data from SuccessFactors API.
    """
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.base_endpoint = "user/learningHistory/v1"
        self.page_size = 100
        
    def extract_learning_history(self, last_sync_date: Optional[datetime] = None, 
                                max_records: int = 1000) -> List[Dict[str, Any]]:
        """
        Extract learning history data with pagination and optional date filtering.
        """
        logger.info("Extracting learning completion data")
        
        all_completions = []
        page = 0
        more_data = True
        
        # Prepare date filter if provided
        date_filter = None
        if last_sync_date:
            date_str = last_sync_date.strftime("%Y-%m-%dT%H:%M:%S")
            date_filter = f"lastModified gt datetime'{date_str}'"
            logger.info(f"Filtering learning completions since {date_str}")
        
        while more_data and len(all_completions) < max_records:
            try:
                params = {
                    "$skip": page * self.page_size,
                    "$top": self.page_size,
                    "$format": "json"
                }
                
                if date_filter:
                    params["$filter"] = date_filter
                
                response = self.api_client.request(
                    method="GET",
                    endpoint=self.base_endpoint,
                    params=params
                )
                
                # Extract results from response
                completions = response.get("d", {}).get("results", [])
                all_completions.extend(completions)
                
                # Check if we have more data
                if len(completions) < self.page_size:
                    more_data = False
                else:
                    page += 1
                
                logger.info(f"Extracted {len(completions)} learning completions (page {page})")
                
            except Exception as e:
                logger.error(f"Error extracting learning completions: {str(e)}")
                raise
        
        logger.info(f"Completed extraction of {len(all_completions)} learning completions")
        return all_completions
    
    def extract_learning_items(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Extract detailed information about learning items.
        """
        logger.info(f"Extracting details for {len(item_ids)} learning items")
        
        all_items = []
        
        # Process in batches to avoid large requests
        batch_size = 20
        for i in range(0, len(item_ids), batch_size):
            batch_ids = item_ids[i:i+batch_size]
            id_filter = " or ".join([f"itemID eq '{item_id}'" for item_id in batch_ids])
            
            try:
                params = {
                    "$filter": id_filter,
                    "$format": "json"
                }
                
                response = self.api_client.request(
                    method="GET",
                    endpoint="admin/searchItem/v1",
                    params=params
                )
                
                # Extract results from response
                items = response.get("d", {}).get("results", [])
                all_items.extend(items)
                
                logger.info(f"Extracted details for {len(items)} learning items (batch {i//batch_size + 1})")
                
            except Exception as e:
                logger.error(f"Error extracting learning item details: {str(e)}")
                raise
        
        logger.info(f"Completed extraction of {len(all_items)} learning item details")
        return all_items
```

## Monitoring Implementation

```python
# src/monitoring/logging.py
import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from ..config.settings import settings

def setup_logging():
    """
    Configure application logging with structured JSON format.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create file handler for rotating logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Create JSON formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Add exception info if available
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            
            # Add extra fields if available
            if hasattr(record, "extra"):
                log_record.update(record.extra)
            
            return json.dumps(log_record)
    
    # Set formatters
    json_formatter = JsonFormatter()
    file_handler.setFormatter(json_formatter)
    
    # Use simpler format for console
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return root_logger

# src/monitoring/metrics.py
import time
import logging
import threading
from typing import Dict, Any
from datetime import datetime
from ..db.connection import get_db_session
from ..db.models import APICallLog, ETLJobLog

logger = logging.getLogger(__name__)

# Thread-local storage for metrics
_local = threading.local()

def record_api_call(endpoint: str, method: str, status_code: int, 
                   duration: float, success: bool) -> None:
    """
    Record metrics for an API call.
    """
    try:
        session = get_db_session()
        
        log_entry = APICallLog(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=int(duration * 1000),
            success=success,
            timestamp=datetime.utcnow()
        )
        
        session.add(log_entry)
        session.commit()
        
        logger.debug(f"Recorded API call metrics: {endpoint} ({status_code})")
    except Exception as e:
        logger.error(f"Failed to record API call metrics: {str(e)}")
    finally:
        session.close()

def record_etl_job(pipeline_name: str, job_id: str, records_processed: int,
                  records_loaded: int, validation_errors: int, 
                  duration: float, status: str) -> None:
    """
    Record metrics for an ETL job.
    """
    try:
        session = get_db_session()
        
        log_entry = ETLJobLog(
            job_id=job_id,
            pipeline_name=pipeline_name,
            records_processed=records_processed,
            records_loaded=records_loaded,
            validation_errors=validation_errors,
            duration_seconds=duration,
            status=status,
            start_time=datetime.utcnow() - timedelta(seconds=duration),
            end_time=datetime.utcnow()
        )
        
        session.add(log_entry)
        session.commit()
        
        logger.debug(f"Recorded ETL job metrics: {pipeline_name} ({status})")
    except Exception as e:
        logger.error(f"Failed to record ETL job metrics: {str(e)}")
    finally:
        session.close()

# src/monitoring/alerts.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from ..config.settings import settings

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Manages alerts for critical system events.
    """
    def __init__(self):
        self.email_enabled = settings.ALERT_EMAIL_ENABLED
        self.email_from = settings.ALERT_EMAIL_FROM
        self.email_to = settings.ALERT_EMAIL_TO
        self.email_server = settings.ALERT_EMAIL_SERVER
        self.email_port = settings.ALERT_EMAIL_PORT
        self.email_username = settings.ALERT_EMAIL_USERNAME
        self.email_password = settings.ALERT_EMAIL_PASSWORD
        
        # Alert thresholds
        self.api_error_threshold = 5  # Number of API errors in a row
        self.etl_failure_threshold = 2  # Number of ETL failures in a row
        
        # Alert state
        self.consecutive_api_errors = 0
        self.consecutive_etl_failures = 0
    
    def check_api_error(self, endpoint: str, status_code: int, error_message: str) -> None:
        """
        Check if an API error should trigger an alert.
        """
        self.consecutive_api_errors += 1
        
        if self.consecutive_api_errors >= self.api_error_threshold:
            self.send_alert(
                subject=f"API Error Alert: {endpoint}",
                message=f"Multiple API errors detected for endpoint {endpoint}.\n"
                        f"Latest error: {status_code} - {error_message}\n"
                        f"This has occurred {self.consecutive_api_errors} times in a row."
            )
    
    def reset_api_error_count(self) -> None:
        """
        Reset the consecutive API error count after a successful call.
        """
        self.consecutive_api_errors = 0
    
    def check_etl_failure(self, pipeline_name: str, error_message: str) -> None:
        """
        Check if an ETL failure should trigger an alert.
        """
        self.consecutive_etl_failures += 1
        
        if self.consecutive_etl_failures >= self.etl_failure_threshold:
            self.send_alert(
                subject=f"ETL Failure Alert: {pipeline_name}",
                message=f"Multiple ETL failures detected for pipeline {pipeline_name}.\n"
                        f"Latest error: {error_message}\n"
                        f"This has occurred {self.consecutive_etl_failures} times in a row."
            )
    
    def reset_etl_failure_count(self) -> None:
        """
        Reset the consecutive ETL failure count after a successful run.
        """
        self.consecutive_etl_failures = 0
    
    def send_alert(self, subject: str, message: str) -> None:
        """
        Send an alert via configured channels.
        """
        logger.warning(f"ALERT: {subject} - {message}")
        
        if self.email_enabled:
            try:
                self._send_email_alert(subject, message)
            except Exception as e:
                logger.error(f"Failed to send email alert: {str(e)}")
    
    def _send_email_alert(self, subject: str, message: str) -> None:
        """
        Send an alert via email.
        """
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg['Subject'] = f"[SuccessFactors Dashboard Alert] {subject}"
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(self.email_server, self.email_port)
        server.starttls()
        server.login(self.email_username, self.email_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email alert sent: {subject}")

# Singleton instance
alert_manager = AlertManager()
```

## Database Models Implementation

```python
# src/db/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(String(255), primary_key=True)
    username = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255))
    manager_id = Column(String(255), ForeignKey('users.user_id'))
    department = Column(String(255))
    division = Column(String(255))
    location = Column(String(255))
    job_title = Column(String(255))
    hire_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    manager = relationship("User", remote_side=[user_id])
    direct_reports = relationship("User", back_populates="manager")
    completions = relationship("LearningCompletion", back_populates="user")
    assignments = relationship("LearningAssignment", back_populates="user")

class LearningItem(Base):
    __tablename__ = 'learning_items'
    
    item_id = Column(String(255), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    duration = Column(Integer)  # in minutes
    credit_hours = Column(Numeric(10, 2))
    cpe_hours = Column(Numeric(10, 2))
    created_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    completions = relationship("LearningCompletion", back_populates="item")
    assignments = relationship("LearningAssignment", back_populates="item")

class LearningCompletion(Base):
    __tablename__ = 'learning_completions'
    
    completion_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    item_id = Column(String(255), ForeignKey('learning_items.item_id'), nullable=False)
    status = Column(String(50), nullable=False)
    completion_date = Column(DateTime)
    expiration_date = Column(DateTime)
    score = Column(Numeric(5, 2))
    credit_hours_earned = Column(Numeric(10, 2))
    cpe_hours_earned = Column(Numeric(10, 2))
    comments = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="completions")
    item = relationship("LearningItem", back_populates="completions")

class LearningAssignment(Base):
    __tablename__ = 'learning_assignments'
    
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    item_id = Column(String(255), ForeignKey('learning_items.item_id'), nullable=False)
    assigned_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    assigned_by = Column(String(255), ForeignKey('users.user_id'))
    status = Column(String(50), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="assignments")
    item = relationship("LearningItem", back_populates="assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])

class OrganizationalStructure(Base):
    __tablename__ = 'organizational_structure'
    
    org_id = Column(String(255), primary_key=True)
    parent_org_id = Column(String(255), ForeignKey('organizational_structure.org_id'))
    org_name = Column(String(255), nullable=False)
    org_type = Column(String(50))
    manager_id = Column(String(255), ForeignKey('users.user_id'))
    created_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("OrganizationalStructure", remote_side=[org_id])
    children = relationship("OrganizationalStructure", back_populates="parent")
    manager = relationship("User")
    members = relationship("UserOrganizationMapping", back_populates="organization")

class UserOrganizationMapping(Base):
    __tablename__ = 'user_organization_mapping'
    
    mapping_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    org_id = Column(String(255), ForeignKey('organizational_structure.org_id'), nullable=False)
    primary_org = Column(Boolean, default=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    organization = relationship("OrganizationalStructure", back_populates="members")

# Monitoring tables
class APICallLog(Base):
    __tablename__ = 'api_call_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ETLJobLog(Base):
    __tablename__ = 'etl_job_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), nullable=False)
    pipeline_name = Column(String(255), nullable=False)
    records_processed = Column(Integer)
    records_loaded = Column(Integer)
    validation_errors = Column(Integer)
    duration_seconds = Column(Float)
    status = Column(String(50), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
```

## Main Application Implementation

```python
# src/app.py
import logging
import argparse
import sys
from datetime import datetime, timedelta
from .api.client import APIClient
from .etl.extractors.learning_extractor import LearningCompletionExtractor
from .etl.extractors.user_extractor import UserExtractor
from .etl.transformers.learning_transformer import LearningTransformer
from .etl.transformers.user_transformer import UserTransformer
from .etl.loaders.learning_loader import LearningLoader
from .etl.loaders.user_loader import UserLoader
from .etl.pipeline import ETLPipeline
from .db.connection import init_db
from .monitoring.logging import setup_logging
from .config.settings import settings

# Set up logging
logger = setup_logging()

def run_user_pipeline(incremental: bool = True, days_back: int = 7):
    """
    Run the user data ETL pipeline.
    """
    logger.info("Starting user data ETL pipeline")
    
    # Initialize API client
    api_client = APIClient(settings.SF_API_BASE_URL)
    
    # Create pipeline
    pipeline = ETLPipeline("user_data")
    
    # Create extractors
    user_extractor = UserExtractor(api_client)
    
    # Set up extraction parameters
    last_sync_date = None
    if incremental:
        last_sync_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Add pipeline components
    pipeline.add_extractor(lambda: user_extractor.extract_users(last_sync_date))
    pipeline.add_transformer(UserTransformer().transform)
    pipeline.add_loader(UserLoader().load)
    
    # Run pipeline
    result = pipeline.run()
    
    logger.info(f"User data ETL pipeline completed with status: {result['status']}")
    return result

def run_learning_pipeline(incremental: bool = True, days_back: int = 7):
    """
    Run the learning data ETL pipeline.
    """
    logger.info("Starting learning data ETL pipeline")
    
    # Initialize API client
    api_client = APIClient(settings.SF_API_BASE_URL)
    
    # Create pipeline
    pipeline = ETLPipeline("learning_data")
    
    # Create extractors
    learning_extractor = LearningCompletionExtractor(api_client)
    
    # Set up extraction parameters
    last_sync_date = None
    if incremental:
        last_sync_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Add pipeline components
    pipeline.add_extractor(lambda: learning_extractor.extract_learning_history(last_sync_date))
    pipeline.add_transformer(LearningTransformer().transform)
    pipeline.add_loader(LearningLoader().load)
    
    # Run pipeline
    result = pipeline.run()
    
    logger.info(f"Learning data ETL pipeline completed with status: {result['status']}")
    return result

def main():
    """
    Main entry point for the ETL application.
    """
    parser = argparse.ArgumentParser(description='SuccessFactors Learning Dashboard ETL')
    parser.add_argument('--full', action='store_true', help='Run full extraction instead of incremental')
    parser.add_argument('--days', type=int, default=7, help='Days back for incremental extraction')
    parser.add_argument('--pipeline', choices=['all', 'users', 'learning'], default='all', 
                        help='Which pipeline to run')
    
    args = parser.parse_args()
    
    try:
        # Initialize database
        init_db()
        
        incremental = not args.full
        days_back = args.days
        
        if args.pipeline in ['all', 'users']:
            run_user_pipeline(incremental, days_back)
        
        if args.pipeline in ['all', 'learning']:
            run_learning_pipeline(incremental, days_back)
        
        logger.info("ETL process completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Configuration Implementation

```python
# src/config/settings.py
import os
from typing import Dict, Any

class Settings:
    """
    Application settings loaded from environment variables with defaults.
    """
    def __init__(self):
        # API Configuration
        self.SF_API_BASE_URL = os.getenv('SF_API_BASE_URL', 'https://api.successfactors.com')
        self.SF_CLIENT_ID = os.getenv('SF_CLIENT_ID', '')
        self.SF_CLIENT_SECRET = os.getenv('SF_CLIENT_SECRET', '')
        self.SF_TOKEN_URL = os.getenv('SF_TOKEN_URL', 'https://api.successfactors.com/oauth/token')
        
        # Database Configuration
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'sf_learning_dashboard')
        self.DB_USER = os.getenv('DB_USER', 'postgres')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
        
        # ETL Configuration
        self.ETL_BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '100'))
        self.ETL_MAX_WORKERS = int(os.getenv('ETL_MAX_WORKERS', '4'))
        self.ETL_RETRY_ATTEMPTS = int(os.getenv('ETL_RETRY_ATTEMPTS', '3'))
        
        # Monitoring Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.ALERT_EMAIL_ENABLED = os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
        self.ALERT_EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM', 'alerts@example.com')
        self.ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', 'admin@example.com')
        self.ALERT_EMAIL_SERVER = os.getenv('ALERT_EMAIL_SERVER', 'smtp.example.com')
        self.ALERT_EMAIL_PORT = int(os.getenv('ALERT_EMAIL_PORT', '587'))
        self.ALERT_EMAIL_USERNAME = os.getenv('ALERT_EMAIL_USERNAME', '')
        self.ALERT_EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD', '')
    
    def get_db_url(self) -> str:
        """
        Get the database connection URL.
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Return settings as a dictionary, masking sensitive values.
        """
        settings_dict = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        # Mask sensitive values
        for key in ['SF_CLIENT_SECRET', 'DB_PASSWORD', 'ALERT_EMAIL_PASSWORD']:
            if key in settings_dict and settings_dict[key]:
                settings_dict[key] = '********'
        
        return settings_dict

# Create a singleton instance
settings = Settings()
```

## Database Connection Implementation

```python
# src/db/connection.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from .models import Base
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.get_db_url(),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    echo=False
)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def init_db():
    """
    Initialize the database by creating all tables.
    """
    try:
        logger.info("Initializing database")
        Base.metadata.create_all(engine)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

def get_db_session():
    """
    Get a database session.
    """
    return Session()

def close_db_session():
    """
    Close the current database session.
    """
    Session.remove()
```

## Requirements File

```
# requirements.txt
Flask==2.3.3
SQLAlchemy==2.0.20
psycopg2-binary==2.9.7
requests==2.31.0
python-dotenv==1.0.0
APScheduler==3.10.4
pydantic==2.3.0
pytest==7.4.0
pytest-cov==4.1.0
black==23.7.0
flake8==6.1.0
```

This implementation provides a robust foundation for the data pipeline, ETL processes, and monitoring systems for the SuccessFactors Learning dashboard application. The code includes:

1. **OAuth Authentication**: Secure token management with automatic refresh
2. **API Client**: Rate-limited client with retry logic and error handling
3. **ETL Pipeline**: Modular pipeline for extracting, transforming, and loading data
4. **Data Extractors**: Specialized extractors for learning and user data
5. **Database Models**: SQLAlchemy models matching the designed schema
6. **Monitoring**: Comprehensive logging, metrics collection, and alerting
7. **Configuration**: Environment-based configuration with sensible defaults

The implementation follows best practices for error handling, logging, and monitoring, ensuring the system is robust and maintainable.
