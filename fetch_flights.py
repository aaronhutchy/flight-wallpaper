"""
Fetch flight data from FlightRadar24 and OpenSky Network APIs
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class FlightRadar24Fetcher:
    """Fetch flight data from FlightRadar24 API"""
    
    BASE_URL = "https://fr24api.flightradar24.com/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Accept-Version': 'v1'
        })
    
    def get_historical_flights(
        self,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        begin_time: int,
        end_time: int
    ) -> List[Dict]:
        """Fetch historical flights in a bounding box"""
        
        url = f"{self.BASE_URL}/historic/flight-positions/full"
        
        # Build bounds parameter: north, south, west, east
        bounds = f"{lat_max},{lat_min},{lon_min},{lon_max}"
        
        print(f"Fetching FlightRadar24 data from {datetime.fromtimestamp(begin_time)} to {datetime.fromtimestamp(end_time)}")
        
        flights = []
        current_time = begin_time
        chunk_size = 900  # 15 minute chunks (was 3600 for hourly)
        
        while current_time < end_time:
            try:
                params = {
                    'timestamp': current_time,
                    'bounds': bounds
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and data['data']:
                        for flight in data['data']:
                            flights.append(self._parse_fr24_flight(flight))
                        print(f"  ✓ Fetched {len(data['data'])} states at {datetime.fromtimestamp(current_time)}")
                    else:
                        print(f"  - No flights at {datetime.fromtimestamp(current_time)}")
                        
                elif response.status_code == 404:
                    print(f"  - No data for {datetime.fromtimestamp(current_time)}")
                else:
                    print(f"  ✗ Error {response.status_code} at {datetime.fromtimestamp(current_time)}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request failed: {e}")
            
            time.sleep(6)  # Rate limiting - 10 requests per minute
            current_time += chunk_size
        
        print(f"Total FR24 states fetched: {len(flights)}")
        return flights
    
    def _parse_fr24_flight(self, flight: Dict) -> Dict:
        """Parse FR24 flight data - NOW WITH ORIGIN/DESTINATION"""
        return {
            'icao24': flight.get('hex'),
            'callsign': flight.get('callsign'),
            'origin_country': None,
            'timestamp': int(datetime.fromisoformat(flight['timestamp'].replace('Z', '+00:00')).timestamp()) if flight.get('timestamp') else None,
            'longitude': flight.get('lon'),
            'latitude': flight.get('lat'),
            'altitude': flight.get('alt') * 0.3048 if flight.get('alt') else None,  # feet to meters
            'on_ground': flight.get('alt', 0) == 0 if flight.get('alt') is not None else False,
            'velocity': flight.get('gspeed') * 0.514444 if flight.get('gspeed') else None,  # knots to m/s
            'heading': flight.get('track'),
            'vertical_rate': flight.get('vspeed') * 0.00508 if flight.get('vspeed') else None,  # ft/min to m/s
            'geo_altitude': flight.get('alt') * 0.3048 if flight.get('alt') else None,
            # ADDED: Extract origin/destination from FR24 API
            'origin_iata': flight.get('orig_iata'),
            'origin_icao': flight.get('orig_icao'),
            'destination_iata': flight.get('dest_iata'),
            'destination_icao': flight.get('dest_icao')
        }
    
    def get_yesterday_flights(self, center_lat: float, center_lon: float, radius_degrees: float) -> List[Dict]:
        """Get yesterday's flights"""
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
        
        return self.get_historical_flights(lat_min, lat_max, lon_min, lon_max, begin_time, end_time)


class OpenSkyFetcher:
    """Fetch flight data from OpenSky Network API"""
    
    BASE_URL = "https://opensky-network.org/api"
    TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.session = requests.Session()
        self.access_token = None
        
        if client_id and client_secret:
            self.client_id = client_id
            self.client_secret = client_secret
            self._get_oauth_token()
    
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
                print("  ✓ OpenSky OAuth2 authentication successful")
            else:
                print(f"  ✗ OpenSky OAuth2 failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ OpenSky OAuth2 failed: {e}")
    
    def _make_request(self, url, params):
        """Make authenticated request"""
        headers = {}
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return self.session.get(url, params=params, headers=headers, timeout=30)
    
    def get_yesterday_flights(self, center_lat: float, center_lon: float, radius_degrees: float) -> List[Dict]:
        """Get yesterday's flights from OpenSky"""
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
        
        url = f"{self.BASE_URL}/states/all"
        flights = []
        current_time = begin_time
        chunk_size = 600
        
        print(f"Fetching OpenSky data from {datetime.fromtimestamp(begin_time)} to {datetime.fromtimestamp(end_time)}")
        
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
                    print(f"  - No data for {datetime.fromtimestamp(current_time)}")
                else:
                    print(f"  ✗ Error {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ✗ Request failed: {e}")
            
            time.sleep(6)  # Rate limiting - 10 requests per minute = 6 second spacing
            current_time += chunk_size
        
        print(f"Total OpenSky states fetched: {len(flights)}")
        return flights
    
    def _parse_state_vector(self, state: List, timestamp: int) -> Dict:
        """Parse OpenSky state vector"""
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


def save_flight_data(flights: List[Dict], filename: str):
    """Save flight data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(flights, f, indent=2)
    print(f"Saved {len(flights)} flight states to {filename}")


def load_flight_data(filename: str) -> List[Dict]:
    """Load flight data from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)