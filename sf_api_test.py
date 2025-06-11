import requests
import base64
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SuccessFactorsAPI:
    def __init__(self, client_id=None, client_secret=None, base_url=None, token_url=None):
        self.client_id = client_id or os.getenv('SF_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SF_CLIENT_SECRET')
        self.base_url = base_url or os.getenv('SF_BASE_URL', 'https://api.successfactors.com')
        
        # Allow custom token URL or try common patterns
        if token_url:
            self.token_url = token_url
        elif os.getenv('SF_TOKEN_URL'):
            self.token_url = os.getenv('SF_TOKEN_URL')
        else:
            # Try different possible OAuth endpoints
            self.token_endpoints = [
                f"{self.base_url}/oauth/token",
                f"{self.base_url}/learning/oauth-api/rest/v1/token",
                f"{self.base_url}/oauth/api/v1/token",
                f"{self.base_url.replace('https://', 'https://api.')}/oauth/token" if not self.base_url.startswith('https://api.') else None,
                f"{self.base_url}/v2/oauth/token"
            ]
            self.token_endpoints = [url for url in self.token_endpoints if url]  # Remove None values
            self.token_url = self.token_endpoints[0]  # Start with first option
        
        self.access_token = None
        self.token_expiry = None
    
    def authenticate(self):
        """Authenticate with SuccessFactors using OAuth 2.0"""
        print("Authenticating with SuccessFactors...")
        
        # Try multiple token endpoints if we have them
        endpoints_to_try = [self.token_url]
        if hasattr(self, 'token_endpoints'):
            endpoints_to_try = self.token_endpoints
        
        for endpoint in endpoints_to_try:
            try:
                print(f"Trying OAuth endpoint: {endpoint}")
                
                # Different endpoints might expect different formats
                if 'learning/oauth-api' in endpoint:
                    # This endpoint expects JSON format (based on Skillsoft example)
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    payload = {
                        'grant_type': 'client_credentials',
                        'scope': {
                            'userId': os.getenv('SF_USER_ID', '00780606'),
                            'companyId': self.client_id,  # Use client_id as company_id
                            'userType': 'admin',  # Changed from 'user' to 'admin'
                            'resourceType': 'learning_public_api'
                        },
                        'client_id': self.client_id,
                        'client_secret': self.client_secret
                    }
                    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
                else:
                    # Standard OAuth with Basic Auth
                    credentials = f"{self.client_id}:{self.client_secret}"
                    encoded_credentials = base64.b64encode(credentials.encode()).decode()
                    headers = {
                        'Authorization': f'Basic {encoded_credentials}',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    data = {
                        'grant_type': 'client_credentials',
                        'scope': 'api'
                    }
                    response = requests.post(endpoint, headers=headers, data=data, timeout=30)
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = datetime.now().timestamp() + expires_in
                
                self.token_url = endpoint  # Save the working endpoint
                print(f"✓ Authentication successful using endpoint: {endpoint}")
                return True
                
            except requests.exceptions.RequestException as e:
                print(f"✗ Failed with endpoint {endpoint}: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(f"Response: {e.response.text[:500]}...")
        
        print("\n✗ Authentication failed with all endpoints")
        print("\nPlease check:")
        print("1. Your client ID and secret are correct")
        print("2. Your base URL is correct (e.g., https://your-instance.successfactors.com)")
        print("3. You may need to specify the exact OAuth token URL")
        return False
    
    def is_token_valid(self):
        """Check if the current token is still valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now().timestamp() < self.token_expiry
    
    def make_api_request(self, endpoint, method='GET', params=None):
        """Make an authenticated API request"""
        if not self.is_token_valid():
            if not self.authenticate():
                return None
        
        # Use OData v4 format for Learning endpoints
        if '/learning/' not in endpoint:
            endpoint = f"/learning/odatav4/public{endpoint}"
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text[:500]}...")
            return None
    
    def test_connection(self):
        """Test the API connection with a simple request"""
        print("\nTesting API connection...")
        
        # Try to get user learning history without any parameters
        endpoint = "/user/learningHistory/v1"
        
        result = self.make_api_request(endpoint)
        
        if result:
            print("✓ Connection test successful!")
            print(f"Sample response: {json.dumps(result, indent=2)[:500]}...")
            return True
        else:
            print("✗ Connection test failed!")
            return False
    
    def get_learning_events(self, limit=10):
        """Retrieve learning events"""
        print(f"\nRetrieving learning events (limit: {limit})...")
        
        endpoint = "/user/learningEvent/v1"
        params = {
            '$top': limit
        }
        
        result = self.make_api_request(endpoint, params=params)
        
        if result and 'value' in result:
            events = result['value']
            print(f"✓ Retrieved {len(events)} learning events")
            for event in events[:3]:  # Show first 3
                print(f"  - {event.get('eventName', 'N/A')} ({event.get('eventType', 'N/A')})")
            return events
        else:
            print("✗ Failed to retrieve learning events")
            return []
    
    def get_user_learning_history(self, user_id=None, limit=10):
        """Retrieve user learning history"""
        print(f"\nRetrieving learning history...")
        
        endpoint = "/user/learningHistory/v1"
        params = {
            '$top': limit
        }
        
        if user_id:
            params['$filter'] = f"userId eq '{user_id}'"
        
        result = self.make_api_request(endpoint, params=params)
        
        if result and 'value' in result:
            history = result['value']
            print(f"✓ Retrieved {len(history)} learning history records")
            for record in history[:3]:  # Show first 3
                print(f"  - {record.get('itemTitle', 'N/A')} - Status: {record.get('status', 'N/A')}")
            return history
        else:
            print("✗ Failed to retrieve learning history")
            return []


def main():
    print("=== SuccessFactors Learning API Test ===\n")
    
    # Check for credentials
    if not all([os.getenv('SF_CLIENT_ID'), os.getenv('SF_CLIENT_SECRET')]):
        print("Please set the following environment variables:")
        print("  - SF_CLIENT_ID: Your SuccessFactors Client ID")
        print("  - SF_CLIENT_SECRET: Your SuccessFactors Client Secret")
        print("  - SF_BASE_URL: Your SuccessFactors API Base URL (optional)")
        print("\nExample:")
        print("  export SF_CLIENT_ID='your-client-id'")
        print("  export SF_CLIENT_SECRET='your-client-secret'")
        print("  export SF_BASE_URL='https://api.successfactors.com'")
        
        # For testing, allow manual input
        print("\nOr enter credentials now for testing:")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        base_url = input("Base URL (press Enter for default): ").strip()
        
        if client_id and client_secret:
            api = SuccessFactorsAPI(client_id, client_secret, base_url if base_url else None)
        else:
            return
    else:
        api = SuccessFactorsAPI()
    
    # Test authentication
    if api.authenticate():
        # Test connection
        api.test_connection()
        
        # Get some sample data
        api.get_learning_events(limit=5)
        api.get_user_learning_history(limit=5)
        
        print("\n✓ API test completed successfully!")
    else:
        print("\n✗ API test failed - check your credentials and try again")


if __name__ == "__main__":
    main()