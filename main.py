#!/usr/bin/env python3
"""
Flight Wallpaper Generator - Main Entry Point
"""
import yaml
import sys
import argparse
from datetime import datetime
from pathlib import Path

from process_data import FlightProcessor, miles_to_degrees
from generate_image import WallpaperGenerator
from demo_data import generate_sample_flights, create_sample_scenario


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_path}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}")
        sys.exit(1)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate flight wallpaper')
    parser.add_argument('--demo', action='store_true', help='Use demo data instead of fetching from API')
    parser.add_argument('--scenario', default='normal', choices=['normal', 'busy', 'quiet', 'overnight'],
                       help='Demo scenario (only with --demo)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Flight Wallpaper Generator")
    if args.demo:
        print("(DEMO MODE - Using Sample Data)")
    print("=" * 60)
    print()
    
    print("Loading configuration...")
    config = load_config()
    
    home_lat = config['home_location']['lat']
    home_lon = config['home_location']['lon']
    radius_miles = config['radius_miles']
    
    print(f"  Home: ({home_lat}, {home_lon})")
    print(f"  Radius: {radius_miles} miles")
    print()
    
    if args.demo:
        print(f"Generating sample flight data (scenario: {args.scenario})...")
        flights = create_sample_scenario(home_lat, home_lon, radius_miles, args.scenario)
        print()
    else:
        print("Initializing API client...")
        
        # Try FlightRadar24 first (better coverage)
        fr24_config = config.get('flightradar24', {})
        if fr24_config.get('enabled') and fr24_config.get('api_key'):
            print("  Using FlightRadar24 API")
            from fetch_flights import FlightRadar24Fetcher
            fetcher = FlightRadar24Fetcher(fr24_config['api_key'])
        else:
            # Fall back to OpenSky
            print("  Using OpenSky Network API")
            from fetch_flights import OpenSkyFetcher
            client_id = config.get('opensky', {}).get('client_id')
            client_secret = config.get('opensky', {}).get('client_secret')
            fetcher = OpenSkyFetcher(client_id, client_secret)
        
        print()
        print("Fetching flight data...")
        print("  This may take a few minutes...\n")
        
        radius_degrees = miles_to_degrees(radius_miles, home_lat)
        
        try:
            flights = fetcher.get_yesterday_flights(home_lat, home_lon, radius_degrees)
        except Exception as e:
            print(f"\n✗ Error fetching flights: {e}")
            print("\nTip: Use '--demo' flag to test:")
            print("  python main.py --demo")
            sys.exit(1)
        
        # Save flight data
        from fetch_flights import save_flight_data
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        data_file = data_dir / f'flights_{timestamp}.json'
        save_flight_data(flights, str(data_file))
        print()
    
    # Process flights
    print("Processing flight data...")
    processor = FlightProcessor(home_lat, home_lon, radius_miles)
    approaches = processor.process_flights(flights)
    stats = processor.get_statistics(approaches)
    print()
    
    # Print statistics
    print("Statistics:")
    print(f"  Total aircraft: {stats['total_aircraft']}")
    if stats['total_aircraft'] > 0:
        print(f"  Closest approach: {stats['closest_distance']:.2f} miles")
        print(f"  Furthest: {stats['furthest_distance']:.2f} miles")
        print(f"  Average distance: {stats['average_distance']:.2f} miles")
        if stats['average_altitude']:
            print(f"  Altitude range: {stats['min_altitude']:,.0f} - {stats['max_altitude']:,.0f} ft")
            print(f"  Average altitude: {stats['average_altitude']:,.0f} ft")
    print()
    
    # Generate wallpaper
    print("Generating wallpaper...")
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    suffix = '_demo' if args.demo else ''
    output_file = output_dir / f'wallpaper_{timestamp}{suffix}.png'
    
    generator = WallpaperGenerator(config)
    generator.create_wallpaper(home_lat, home_lon, approaches, stats, str(output_file))
    
    print()
    print("=" * 60)
    print("✓ Complete!")
    print("=" * 60)
    print(f"\nYour wallpaper is ready: {output_file}")
    if args.demo:
        print("\nThis was generated with sample data.")
        print("To use real flight data, run without --demo flag:")
        print("  python main.py")
    print("\nNext steps:")
    print("  1. View the image in the output/ directory")
    print("  2. Set it as your desktop wallpaper")
    print("  3. Run this script daily for fresh wallpapers!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)