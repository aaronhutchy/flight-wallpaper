"""
Fetch flight data from OpenSky Network API
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class OpenSkyFetcher:
    """Handles fetching flight data from OpenSky Network API"""
    
    BASE_URL = "https://opensky-network.org/api"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.auth = (username, password) if username and password else None
        self.session = requests.Session()
        
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
                response = self.session.get(url, params=params, auth=self.auth, timeout=30)
                
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


def save_flight_data(flights: List[Dict], filename: str):
    """Save flight data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(flights, f, indent=2)
    print(f"Saved {len(flights)} flight states to {filename}")


def load_flight_data(filename: str) -> List[Dict]:
    """Load flight data from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)