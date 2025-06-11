#!/usr/bin/env python3
"""
SuccessFactors Learning API Test - Version 2
Based on the working Skillsoft example
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_bearer_token(base_url, user_id, client_id, client_secret):
    """Get OAuth token following the Skillsoft pattern"""
    token_url = f"{base_url}/learning/oauth-api/rest/v1/token"
    
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
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Requesting token from: {token_url}")
    response = requests.post(token_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        print("✓ Authentication successful!")
        return token_data["access_token"]
    else:
        print(f"✗ Failed to get token: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_api_endpoints(base_url, access_token):
    """Test various API endpoints"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test endpoints similar to the recordLearningEvents endpoint
    test_endpoints = [
        "/learning/odatav4/public/admin/learningEvent/v1",
        "/learning/odatav4/public/admin/user-service/v1",
        "/learning/odatav4/public/admin/searchStudent/v1",
        "/learning/odatav4/public/user/learningHistory/v1",
        "/learning/odatav4/public/user/curriculum/v1"
    ]
    
    for endpoint in test_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTesting endpoint: {endpoint}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success! Response preview: {json.dumps(data, indent=2)[:200]}...")
                
                # If we get data, show the structure
                if 'value' in data and len(data['value']) > 0:
                    print(f"Found {len(data['value'])} records")
                    print(f"First record keys: {list(data['value'][0].keys())[:5]}...")
            else:
                print(f"✗ Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")

def main():
    # Get credentials from environment
    CLIENT_ID = os.getenv("SF_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET")
    USER_ID = os.getenv("SF_USER_ID")
    BASE_URL = os.getenv("SF_BASE_URL")
    
    print("=== SuccessFactors Learning API Test V2 ===")
    print(f"Client ID: {CLIENT_ID}")
    print(f"User ID: {USER_ID}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Get token
    token = get_bearer_token(BASE_URL, USER_ID, CLIENT_ID, CLIENT_SECRET)
    
    if token:
        print(f"\nToken obtained: {token[:20]}...")
        
        # Test various endpoints
        test_api_endpoints(BASE_URL, token)
        
        print("\n✓ Test completed!")
    else:
        print("\n✗ Failed to authenticate")

if __name__ == "__main__":
    main()