"""
Generate wallpapers from your test data
"""
import json
from pathlib import Path
from generate_image import WallpaperGenerator
from process_data import FlightProcessor

print("=" * 60)
print("Testing with your captured flight data")
print("=" * 60)

# Load your test data
with open('your_test_data.json', 'r') as f:
    flights = json.load(f)

print(f"\nLoaded {len(flights)} flight records")

# Configuration
config = {'radius_miles': 5.0}
home_lat = 53.192780
home_lon = -0.469602

# Process flights
print("\nProcessing flight data...")
processor = FlightProcessor(home_lat, home_lon, config['radius_miles'])
approaches = processor.process_flights(flights)
stats = processor.get_statistics(approaches)

print(f"  Found {stats['total_aircraft']} unique aircraft")
print(f"  Closest: {stats['closest_distance']:.2f} miles")
print(f"  Avg altitude: {stats['average_altitude']:,.0f} ft")

# Generate wallpapers
print("\nGenerating wallpapers...")
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

output_file = output_dir / 'test_wallpaper.png'

generator = WallpaperGenerator(config)

# Generate all versions
generator.create_wallpaper(home_lat, home_lon, approaches, stats, str(output_file))
generator.create_landscape_wallpaper(home_lat, home_lon, approaches, stats, str(output_file))
generator.create_artistic_wallpaper(home_lat, home_lon, approaches, stats, str(output_file))

print()
print("=" * 60)
print("✓ Complete!")
print("=" * 60)
print("\nYour test wallpapers are ready:")
print(f"  Portrait PNG: output/test_wallpaper.png")
print(f"  Portrait JPG: output/test_wallpaper.jpg")
print(f"  Landscape JPG: output/test_wallpaper_landscape.jpg")
print(f"  Artistic JPG: output/test_wallpaper_artistic.jpg")
print()