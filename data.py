"""
Process flight data: filter by radius and find closest approaches
"""
from typing import List, Dict
from geopy.distance import geodesic
from collections import defaultdict
import math


class FlightProcessor:
    """Process and filter flight data"""
    
    def __init__(self, home_lat: float, home_lon: float, radius_miles: float):
        self.home = (home_lat, home_lon)
        self.radius_miles = radius_miles
        
    def calculate_distance(self, lat: float, lon: float) -> float:
        """Calculate distance from home to a point"""
        if lat is None or lon is None:
            return float('inf')
        point = (lat, lon)
        return geodesic(self.home, point).miles
    
    def filter_by_radius(self, flights: List[Dict]) -> List[Dict]:
        """Filter flights to only those within radius"""
        filtered = []
        
        for flight in flights:
            if flight['latitude'] is None or flight['longitude'] is None:
                continue
                
            distance = self.calculate_distance(flight['latitude'], flight['longitude'])
            
            if distance <= self.radius_miles:
                flight['distance_to_home'] = distance
                filtered.append(flight)
        
        print(f"Filtered {len(filtered)} states within {self.radius_miles} miles")
        return filtered
    
    def group_by_aircraft(self, flights: List[Dict]) -> Dict[str, List[Dict]]:
        """Group flight states by aircraft"""
        grouped = defaultdict(list)
        
        for flight in flights:
            grouped[flight['icao24']].append(flight)
        
        for icao24 in grouped:
            grouped[icao24].sort(key=lambda x: x['timestamp'])
        
        return dict(grouped)
    
    def find_closest_approach(self, flight_states: List[Dict]) -> Dict:
        """Find the closest approach point for an aircraft"""
        if not flight_states:
            return None
        
        closest = min(flight_states, key=lambda x: x.get('distance_to_home', float('inf')))
        
        result = closest.copy()
        result['num_observations'] = len(flight_states)
        result['first_seen'] = min(s['timestamp'] for s in flight_states)
        result['last_seen'] = max(s['timestamp'] for s in flight_states)
        
        return result
    
    def process_flights(self, flights: List[Dict]) -> List[Dict]:
        """Complete processing pipeline"""
        print(f"\nProcessing {len(flights)} flight states...")
        
        within_radius = self.filter_by_radius(flights)
        
        if not within_radius:
            print("No flights found within radius")
            return []
        
        grouped = self.group_by_aircraft(within_radius)
        print(f"Found {len(grouped)} unique aircraft")
        
        closest_approaches = []
        for icao24, states in grouped.items():
            closest = self.find_closest_approach(states)
            if closest:
                closest_approaches.append(closest)
        
        closest_approaches.sort(key=lambda x: x['distance_to_home'])
        
        print(f"Identified {len(