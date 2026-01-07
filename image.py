"""
Generate wallpaper visualization from flight data
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from datetime import datetime
from typing import List, Dict
import numpy as np


class WallpaperGenerator:
    """Generate stylish wallpaper from flight data"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.width = config['image']['width']
        self.height = config['image']['height']
        self.bg_color = config['image']['background_color']
        self.home_color = config['image']['home_color']
        self.flight_color = config['image']['flight_color']
        self.text_color = config['image']['text_color']
        
    def create_wallpaper(self, home_lat: float, home_lon: float, approaches: List[Dict], stats: Dict, output_path: str):
        """Create the wallpaper image"""
        dpi = 100
        fig_width = self.width / dpi
        fig_height = self.height / dpi
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        
        if not approaches:
            self._create_empty_wallpaper(ax, home_lat, home_lon)
        else:
            self._create_flight_wallpaper(ax, home_lat, home_lon, approaches, stats)
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=dpi, facecolor=self.bg_color, edgecolor='none')
        plt.close()
        
        print(f"\n✓ Wallpaper saved to: {output_path}")
    
    def _create_flight_wallpaper(self, ax, home_lat: float, home_lon: float, approaches: List[Dict], stats: Dict):
        """Create wallpaper with flight data"""
        lats = [a['latitude'] for a in approaches if a['latitude']]
        lons = [a['longitude'] for a in approaches if a['longitude']]
        lats.append(home_lat)
        lons.append(home_lon)
        
        lat_margin = (max(lats) - min(lats)) * 0.2
        lon_margin = (max(lons) - min(lons)) * 0.2
        
        ax.set_xlim(min(lons) - lon_margin, max(lons) + lon_margin)
        ax.set_ylim(min(lats) - lat_margin, max(lats) + lat_margin)
        ax.set_aspect('equal')
        
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        circle = Circle((home_lon, home_lat), radius_degrees, fill=False, edgecolor=self.text_color, 
                       alpha=0.2, linewidth=1, linestyle='--')
        ax.add_patch(circle)
        
        ax.plot(home_lon, home_lat, marker='*', markersize=20, color=self.home_color, 
               zorder=1000, markeredgecolor='white', markeredgewidth=1)
        
        for approach in approaches:
            if approach['latitude'] is None or approach['longitude'] is None:
                continue
            
            lat = approach['latitude']
            lon = approach['longitude']
            
            ax.plot([home_lon, lon], [home_lat, lat], color=self.flight_color, 
                   alpha=0.3, linewidth=0.5, zorder=1)
            
            marker_size = self._get_marker_size(approach)
            ax.plot(lon, lat, marker='o', markersize=marker_size, color=self.flight_color, 
                   alpha=0.7, zorder=10, markeredgecolor=self.flight_color, markeredgewidth=0)
        
        self._add_text_info(ax, stats)
    
    def _create_empty_wallpaper(self, ax, home_lat: float, home_lon: float):
        """Create wallpaper when no flights found"""
        margin = 0.05
        ax.set_xlim(home_lon - margin, home_lon + margin)
        ax.set_ylim(home_lat - margin, home_lat + margin)
        ax.set_aspect('equal')
        
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        circle = Circle((home_lon, home_lat), radius_degrees, fill=False, edgecolor=self.text_color,
                       alpha=0.2, linewidth=1, linestyle='--')
        ax.add_patch(circle)
        
        ax.plot(home_lon, home_lat, marker='*', markersize=20, color=self.home_color,
               zorder=1000, markeredgecolor='white', markeredgewidth=1)
        
        ax.text(0.5, 0.95, 'No flights detected', transform=ax.transAxes, fontsize=28,
               color=self.text_color, ha='center', va='top', fontweight='light')
        
        ax.text(0.5, 0.88, 'within the search radius', transform=ax.transAxes, fontsize=16,
               color=self.text_color, ha='center', va='top', alpha=0.6)
    
    def _add_text_info(self, ax, stats: Dict):
        """Add title and statistics text"""
        yesterday = datetime.now().date()
        title = f"Flights Over My House"
        subtitle = f"{yesterday.strftime('%B %d, %Y')}"
        
        ax.text(0.5, 0.97, title, transform=ax.transAxes, fontsize=32, color=self.text_color,
               ha='center', va='top', fontweight='bold')
        
        ax.text(0.5, 0.93, subtitle, transform=ax.transAxes, fontsize=16, color=self.text_color,
               ha='center', va='top', alpha=0.7)
        
        stats_text = f"Total Aircraft: {stats['total_aircraft']}\n"
        if stats['closest_distance'] is not None:
            stats_text += f"Closest: {stats['closest_distance']:.2f} mi\n"
        if stats['average_altitude'] is not None:
            stats_text += f"Avg Altitude: {stats['average_altitude']:,.0f} ft"
        
        ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=11,
               color=self.text_color, ha='left', va='bottom', alpha=0.7, family='monospace')
        
        legend_text = "★  Home\n●  Closest approach"
        ax.text(0.98, 0.02, legend_text, transform=ax.transAxes, fontsize=10,
               color=self.text_color, ha='right', va='bottom', alpha=0.6)
    
    def _get_marker_size(self, approach: Dict) -> float:
        """Calculate marker size based on altitude"""
        altitude = approach.get('altitude')
        if altitude is None:
            return 4
        
        altitude_feet = altitude * 3.28084
        
        if altitude_feet < 5000:
            return 6
        elif altitude_feet < 15000:
            return 5
        elif altitude_feet < 30000:
            return 4
        else:
            return 3
    
    def _miles_to_degrees(self, miles: float, latitude: float) -> float:
        """Convert miles to approximate degrees"""
        import math
        lat_degrees = miles / 69.0
        lon_degrees = miles / (69.0 * math.cos(math.radians(latitude)))
        return max(lat_degrees, lon_degrees)