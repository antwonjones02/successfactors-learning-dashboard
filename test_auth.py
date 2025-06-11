#!/usr/bin/env python3
"""
Test SuccessFactors Authentication
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Testing SuccessFactors Authentication")
print("=" * 50)

# Get credentials
client_id = os.getenv("SF_CLIENT_ID")
client_secret = os.getenv("SF_CLIENT_SECRET")
user_id = os.getenv("SF_USER_ID")
base_url = os.getenv("SF_BASE_URL")

print(f"Client ID: {client_id}")
print(f"User ID: {user_id}")
print(f"Base URL: {base_url}")
print(f"Client Secret: {'*' * 10} (hidden)")
print()

# Test authentication
token_url = f"{base_url}/learning/oauth-api/rest/v1/token"
print(f"Token URL: {token_url}")
print()

payload = {
    "grant_type": "client_credentials",
    "scope": {
        "userId": user_id,
        "companyId": client_id,
        "userType": "admin",
        "resourceType": "learning_public_api"
    },
    "client_id": client_id,
    "client_secret": client_secret
}

headers = {"Content-Type": "application/json"}

print("Sending authentication request...")
try:
    response = requests.post(token_url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Authentication successful!")
        token_data = response.json()
        access_token = token_data.get("access_token", "")
        print(f"Access Token: {access_token[:50]}...")
    else:
        print("✗ Authentication failed!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"✗ Exception occurred: {str(e)}")
    import traceback
    traceback.print_exc()