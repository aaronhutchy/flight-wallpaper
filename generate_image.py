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
        # Override config for neon pink radar phone wallpaper
        self.width = 1080   # Phone width
        self.height = 2316  # 19.3:9 aspect ratio
        self.bg_color = '#000000'  # Black background
        self.home_color = '#ff69b4'  # Light pink for home dot
        self.flight_color = '#ff69b4'  # Light pink for aircraft
        self.text_color = '#ff69b4'  # Light pink for text
        self.radar_color = '#ff1493'  # Neon pink for radar circles
        
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
        
        # Remove all padding to fill entire screen
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Save PNG
        plt.savefig(output_path, dpi=dpi, facecolor=self.bg_color, edgecolor='none', bbox_inches='tight', pad_inches=0)
        
        # Also save as JPG
        jpg_path = output_path.replace('.png', '.jpg')
        plt.savefig(jpg_path, dpi=dpi, facecolor=self.bg_color, edgecolor='none', bbox_inches='tight', pad_inches=0, format='jpg')
        
        plt.close()
        
        print(f"\n✓ Wallpaper saved to:")
        print(f"  PNG: {output_path}")
        print(f"  JPG: {jpg_path}")
    
    def _create_flight_wallpaper(self, ax, home_lat: float, home_lon: float, approaches: List[Dict], stats: Dict):
        """Create wallpaper with flight data"""
        # Fixed view optimized for PORTRAIT phone (tall, narrow)
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        
        # Phone aspect ratio: height=2316, width=1080 → tall and narrow
        # To fill screen: show MORE vertically, crop sides
        
        # Set vertical span to fill height  
        v_margin = radius_degrees * 1.05
        
        # Set horizontal span narrower to crop left/right edges
        h_margin = v_margin * 0.47  # Crop sides for portrait
        
        ax.set_xlim(home_lon - h_margin, home_lon + h_margin)
        ax.set_ylim(home_lat - v_margin, home_lat + v_margin)
        ax.set_aspect('equal')
        
        # Use clean radar grid background (no map tiles)
        print("  Using clean radar grid design...")
        self._draw_minimal_grid(ax, home_lat, home_lon, radius_degrees)
        
        # Draw neon pink radar circles (multiple for reference)
        for i in range(1, int(self.config['radius_miles']) + 1):
            circle_radius = self._miles_to_degrees(i, home_lat)
            circle = Circle((home_lon, home_lat), circle_radius, fill=False, edgecolor=self.radar_color, 
                           alpha=0.4, linewidth=2, linestyle='-')
            ax.add_patch(circle)
        
        # Plot home location as a simple pink dot
        ax.plot(home_lon, home_lat, marker='o', markersize=15, color=self.home_color, 
               zorder=1000, markeredgecolor=self.home_color, markeredgewidth=2)
        
        # Plot each flight with LARGER markers and CALLSIGN LABELS
        for approach in approaches:
            if approach['latitude'] is None or approach['longitude'] is None:
                continue
            
            lat = approach['latitude']
            lon = approach['longitude']
            
            # Draw line from home to approach point
            ax.plot([home_lon, lon], [home_lat, lat], color=self.flight_color, 
                   alpha=0.4, linewidth=1, zorder=1)
            
            # Use airplane marker (MUCH LARGER)
            marker_size = self._get_marker_size(approach)
            heading = approach.get('heading', 0)
            if heading is None:
                heading = 0
            
            # Plot airplane symbol (rotated triangle) - LARGER
            ax.plot(lon, lat, marker=(3, 0, heading - 90), markersize=marker_size, 
                   color=self.flight_color, alpha=0.9, zorder=10, 
                   markeredgecolor=self.flight_color, markeredgewidth=1.5)
            
            # ADD CALLSIGN LABEL below aircraft with smart formatting
            label = self._format_label(approach)
            if label:
                # Calculate offset in data coordinates for label placement
                lat_range = ax.get_ylim()[1] - ax.get_ylim()[0]
                label_offset = lat_range * 0.015  # Offset below aircraft
                
                ax.text(lon, lat - label_offset, label, 
                       fontsize=11, color=self.text_color, ha='center', va='top',
                       fontweight='bold', zorder=11,
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='black', 
                                edgecolor=self.flight_color, linewidth=1, alpha=0.9))
        
        self._add_text_info(ax, stats)
    
    def _create_empty_wallpaper(self, ax, home_lat: float, home_lon: float):
        """Create wallpaper when no flights found"""
        # Fixed view optimized for PORTRAIT phone (tall, narrow)
        radius_degrees = self._miles_to_degrees(self.config['radius_miles'], home_lat)
        
        # Set vertical span to fill height
        v_margin = radius_degrees * 1.05
        
        # Set horizontal span narrower to crop sides
        h_margin = v_margin * 0.47
        
        ax.set_xlim(home_lon - h_margin, home_lon + h_margin)
        ax.set_ylim(home_lat - v_margin, home_lat + v_margin)
        ax.set_aspect('equal')
        
        # Use clean radar grid background
        print("  Using clean radar grid design...")
        self._draw_minimal_grid(ax, home_lat, home_lon, radius_degrees)
        
        # Draw neon pink radar circles
        for i in range(1, int(self.config['radius_miles']) + 1):
            circle_radius = self._miles_to_degrees(i, home_lat)
            circle = Circle((home_lon, home_lat), circle_radius, fill=False, edgecolor=self.radar_color,
                           alpha=0.4, linewidth=2, linestyle='-')
            ax.add_patch(circle)
        
        # Plot home location as pink dot
        ax.plot(home_lon, home_lat, marker='o', markersize=15, color=self.home_color,
               zorder=1000, markeredgecolor=self.home_color, markeredgewidth=2)
        
        # Add text
        ax.text(0.5, 0.95, 'No flights detected', transform=ax.transAxes, fontsize=28,
               color=self.text_color, ha='center', va='top', fontweight='light')
        
        ax.text(0.5, 0.88, 'within the search radius', transform=ax.transAxes, fontsize=16,
               color=self.text_color, ha='center', va='top', alpha=0.6)
    
    def _draw_minimal_grid(self, ax, home_lat: float, home_lon: float, radius_degrees: float):
        """Draw a neon pink radar grid background"""
        # Draw crosshairs
        ax.axhline(y=home_lat, color=self.radar_color, alpha=0.3, linewidth=1.5, linestyle='-')
        ax.axvline(x=home_lon, color=self.radar_color, alpha=0.3, linewidth=1.5, linestyle='-')
        
        # Draw diagonal guides
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Calculate diagonal lines through center
        ax.plot(xlim, [home_lat - (xlim[1]-home_lon), home_lat + (xlim[1]-home_lon)], 
               color=self.radar_color, alpha=0.3, linewidth=1.5, linestyle='-')
        ax.plot(xlim, [home_lat + (xlim[1]-home_lon), home_lat - (xlim[1]-home_lon)], 
               color=self.radar_color, alpha=0.3, linewidth=1.5, linestyle='-')
    
    def _add_text_info(self, ax, stats: Dict):
        """Add statistics text"""
        # No title or subtitle - clean minimal look
        
        stats_text = f"Total Aircraft: {stats['total_aircraft']}\n"
        if stats['closest_distance'] is not None:
            stats_text += f"Closest: {stats['closest_distance']:.2f} mi\n"
        if stats['average_altitude'] is not None:
            stats_text += f"Avg Altitude: {stats['average_altitude']:,.0f} ft"
        
        ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=12,
               color=self.text_color, ha='left', va='bottom', alpha=0.7, family='monospace')
        
        legend_text = "●  Home\n✈  Aircraft"
        ax.text(0.98, 0.02, legend_text, transform=ax.transAxes, fontsize=11,
               color=self.text_color, ha='right', va='bottom', alpha=0.6)
    
    def _format_label(self, approach: Dict) -> str:
        """Format aircraft label intelligently based on available data"""
        callsign = (approach.get('callsign') or '').strip()
        origin = approach.get('origin', '').strip()
        destination = approach.get('destination', '').strip()
        icao24 = approach.get('icao24', '').strip()
        
        # Build label with flight number and route
        label_parts = []
        
        # Line 1: Flight number/callsign
        if not callsign:
            flight_label = icao24.upper() if icao24 else 'UNKNOWN'
        elif callsign.isalpha():
            flight_label = callsign.upper()  # Special callsigns like REDARROW
        else:
            # Parse airline code + flight number (e.g., "RYR9630" → "RYR 9630")
            import re
            match = re.match(r'^([A-Z]{2,3})(\d+.*)$', callsign.upper())
            if match:
                airline_code = match.group(1)
                flight_num = match.group(2)
                flight_label = f"{airline_code} {flight_num}"
            else:
                flight_label = callsign.upper()
        
        label_parts.append(flight_label)
        
        # Line 2: Route (if available)
        if origin and destination:
            label_parts.append(f"{origin} → {destination}")
        elif origin:
            label_parts.append(f"{origin} → ?")
        elif destination:
            label_parts.append(f"? → {destination}")
        
        return '\n'.join(label_parts)
    
    def _get_marker_size(self, approach: Dict) -> float:
        """Calculate marker size based on altitude - LARGER for better visibility"""
        altitude = approach.get('altitude')
        if altitude is None:
            return 28  # Larger default
        
        altitude_feet = altitude * 3.28084
        
        # Larger sizes for better visibility
        if altitude_feet < 5000:
            return 32
        elif altitude_feet < 15000:
            return 30
        elif altitude_feet < 30000:
            return 28
        else:
            return 26
    
    def _miles_to_degrees(self, miles: float, latitude: float) -> float:
        """Convert miles to approximate degrees"""
        import math
        lat_degrees = miles / 69.0
        lon_degrees = miles / (69.0 * math.cos(math.radians(latitude)))
        return max(lat_degrees, lon_degrees)