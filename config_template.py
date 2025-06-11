"""
Configuration Template for SuccessFactors Learning Dashboard
Copy this file to config_production.py and update with your credentials
"""

# PRODUCTION CREDENTIALS
# Replace these with your actual production values

SF_CONFIG = {
    "CLIENT_ID": "your-client-id",        # Your production client ID
    "CLIENT_SECRET": "your-client-secret", # Your production client secret
    "USER_ID": "your-user-id",            # Your production user ID
    "BASE_URL": "https://your-company.plateau.com",  # Your production URL
}

# SANDBOX CREDENTIALS (for testing)
SF_CONFIG_SANDBOX = {
    "CLIENT_ID": "sandbox-client-id",
    "CLIENT_SECRET": "sandbox-client-secret",
    "USER_ID": "sandbox-user-id",
    "BASE_URL": "https://sandbox.plateau.com",
}

# Toggle this to switch between sandbox and production
USE_PRODUCTION = False  # Set to True when ready for production

# Get the active configuration
ACTIVE_CONFIG = SF_CONFIG if USE_PRODUCTION else SF_CONFIG_SANDBOX