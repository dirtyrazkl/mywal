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
import logging
import argparse
import colorsys  # Added for HSL manipulation

# ===== CONFIGURATION =====
CONFIG = {
    "komorebi_config": os.getenv("KOMOREBI_CONFIG", "C:\\Users\\Mike\\komorebi.json"),
    "alacritty_config": os.getenv("ALACRITTY_CONFIG", "C:\\Users\\Mike\\AppData\\Roaming\\alacritty\\colors.toml"),
    "debug_images": True,
    "debug_path": os.path.expanduser("~/walldesk_debug"),
    "num_colors": 5,
    "saturation_boost": 3,  # Factor to boost saturation
}

# Configure logging
logging.basicConfig(
    filename='error.log',
    level=logging.DEBUG,  # Set to DEBUG for detailed log output
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class WallpaperColorExtractor:
    """
    A class to extract dominant colors from a wallpaper and update configurations for specific programs.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the WallpaperColorExtractor with optional configuration.
        """
        self.config = config if config else CONFIG
        self.ensure_debug_directory()

    def ensure_debug_directory(self) -> None:
        """
        Ensure that the debug directory exists if debugging is enabled.
        """
        if self.config["debug_images"]:
            os.makedirs(self.config["debug_path"], exist_ok=True)

    def log_error(self, error: Exception) -> None:
        """
        Log the error details to a file.
        """
        logging.error("An error occurred: %s", str(error), exc_info=True)

    def capture_wallpaper_screenshot(self) -> Optional[Image.Image]:
        """
        Capture a screenshot of the current wallpaper.
        """
        try:
            print("\n📸 Capturing wallpaper screenshot...")
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            print(f"  ▶ Screen dimensions: {width}x{height}")
            screenshot = ImageGrab.grab(bbox=(0, 0, width, height))
            if self.config["debug_images"]:
                debug_file = os.path.join(self.config["debug_path"], "wallpaper.png")
                screenshot.save(debug_file, format="PNG")
                print(f"  ✔ Screenshot saved to: {debug_file}")
            return screenshot
        except Exception as e:
            print(f"  ❌ Screenshot failed: {str(e)}")
            self.log_error(e)
            return None

    def get_dominant_colors(self, image: Image.Image) -> Optional[List[str]]:
        """
        Extract dominant colors from the image using k-means clustering.
        """
        try:
            print("\n🎨 Extracting dominant colors...")
            arr = np.array(image)
            pixels = arr.reshape(-1, 3)
            kmeans = KMeans(n_clusters=self.config["num_colors"], random_state=42).fit(pixels)
            colors = kmeans.cluster_centers_
            hex_colors = [to_hex(color / 255) for color in colors]
            print(f"  ✔ Extracted colors (before adjustment): {hex_colors}")
            adjusted_colors = self.boost_saturation(hex_colors)
            print(f"  ✔ Colors after saturation boost: {adjusted_colors}")
            return adjusted_colors
        except Exception as e:
            print(f"  ❌ Color extraction failed: {str(e)}")
            self.log_error(e)
            return None

    def boost_saturation(self, hex_colors: List[str]) -> List[str]:
        """
        Boost the saturation of colors to make them more vibrant.
        """
        boosted_colors = []
        for hex_color in hex_colors:
            try:
                r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (1, 3, 5))  # Convert HEX to normalized RGB
                h, l, s = colorsys.rgb_to_hls(r, g, b)  # Convert RGB to HSL
                s = min(1.0, s * self.config["saturation_boost"])  # Boost saturation
                r, g, b = colorsys.hls_to_rgb(h, l, s)  # Convert back to RGB
                boosted_colors.append(to_hex([r, g, b]))  # Convert normalized RGB to HEX
            except Exception as e:
                logging.warning(f"Failed to boost saturation for {hex_color}: {str(e)}")
        return boosted_colors

    def show_color_palette(self, colors: List[str]) -> None:
        """
        Display the color palette in the terminal.
        """
        if not colors:
            print("❌ No colors provided to display the palette.")
            return
        print("\n🌈 Color Palette:")
        for color in colors:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            print(f"\033[48;2;{r};{g};{b}m   \033[0m {color}")
        print()  # Add a blank line for better formatting

    def update_alacritty_colors(self, colors: List[str]) -> bool:
        """
        Update Alacritty terminal colors while preserving the file structure.
        """
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

            # Define a helper function to calculate brightness
            def brightness(hex_color):
                r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (1, 3, 5))
                return 0.299 * r + 0.587 * g + 0.114 * b

            # Sort colors by brightness
            sorted_colors = sorted(colors, key=brightness)

            # Assign colors based on contrast
            background_color = sorted_colors[0]  # Darkest color for background
            foreground_color = sorted_colors[-1]  # Brightest color for foreground
            text_color = sorted_colors[-2]  # Second brightest for text
            other_colors = sorted_colors[1:-2]  # Remaining colors for other mappings

            # Define a mapping of replacement values
            replacements = {
                "background": background_color,
                "foreground": foreground_color,
                "black": background_color,
                "white": foreground_color,
                "red": other_colors[0] if len(other_colors) > 0 else foreground_color,
                "green": other_colors[1] if len(other_colors) > 1 else foreground_color,
                "yellow": other_colors[2] if len(other_colors) > 2 else foreground_color,
                "blue": other_colors[3] if len(other_colors) > 3 else foreground_color,
            }

            # Update the colors in the file
            updated_lines = []
            for line in lines:
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
            self.log_error(e)
            return False

    def update_komorebi_colors(self, colors: List[str]) -> bool:
        """
        Update Komorebi border colors while preserving the file structure.
        """
        config_path = self.config["komorebi_config"]
        try:
            print("\n🖼️ Updating Komorebi border colors...")
            backup_path = config_path + ".bak"
            shutil.copy(config_path, backup_path)
            print(f"  ✔ Backup created at: {backup_path}")

            with open(config_path, "r") as f:
                config_data = json.load(f)

            if "border_colours" in config_data:
                # Sort colors by brightness (luminance)
                def brightness(hex_color):
                    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (1, 3, 5))
                    return 0.299 * r + 0.587 * g + 0.114 * b

                sorted_colors = sorted(colors, key=brightness, reverse=True)

                # Assign the brightest color to "single" (active window)
                # and distribute the rest to other keys
                keys_to_update = ["single", "stack", "monocle", "unfocused"]
                for i, key in enumerate(keys_to_update):
                    if key in config_data["border_colours"]:
                        print(f"  🟡 Updating {key} to {sorted_colors[i % len(sorted_colors)]}")
                        config_data["border_colours"][key] = sorted_colors[i % len(sorted_colors)]

            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=4)
            print(f"  ✔ Komorebi colors updated at: {config_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update Komorebi colors: {str(e)}")
            self.log_error(e)
            return False

    def run(self) -> None:
        """
        Main execution method to capture wallpaper, extract colors, and update configurations.
        """
        try:
            print("🎨 Starting Wallpaper Color Extractor...\n")
            wallpaper = self.capture_wallpaper_screenshot()
            if not wallpaper:
                raise Exception("Failed to capture wallpaper screenshot")
            palette = self.get_dominant_colors(wallpaper)
            if not palette:
                raise Exception("Failed to extract colors from wallpaper")
            self.show_color_palette(palette)
            print("\nUpdating configurations...\n")
            updates = {
                "Alacritty": self.update_alacritty_colors(palette),
                "Komorebi": self.update_komorebi_colors(palette),
            }
            print("\n✅ Done! Summary of changes:")
            for name, success in updates.items():
                status = "✔ Success" if success else "❌ Failed"
                print(f"{status}: {name}")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            self.log_error(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wallpaper Color Extractor")
    parser.add_argument("--num-colors", type=int, default=5, help="Number of dominant colors to extract")
    parser.add_argument("--saturation-boost", type=float, default=3, help="Saturation boost factor")
    args = parser.parse_args()

    CONFIG["num_colors"] = args.num_colors
    CONFIG["saturation_boost"] = args.saturation_boost

    extractor = WallpaperColorExtractor()
    extractor.run()
