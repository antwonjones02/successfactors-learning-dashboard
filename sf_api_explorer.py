#!/usr/bin/env python3
"""
SuccessFactors Learning API Explorer
Explore and retrieve data from the sandbox environment
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

class SuccessFactorsAPI:
    def __init__(self):
        self.client_id = os.getenv("SF_CLIENT_ID")
        self.client_secret = os.getenv("SF_CLIENT_SECRET")
        self.user_id = os.getenv("SF_USER_ID")
        self.base_url = os.getenv("SF_BASE_URL")
        self.access_token = None
        
    def authenticate(self):
        """Get OAuth token"""
        token_url = f"{self.base_url}/learning/oauth-api/rest/v1/token"
        
        payload = {
            "grant_type": "client_credentials",
            "scope": {
                "userId": self.user_id,
                "companyId": self.client_id,
                "userType": "admin",
                "resourceType": "learning_public_api"
            },
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {"Content-Type": "application/json"}
        
        print(f"Authenticating...")
        response = requests.post(token_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            print("✓ Authentication successful!")
            return True
        else:
            print(f"✗ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def make_request(self, endpoint, params=None):
        """Make authenticated API request"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text[:200]}")
            return None
    
    def explore_endpoint(self, endpoint, name):
        """Explore an endpoint and show available data"""
        print(f"\n{'='*60}")
        print(f"Exploring: {name}")
        print(f"Endpoint: {endpoint}")
        print('='*60)
        
        data = self.make_request(endpoint)
        
        if data:
            if 'value' in data:
                records = data['value']
                print(f"✓ Found {len(records)} records")
                
                if len(records) > 0:
                    print(f"\nFirst record structure:")
                    first_record = records[0]
                    for key in list(first_record.keys())[:10]:  # Show first 10 fields
                        value = first_record[key]
                        print(f"  - {key}: {value}")
                    
                    if len(first_record.keys()) > 10:
                        print(f"  ... and {len(first_record.keys()) - 10} more fields")
                    
                    # Return DataFrame for further analysis
                    return pd.DataFrame(records)
                else:
                    print("No records found (empty dataset)")
            else:
                print("Response structure:")
                print(json.dumps(data, indent=2)[:500])
        else:
            print("✗ No data returned")
        
        return None
    
    def search_users(self, search_term=None):
        """Search for users"""
        endpoint = "/learning/odatav4/public/admin/searchStudent/v1"
        
        if search_term:
            # Try with filter
            endpoint += f"?$filter=contains(userName,'{search_term}')"
        
        return self.explore_endpoint(endpoint, "User Search")
    
    def get_learning_history(self):
        """Get learning history"""
        endpoints = [
            # Try different variations
            "/learning/odatav4/public/user/learningHistory/v1",
            "/learning/odatav4/public/admin/learningHistory/v1",
            "/learning/odatav4/public/user/learning-history/v1"
        ]
        
        for endpoint in endpoints:
            df = self.explore_endpoint(endpoint, f"Learning History ({endpoint})")
            if df is not None and len(df) > 0:
                return df
        
        return None
    
    def get_learning_events(self):
        """Get learning events"""
        endpoints = [
            "/learning/odatav4/public/admin/learningEvent/v1",
            "/learning/odatav4/public/user/learningEvent/v1"
        ]
        
        for endpoint in endpoints:
            df = self.explore_endpoint(endpoint, f"Learning Events ({endpoint})")
            if df is not None and len(df) > 0:
                return df
        
        return None
    
    def get_curriculum(self):
        """Get curriculum data"""
        endpoint = "/learning/odatav4/public/user/curriculum/v1"
        return self.explore_endpoint(endpoint, "Curriculum")
    
    def get_all_users(self):
        """Get all users"""
        endpoints = [
            "/learning/odatav4/public/admin/user-service/v1",
            "/learning/odatav4/public/admin/user-service/v2"
        ]
        
        for endpoint in endpoints:
            df = self.explore_endpoint(endpoint, f"Users ({endpoint})")
            if df is not None and len(df) > 0:
                return df
        
        return None
    
    def save_data(self, data_dict):
        """Save retrieved data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for name, df in data_dict.items():
            if df is not None and len(df) > 0:
                filename = f"sf_data_{name}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                print(f"✓ Saved {len(df)} records to {filename}")

def main():
    print("=== SuccessFactors Learning API Explorer ===\n")
    
    api = SuccessFactorsAPI()
    
    if not api.authenticate():
        print("Failed to authenticate. Exiting.")
        return
    
    # Collect all available data
    data_collection = {}
    
    # Try to get learning history
    print("\n" + "="*60)
    print("SEARCHING FOR LEARNING DATA...")
    print("="*60)
    
    data_collection['learning_history'] = api.get_learning_history()
    data_collection['learning_events'] = api.get_learning_events()
    data_collection['curriculum'] = api.get_curriculum()
    data_collection['users'] = api.get_all_users()
    
    # Try user search
    data_collection['user_search'] = api.search_users()
    
    # Summary
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    
    total_records = 0
    for name, df in data_collection.items():
        if df is not None and len(df) > 0:
            print(f"✓ {name}: {len(df)} records")
            total_records += len(df)
        else:
            print(f"✗ {name}: No data")
    
    print(f"\nTotal records found: {total_records}")
    
    # Save data if any found
    if total_records > 0:
        print("\nSaving data to CSV files...")
        api.save_data(data_collection)
    
    # If we found data, show some statistics
    if data_collection['learning_history'] is not None and len(data_collection['learning_history']) > 0:
        df = data_collection['learning_history']
        print("\n" + "="*60)
        print("LEARNING HISTORY STATISTICS")
        print("="*60)
        
        # Show column names
        print(f"Available columns: {', '.join(df.columns[:10])}")
        if len(df.columns) > 10:
            print(f"... and {len(df.columns) - 10} more columns")
        
        # Basic stats
        print(f"\nTotal records: {len(df)}")
        
        # Check for common fields
        if 'status' in df.columns:
            print("\nStatus distribution:")
            print(df['status'].value_counts())
        
        if 'completionDate' in df.columns:
            print(f"\nDate range: {df['completionDate'].min()} to {df['completionDate'].max()}")

if __name__ == "__main__":
    main()