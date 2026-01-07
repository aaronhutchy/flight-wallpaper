"""
Generate wallpaper visualization from flight data
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from datetime import datetime
from typing import List, Dict
import numpy as np
import contextily as ctx


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
        # Fixed view: always center on home with radius-based bounds
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        margin = radius_degrees * 1.2  # 20% extra margin around the search radius
        
        ax.set_xlim(home_lon - margin, home_lon + margin)
        ax.set_ylim(home_lat - margin, home_lat + margin)
        ax.set_aspect('equal')
        
        # Add watercolor artistic map background
        try:
            print("  Adding watercolor map background...")
            # Use Stamen Watercolor for artistic painted look
            ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.Stamen.Watercolor, alpha=0.6)
            print("  ✓ Watercolor map background loaded")
        except Exception as e:
            print(f"  Note: Map background unavailable: {e}")
            print("  Continuing with clean grid design")
            # Draw minimal grid instead
            self._draw_minimal_grid(ax, home_lat, home_lon, radius_degrees)
        
        # Draw radius circles (multiple for reference)
        for i in range(1, int(self.config['radius_miles']) + 1):
            circle_radius = self._miles_to_degrees(i, home_lat)
            circle = Circle((home_lon, home_lat), circle_radius, fill=False, edgecolor=self.text_color, 
                           alpha=0.15, linewidth=1, linestyle='--')
            ax.add_patch(circle)
        
        # Plot home location (larger star)
        ax.plot(home_lon, home_lat, marker='*', markersize=30, color=self.home_color, 
               zorder=1000, markeredgecolor='white', markeredgewidth=2)
        
        # Plot each flight with LARGER markers and CALLSIGN LABELS
        for approach in approaches:
            if approach['latitude'] is None or approach['longitude'] is None:
                continue
            
            lat = approach['latitude']
            lon = approach['longitude']
            callsign = approach.get('callsign', '').strip()
            
            # Draw line from home to approach point
            ax.plot([home_lon, lon], [home_lat, lat], color=self.flight_color, 
                   alpha=0.3, linewidth=1, zorder=1)
            
            # Use airplane marker (MUCH LARGER)
            marker_size = self._get_marker_size(approach)
            heading = approach.get('heading', 0)
            if heading is None:
                heading = 0
            
            # Plot airplane symbol (rotated triangle) - LARGER
            ax.plot(lon, lat, marker=(3, 0, heading - 90), markersize=marker_size, 
                   color=self.flight_color, alpha=0.9, zorder=10, 
                   markeredgecolor='white', markeredgewidth=1.5)
            
            # ADD CALLSIGN LABEL below aircraft
            if callsign:
                # Calculate offset in data coordinates for label placement
                lat_range = ax.get_ylim()[1] - ax.get_ylim()[0]
                label_offset = lat_range * 0.015  # Offset below aircraft
                
                ax.text(lon, lat - label_offset, callsign, 
                       fontsize=9, color=self.text_color, ha='center', va='top',
                       fontweight='bold', zorder=11,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=self.bg_color, 
                                edgecolor='none', alpha=0.8))
        
        self._add_text_info(ax, stats)
    
    def _create_empty_wallpaper(self, ax, home_lat: float, home_lon: float):
        """Create wallpaper when no flights found"""
        # Fixed view: same as flight wallpaper
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        margin = radius_degrees * 1.2
        
        ax.set_xlim(home_lon - margin, home_lon + margin)
        ax.set_ylim(home_lat - margin, home_lat + margin)
        ax.set_aspect('equal')
        
        # Add watercolor artistic map background
        try:
            print("  Adding watercolor map background...")
            ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.Stamen.Watercolor, alpha=0.6)
            print("  ✓ Watercolor map background loaded")
        except Exception as e:
            print(f"  Note: Map background unavailable: {e}")
            print("  Continuing with clean grid design")
            self._draw_minimal_grid(ax, home_lat, home_lon, radius_degrees)
        
        # Draw radius circles
        for i in range(1, int(self.config['radius_miles']) + 1):
            circle_radius = self._miles_to_degrees(i, home_lat)
            circle = Circle((home_lon, home_lat), circle_radius, fill=False, edgecolor=self.text_color,
                           alpha=0.15, linewidth=1, linestyle='--')
            ax.add_patch(circle)
        
        # Plot home location
        ax.plot(home_lon, home_lat, marker='*', markersize=30, color=self.home_color,
               zorder=1000, markeredgecolor='white', markeredgewidth=2)
        
        # Add text
        ax.text(0.5, 0.95, 'No flights detected', transform=ax.transAxes, fontsize=28,
               color=self.text_color, ha='center', va='top', fontweight='light')
        
        ax.text(0.5, 0.88, 'within the search radius', transform=ax.transAxes, fontsize=16,
               color=self.text_color, ha='center', va='top', alpha=0.6)
    
    def _draw_minimal_grid(self, ax, home_lat: float, home_lon: float, radius_degrees: float):
        """Draw a minimal grid background when basemap fails"""
        # Draw crosshairs
        ax.axhline(y=home_lat, color=self.text_color, alpha=0.1, linewidth=1, linestyle='-')
        ax.axvline(x=home_lon, color=self.text_color, alpha=0.1, linewidth=1, linestyle='-')
        
        # Draw diagonal guides
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Calculate diagonal lines through center
        ax.plot(xlim, [home_lat - (xlim[1]-home_lon), home_lat + (xlim[1]-home_lon)], 
               color=self.text_color, alpha=0.1, linewidth=1, linestyle='-')
        ax.plot(xlim, [home_lat + (xlim[1]-home_lon), home_lat - (xlim[1]-home_lon)], 
               color=self.text_color, alpha=0.1, linewidth=1, linestyle='-')
    
    def _add_text_info(self, ax, stats: Dict):
        """Add title and statistics text"""
        now = datetime.now()
        title = f"Flights Over My House"
        subtitle = f"Live - {now.strftime('%B %d, %Y %H:%M')}"
        
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
        
        legend_text = "★  Home\n✈  Aircraft"
        ax.text(0.98, 0.02, legend_text, transform=ax.transAxes, fontsize=10,
               color=self.text_color, ha='right', va='bottom', alpha=0.6)
    
    def _get_marker_size(self, approach: Dict) -> float:
        """Calculate marker size based on altitude - MUCH LARGER for visibility"""
        altitude = approach.get('altitude')
        if altitude is None:
            return 20  # Much larger default
        
        altitude_feet = altitude * 3.28084
        
        # Much larger sizes for visibility
        if altitude_feet < 5000:
            return 25
        elif altitude_feet < 15000:
            return 22
        elif altitude_feet < 30000:
            return 20
        else:
            return 18
    
    def _miles_to_degrees(self, miles: float, latitude: float) -> float:
        """Convert miles to approximate degrees"""
        import math
        lat_degrees = miles / 69.0
        lon_degrees = miles / (69.0 * math.cos(math.radians(latitude)))
        return max(lat_degrees, lon_degrees)