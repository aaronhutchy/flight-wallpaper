"""
Process flight data and calculate closest approaches
"""
import math
from typing import List, Dict, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles"""
    R = 3959  # Earth's radius in miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def miles_to_degrees(miles: float, latitude: float) -> float:
    """Convert miles to approximate degrees at given latitude"""
    lat_degrees = miles / 69.0
    lon_degrees = miles / (69.0 * math.cos(math.radians(latitude)))
    return max(lat_degrees, lon_degrees)


class FlightProcessor:
    """Process flight data and find closest approaches"""
    
    def __init__(self, home_lat: float, home_lon: float, radius_miles: float):
        self.home_lat = home_lat
        self.home_lon = home_lon
        self.radius_miles = radius_miles
    
    def process_flights(self, flights: List[Dict]) -> List[Dict]:
        """
        Process flights and find closest approach points
        Groups by ICAO24 and finds the point closest to home for each aircraft
        """
        # Group flights by aircraft
        aircraft_flights = {}
        for flight in flights:
            icao24 = flight.get('icao24')
            if not icao24:
                continue
            
            if icao24 not in aircraft_flights:
                aircraft_flights[icao24] = []
            aircraft_flights[icao24].append(flight)
        
        print(f"Processing {len(flights)} flight states...")
        print(f"Filtered {len(aircraft_flights)} states within {self.radius_miles} miles")
        print(f"Found {len(aircraft_flights)} unique aircraft")
        
        # Find closest approach for each aircraft
        approaches = []
        for icao24, aircraft_states in aircraft_flights.items():
            closest = self._find_closest_approach(aircraft_states)
            if closest:
                approaches.append(closest)
        
        print(f"Identified {len(approaches)} aircraft with closest approaches")
        return approaches
    
    def _find_closest_approach(self, states: List[Dict]) -> Dict:
        """Find the closest point to home for this aircraft"""
        closest_state = None
        closest_distance = float('inf')
        
        for state in states:
            lat = state.get('latitude')
            lon = state.get('longitude')
            
            if lat is None or lon is None:
                continue
            
            distance = haversine_distance(self.home_lat, self.home_lon, lat, lon)
            
            if distance < closest_distance and distance <= self.radius_miles:
                closest_distance = distance
                closest_state = state
        
        if closest_state is None:
            return None
        
        return {
            'icao24': closest_state['icao24'],
            'callsign': closest_state.get('callsign'),
            'latitude': closest_state['latitude'],
            'longitude': closest_state['longitude'],
            'altitude': closest_state.get('altitude'),
            'heading': closest_state.get('heading'),
            'velocity': closest_state.get('velocity'),
            'timestamp': closest_state.get('timestamp'),
            'distance': closest_distance
        }
    
    def get_statistics(self, approaches: List[Dict]) -> Dict:
        """Calculate statistics from approaches"""
        if not approaches:
            return {
                'total_aircraft': 0,
                'closest_distance': None,
                'furthest_distance': None,
                'average_distance': None,
                'min_altitude': None,
                'max_altitude': None,
                'average_altitude': None
            }
        
        distances = [a['distance'] for a in approaches]
        altitudes = []
        
        for a in approaches:
            if a['altitude'] is not None:
                # Convert meters to feet
                altitudes.append(a['altitude'] * 3.28084)
        
        stats = {
            'total_aircraft': len(approaches),
            'closest_distance': min(distances),
            'furthest_distance': max(distances),
            'average_distance': sum(distances) / len(distances)
        }
        
        if altitudes:
            stats['min_altitude'] = min(altitudes)
            stats['max_altitude'] = max(altitudes)
            stats['average_altitude'] = sum(altitudes) / len(altitudes)
        else:
            stats['min_altitude'] = None
            stats['max_altitude'] = None
            stats['average_altitude'] = None
        
        return stats