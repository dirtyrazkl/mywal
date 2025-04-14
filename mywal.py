import os
import json
import re
import shutil
import numpy as np
from PIL import Image, ImageGrab
from sklearn.cluster import KMeans
from matplotlib.colors import to_hex
import sys
import ctypes
from typing import List, Optional, Dict, Any
import traceback

# ===== CONFIGURATION =====
CONFIG = {
    "komorebi_config": os.path.expanduser("~\\.config\\komorebi\\komorebi.json"),
    "alacritty_config": ("C:\\Users\\Mike\\AppData\\Roaming\\alacritty\\colors.toml"),
    "debug_images": True,
    "debug_path": os.path.expanduser("~/walldesk_debug"),
    "num_colors": 5,
}

class WallpaperColorExtractor:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config if config else CONFIG
        self.ensure_debug_directory()

    def ensure_debug_directory(self) -> None:
        """Ensure debug directory exists"""
        if self.config["debug_images"]:
            os.makedirs(self.config["debug_path"], exist_ok=True)

    def capture_wallpaper_screenshot(self) -> Optional[Image.Image]:
        """Capture screenshot of wallpaper"""
        try:
            print("\n📸 Capturing wallpaper screenshot...")
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            print(f"  ▶ Screen dimensions: {width}x{height}")
            screenshot = ImageGrab.grab(bbox=(0, 0, width, height))
            if self.config["debug_images"]:
                debug_file = os.path.join(self.config["debug_path"], "wallpaper.jpg")
                screenshot.save(debug_file)
                print(f"  ✔ Screenshot saved to: {debug_file}")
            return screenshot
        except Exception as e:
            print(f"  ❌ Screenshot failed: {str(e)}")
            traceback.print_exc()
            return None

    def get_dominant_colors(self, image: Image.Image) -> Optional[List[str]]:
        """Extract dominant colors from image using k-means clustering"""
        try:
            print("\n🎨 Extracting dominant colors...")
            arr = np.array(image)
            pixels = arr.reshape(-1, 3)
            kmeans = KMeans(n_clusters=self.config["num_colors"], random_state=42).fit(pixels)
            colors = kmeans.cluster_centers_
            hex_colors = [to_hex(color / 255) for color in colors]
            print(f"  ✔ Extracted colors: {hex_colors}")
            return hex_colors
        except Exception as e:
            print(f"  ❌ Color extraction failed: {str(e)}")
            traceback.print_exc()
            return None

    def show_color_palette(self, colors: List[str]) -> None:
        """Display the color palette directly in the terminal."""
        if not colors:
            print("❌ No colors provided to display the palette.")
            return
        print("\n🌈 Color Palette:")
        for color in colors:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            print(f"\033[48;2;{r};{g};{b}m   \033[0m {color}")
        print()  # Add a blank line for better formatting

    def update_alacritty_colors(self, colors: List[str]) -> bool:
        """Update Alacritty terminal colors while preserving the file structure."""
        try:
            print("\n🖥️ Updating Alacritty colors...")
            config_path = self.config["alacritty_config"]

            # Backup the original file
            backup_path = config_path + ".bak"
            shutil.copy(config_path, backup_path)
            print(f"  ✔ Backup created at: {backup_path}")

            # Read the existing file
            if not os.path.exists(config_path):
                print(f"  ❌ File not found: {config_path}")
                return False

            with open(config_path, "r") as f:
                lines = f.readlines()
                print(f"  ✔ Read {len(lines)} lines from {config_path}")

            # Define a mapping of replacement values
            replacements = {
                "background": colors[0],
                "foreground": colors[-1],
                "black": colors[0],
                "red": colors[1],
                "green": colors[2],
                "yellow": colors[3],
                "blue": colors[4],
                "white": colors[-1],
            }

            # Update the colors in the file
            updated_lines = []
            current_section = None
            for line in lines:
                # Check if the line is a section header
                section_match = re.match(r"^\[([^\]]+)\]", line)
                if section_match:
                    current_section = section_match.group(1)

                # Attempt to replace colors based on the current section and key
                for color_key, new_value in replacements.items():
                    if f"{color_key} =" in line:
                        print(f"  🟡 Replacing {color_key} with {new_value}")
                        line = re.sub(r'".*"', f'"{new_value}"', line)
                updated_lines.append(line)

            # Write the updated file
            with open(config_path, "w") as f:
                f.writelines(updated_lines)
            print(f"  ✔ Alacritty colors updated at: {config_path}")

            return True
        except Exception as e:
            print(f"  ❌ Failed to update Alacritty colors: {str(e)}")
            traceback.print_exc()
            return False

    def run(self) -> None:
        """Main execution method"""
        try:
            print("🎨 Starting Wallpaper Color Extractor...")
            wallpaper = self.capture_wallpaper_screenshot()
            if not wallpaper:
                raise Exception("Failed to capture wallpaper screenshot")
            palette = self.get_dominant_colors(wallpaper)
            if not palette:
                raise Exception("Failed to extract colors from wallpaper")
            self.show_color_palette(palette)
            updates = {
                "Alacritty": self.update_alacritty_colors(palette),
            }
            print("\n✅ Done! Summary of changes:")
            for name, success in updates.items():
                status = "✔" if success else "❌"
                print(f"{status} {name}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    extractor = WallpaperColorExtractor()
    extractor.run()
