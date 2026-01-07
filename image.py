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
        
        radius_degrees = self._miles_to_degrees(self.co