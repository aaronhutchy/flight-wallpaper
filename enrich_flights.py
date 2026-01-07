"""
Enrich flight data with origin and destination information
"""
import requests
import time
from typing import List, Dict


def enrich_with_routes(approaches: List[Dict], api_key: str) -> List[Dict]:
    """
    Enrich flight approaches with origin and destination airport codes
    Makes additional API calls to FlightRadar24 for flight details
    """
    if not approaches:
        return approaches
    
    print(f"Fetching route details for {len(approaches)} flights...")
    enriched = []
    
    for i, approach in enumerate(approaches, 1):
        callsign = approach.get('callsign')
        
        if not callsign:
            # No callsign, can't look up route
            enriched.append(approach)
            continue
        
        try:
            # Fetch flight details from FR24 API
            print(f"  [{i}/{len(approaches)}] Looking up {callsign}...", end=' ')
            
            origin, destination = _fetch_flight_route(callsign, api_key)
            
            if origin or destination:
                approach['origin'] = origin
                approach['destination'] = destination
                print(f"✓ {origin or '?'} → {destination or '?'}")
            else:
                print("✗ No route data")
            
            enriched.append(approach)
            
            # Rate limiting - don't hammer the API
            if i < len(approaches):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error: {e}")
            enriched.append(approach)
    
    print()
    return enriched


def _fetch_flight_route(callsign: str, api_key: str) -> tuple:
    """
    Fetch origin and destination for a specific flight
    Returns: (origin_code, destination_code) or (None, None)
    """
    # FlightRadar24 API endpoint for flight details
    url = "https://fr24api.flightradar24.com/api/live/flight-positions/full"
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {api_key}"
    }
    
    params = {
        "callsign": callsign.strip()
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # FR24 API structure: data might be in different places depending on endpoint
            # Try to extract origin/destination from response
            if isinstance(data, dict):
                # Check for flight data in response
                flights = data.get('data', [])
                
                if flights and len(flights) > 0:
                    flight = flights[0]
                    
                    # Extract airport codes
                    origin = flight.get('airport', {}).get('origin', {}).get('code', {}).get('iata')
                    destination = flight.get('airport', {}).get('destination', {}).get('code', {}).get('iata')
                    
                    # Fallback to ICAO codes if IATA not available
                    if not origin:
                        origin = flight.get('airport', {}).get('origin', {}).get('code', {}).get('icao')
                    if not destination:
                        destination = flight.get('airport', {}).get('destination', {}).get('code', {}).get('icao')
                    
                    return (origin, destination)
        
        return (None, None)
        
    except Exception as e:
        # Silently fail for individual flights
        return (None, None)