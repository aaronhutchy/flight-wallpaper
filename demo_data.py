"""
Generate sample flight data for demonstration purposes
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict


def generate_sample_flights(
    home_lat: float,
    home_lon: float,
    radius_miles: float,
    num_aircraft: int = 20
) -> List[Dict]:
    """Generate realistic sample flight data"""
    flights = []
    
    # Typical callsign prefixes
    airlines = ['BAW', 'AAL', 'UAL', 'DAL', 'EZY', 'RYR', 'DLH', 'AFR', 'KLM', 'SWA']
    
    # Yesterday's time range
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    
    # Convert miles to degrees (approximate)
    radius_degrees = radius_miles / 69.0
    
    for i in range(num_aircraft):
        # Generate a unique aircraft
        icao24 = f"{random.randint(100000, 999999):06x}"
        airline = random.choice(airlines)
        flight_num = random.randint(1, 9999)
        callsign = f"{airline}{flight_num}"
        
        # Generate flight path
        num_observations = random.randint(5, 15)
        
        # Random entry/exit points
        entry_angle = random.uniform(0, 2 * math.pi)
        exit_angle = entry_angle + math.pi + random.uniform(-0.5, 0.5)
        
        # Random altitude (in meters)
        altitude = random.randint(3000, 12000)
        
        # Random time during the day
        flight_start = start_time + timedelta(
            seconds=random.randint(0, int((end_time - start_time).total_seconds()))
        )
        
        # Generate observations along the path
        for j in range(num_observations):
            progress = j / (num_observations - 1)
            
            current_angle = entry_angle + (exit_angle - entry_angle) * progress
            distance = radius_degrees * random.uniform(0.3, 1.2)
            
            lat = home_lat + distance * math.sin(current_angle)
            lon = home_lon + distance * math.cos(current_angle)
            
            # Add some noise
            lat += random.gauss(0, 0.005)
            lon += random.gauss(0, 0.005)
            
            current_altitude = altitude + random.gauss(0, 200)
            
            timestamp = int((flight_start + timedelta(seconds=j * 30)).timestamp())
            
            flights.append({
                'icao24': icao24,
                'callsign': callsign,
                'origin_country': random.choice(['United States', 'United Kingdom', 'Germany', 'France']),
                'timestamp': timestamp,
                'longitude': lon,
                'latitude': lat,
                'altitude': current_altitude,
                'on_ground': False,
                'velocity': random.uniform(200, 250),
                'heading': math.degrees(current_angle) % 360,
                'vertical_rate': random.gauss(0, 2),
                'geo_altitude': current_altitude
            })
    
    print(f"Generated {len(flights)} sample flight states for {num_aircraft} aircraft")
    return flights


def create_sample_scenario(home_lat: float, home_lon: float, radius_miles: float, scenario: str = 'normal') -> List[Dict]:
    """Create different sample scenarios"""
    if scenario == 'busy':
        return generate_sample_flights(home_lat, home_lon, radius_miles, num_aircraft=35)
    elif scenario == 'quiet':
        return generate_sample_flights(home_lat, home_lon, radius_miles, num_aircraft=5)
    elif scenario == 'overnight':
        flights = generate_sample_flights(home_lat, home_lon, radius_miles, num_aircraft=8)
        for flight in flights:
            flight['altitude'] = flight['altitude'] * 1.5
        return flights
    else:
        return generate_sample_flights(home_lat, home_lon, radius_miles, num_aircraft=20)