#!/usr/bin/env python3
"""
SuccessFactors Data Finder
Comprehensive search for data in the sandbox
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SFDataFinder:
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
        
        response = requests.post(token_url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("✓ Authenticated successfully")
            return True
        return False
    
    def test_endpoint(self, endpoint, method="GET", data=None):
        """Test an endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            return response.status_code, response.text
        except Exception as e:
            return None, str(e)
    
    def find_data(self):
        """Try various endpoint patterns to find data"""
        print("\n" + "="*60)
        print("SEARCHING FOR DATA IN SUCCESSFACTORS SANDBOX")
        print("="*60)
        
        # Common endpoint patterns
        base_paths = [
            "/learning/odatav4/public",
            "/learning/odatav4/restricted",
            "/learning/odata/v4",
            "/learning/odata",
            "/odata/v2",
            "/odata/v4",
            "/learning/public/v1",
            "/learning/admin/v1"
        ]
        
        resource_types = [
            "learningHistory",
            "learning-history",
            "LearningHistory",
            "learning_history",
            "userLearning",
            "user-learning",
            "UserLearning",
            "learningEvent",
            "learning-event",
            "LearningEvent",
            "learning_event",
            "itemAssignment",
            "item-assignment",
            "ItemAssignment",
            "curriculum",
            "Curriculum",
            "certification",
            "Certification",
            "student",
            "Student",
            "users",
            "Users",
            "completions",
            "Completions"
        ]
        
        # Test combinations
        found_data = []
        
        for base in base_paths:
            for resource in resource_types:
                # Try different patterns
                endpoints = [
                    f"{base}/{resource}",
                    f"{base}/user/{resource}",
                    f"{base}/admin/{resource}",
                    f"{base}/{resource}/v1",
                    f"{base}/user/{resource}/v1",
                    f"{base}/admin/{resource}/v1"
                ]
                
                for endpoint in endpoints:
                    status, response = self.test_endpoint(endpoint)
                    
                    if status == 200:
                        try:
                            data = json.loads(response)
                            if 'value' in data and len(data['value']) > 0:
                                print(f"\n✓ FOUND DATA at {endpoint}")
                                print(f"  Records: {len(data['value'])}")
                                print(f"  First record: {json.dumps(data['value'][0], indent=2)[:200]}...")
                                found_data.append({
                                    'endpoint': endpoint,
                                    'count': len(data['value']),
                                    'sample': data['value'][0]
                                })
                            elif 'value' not in data and data:
                                # Check if it's a different format
                                print(f"\n? Different format at {endpoint}")
                                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                        except:
                            pass
        
        # Try specific known endpoints from the Skillsoft example
        print("\n" + "-"*60)
        print("Testing specific endpoints from examples...")
        print("-"*60)
        
        specific_endpoints = [
            "/learning/odatav4/public/admin/learningEvent/v1/recordLearningEvents",
            "/learning/odatav4/public/admin/learningHistory/v1",
            "/learning/odatav4/public/admin/user/v1",
            "/learning/odatav4/public/admin/searchStudent/v1",
            "/learning/odatav4/public/user/userlearning-service/v1",
            "/learning/odatav4/public/user/learningplan-service/v1",
            "/learning/odatav4/public/user/curriculum/v1",
            "/learning/odatav4/public/user/itemAssignment/v1"
        ]
        
        for endpoint in specific_endpoints:
            status, response = self.test_endpoint(endpoint)
            print(f"\n{endpoint}:")
            print(f"  Status: {status}")
            if status == 200:
                try:
                    data = json.loads(response)
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"  Response: {response[:300]}...")
        
        # Try with the specific user ID
        print("\n" + "-"*60)
        print(f"Testing user-specific endpoints for user {self.user_id}...")
        print("-"*60)
        
        user_endpoints = [
            f"/learning/odatav4/public/user/learningHistory/v1?userId={self.user_id}",
            f"/learning/odatav4/public/user/learningHistory/v1?$filter=userId eq '{self.user_id}'",
            f"/learning/odatav4/public/admin/searchStudent/v1?userId={self.user_id}",
            f"/learning/odatav4/public/admin/user/v1/{self.user_id}"
        ]
        
        for endpoint in user_endpoints:
            status, response = self.test_endpoint(endpoint)
            print(f"\n{endpoint}:")
            print(f"  Status: {status}")
            if status == 200:
                try:
                    data = json.loads(response)
                    print(f"  Response: {json.dumps(data, indent=2)[:300]}...")
                except:
                    print(f"  Response: {response[:300]}...")
        
        return found_data

def main():
    finder = SFDataFinder()
    
    if finder.authenticate():
        found_data = finder.find_data()
        
        if found_data:
            print("\n" + "="*60)
            print("SUMMARY OF FOUND DATA")
            print("="*60)
            for item in found_data:
                print(f"\nEndpoint: {item['endpoint']}")
                print(f"Records: {item['count']}")
                print(f"Sample fields: {', '.join(list(item['sample'].keys())[:5])}")
        else:
            print("\n✗ No data found in any endpoints tested")
    else:
        print("✗ Authentication failed")

if __name__ == "__main__":
    main()