"""
Fetch flight data from OpenSky Network API with OAuth2 support
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class OpenSkyFetcher:
    """Handles fetching flight data from OpenSky Network API"""
    
    BASE_URL = "https://opensky-network.org/api"
    TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the OpenSky API client
        
        Args:
            client_id: OAuth2 client ID (for new accounts)
            client_secret: OAuth2 client secret (for new accounts)
            username: Username (legacy accounts only)
            password: Password (legacy accounts only)
        """
        self.session = requests.Session()
        self.access_token = None
        
        # Try OAuth2 first (new authentication method)
        if client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret
            self._get_oauth_token()
        # Fall back to basic auth (legacy)
        elif username and password:
            self.session.auth = (username, password)
        
    def _get_oauth_token(self):
        """Get OAuth2 access token"""
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                print("  ✓ OAuth2 authentication successful")
            else:
                print(f"  ✗ OAuth2 authentication failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ OAuth2 token request failed: {e}")
    
    def _make_request(self, url, params):
        """Make authenticated request"""
        headers = {}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            
        return self.session.get(url, params=params, headers=headers, timeout=30)
        
    def get_flights_in_timerange(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        begin_time: int,
        end_time: int
    ) -> List[Dict]:
        """Fetch all flights in a bounding box for a given time range"""
        url = f"{self.BASE_URL}/states/all"
        flights = []
        chunk_size = 600  # 10 minutes
        current_time = begin_time
        
        print(f"Fetching flight data from {datetime.fromtimestamp(begin_time)} to {datetime.fromtimestamp(end_time)}")
        
        while current_time < end_time:
            params = {
                'time': current_time,
                'lamin': lat_min,
                'lamax': lat_max,
                'lomin': lon_min,
                'lomax': lon_max
            }
            
            try:
                response = self._make_request(url, params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data and 'states' in data and data['states']:
                        for state in data['states']:
                            flights.append(self._parse_state_vector(state, current_time))
                        print(f"  ✓ Fetched {len(data['states'])} states at {datetime.fromtimestamp(current_time)}")
                    else:
                        print(f"  - No flights at {datetime.fromtimestamp(current_time)}")
                elif response.status_code == 404:
                    print(f"  - No data available for {datetime.fromtimestamp(current_time)}")
                else:
                    print(f"  ✗ Error {response.status_code} at {datetime.fromtimestamp(current_time)}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request failed: {e}")
            
            time.sleep(1)
            current_time += chunk_size
            
        print(f"Total states fetched: {len(flights)}")
        return flights
    
    def _parse_state_vector(self, state: List, timestamp: int) -> Dict:
        """Parse a state vector from OpenSky API"""
        return {
            'icao24': state[0],
            'callsign': state[1].strip() if state[1] else None,
            'origin_country': state[2],
            'timestamp': timestamp,
            'longitude': state[5],
            'latitude': state[6],
            'altitude': state[7],
            'on_ground': state[8],
            'velocity': state[9],
            'heading': state[10],
            'vertical_rate': state[11],
            'geo_altitude': state[13]
        }
    
    def get_yesterday_flights(self, center_lat: float, center_lon: float, radius_degrees: float) -> List[Dict]:
        """Convenience method to get yesterday's flights"""
        lat_min = center_lat - radius_degrees
        lat_max = center_lat + radius_degrees
        lon_min = center_lon - radius_degrees
        lon_max = center_lon + radius_degrees
        
        now = datetime.now()
        yesterday_start = now - timedelta(days=1)
        yesterday_start = yesterday_start.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday_start + timedelta(days=1)
        
        begin_time = int(yesterday_start.timestamp())
        end_time = int(yesterday_end.timestamp())
        
        return self.get_flights_in_timerange(lat_min, lat_max, lon_min, lon_max, begin_time, end_time)
    
    def get_current_flights(self, center_lat: float, center_lon: float, radius_degrees: float) -> List[Dict]:
        """Get current/live flights (no time parameter for current data)"""
        lat_min = center_lat - radius_degrees
        lat_max = center_lat + radius_degrees
        lon_min = center_lon - radius_degrees
        lon_max = center_lon + radius_degrees
        
        url = f"{self.BASE_URL}/states/all"
        
        params = {
            'lamin': lat_min,
            'lamax': lat_max,
            'lomin': lon_min,
            'lomax': lon_max
        }
        
        print("Fetching current/live flight data...")
        
        try:
            response = self._make_request(url, params)
            
            if response.status_code == 200:
                data = response.json()
                flights = []
                
                if data and 'states' in data and data['states']:
                    current_time = data.get('time', int(time.time()))
                    for state in data['states']:
                        flights.append(self._parse_state_vector(state, current_time))
                    print(f"  ✓ Fetched {len(flights)} current flight states")
                else:
                    print("  - No flights currently in the area")
                    
                return flights
            else:
                print(f"  ✗ Error {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request failed: {e}")
            return []


def save_flight_data(flights: List[Dict], filename: str):
    """Save flight data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(flights, f, indent=2)
    print(f"Saved {len(flights)} flight states to {filename}")


def load_flight_data(filename: str) -> List[Dict]:
    """Load flight data from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)