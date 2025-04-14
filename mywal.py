import os
import json
import re
import winreg
import shutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
from PIL import Image, ImageGrab
from sklearn.cluster import KMeans
from matplotlib.patches import Rectangle
from matplotlib.colors import to_hex
import sys
import ctypes
from ctypes import wintypes
import time
import traceback
import subprocess
from typing import List, Optional, Dict, Any

# ===== CONFIGURATION =====
CONFIG = {
    "komorebi_config": os.path.expanduser("~/.config/komorebi/komorebi.json"),
    "powershell_profile": os.path.expanduser("~/Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1"),
    "windows_terminal_settings": os.path.expanduser("~/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"),
    "alacritty_config": os.path.expanduser("~/AppData/Roaming/alacritty/colors.toml"),
    "yasb_styles": os.path.expanduser("~/.config/yasb/styles.css"),
    "debug_images": True,
    "debug_path": os.path.expanduser("~/walldesk_debug"),
    "num_colors": 5,
    "minimize_windows": True,
    "minimize_delay": 2,
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
        """Capture screenshot of wallpaper without windows"""
        try:
            print("\n📸 Capturing wallpaper screenshot...")
            
            # Get screen dimensions
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            print(f"  ▶ Screen dimensions: {width}x{height}")
            
            if self.config["minimize_windows"]:
                print("  ▶ Minimizing windows...")
                try:
                    user32.keybd_event(0x5B, 0, 0, 0)  # Win key
                    user32.keybd_event(0x44, 0, 0, 0)  # D key
                    time.sleep(self.config["minimize_delay"])
                except Exception as e:
                    print(f"  ⚠️ Couldn't minimize windows: {str(e)}")
            
            # Capture screenshot
            print("  ▶ Capturing screenshot...")
            screenshot = ImageGrab.grab(bbox=(0, 0, width, height))
            
            if self.config["minimize_windows"]:
                try:
                    print("  ▶ Restoring windows...")
                    user32.keybd_event(0x5B, 0, 0x2, 0)
                    user32.keybd_event(0x44, 0, 0x2, 0)
                except Exception as e:
                    print(f"  ⚠️ Couldn't restore windows: {str(e)}")
            
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
            
            # Convert image to numpy array
            arr = np.array(image)
            print(f"  ▶ Image array shape: {arr.shape}")
            
            # Reshape to 2D array of pixels
            pixels = arr.reshape(-1, 3)
            print(f"  ▶ Pixel array shape: {pixels.shape}")
            
            # Perform k-means clustering
            print(f"  ▶ Running K-means for {self.config['num_colors']} colors...")
            kmeans = KMeans(n_clusters=self.config["num_colors"], random_state=42).fit(pixels)
            colors = kmeans.cluster_centers_
            
            # Convert to hex
            hex_colors = [to_hex(color/255) for color in colors]
            print(f"  ✔ Extracted colors: {hex_colors}")
            
            return hex_colors
        except Exception as e:
            print(f"  ❌ Color extraction failed: {str(e)}")
            traceback.print_exc()
            return None

    def show_color_palette(self, colors: List[str]) -> None:
        """Display the color palette"""
        if not colors:
            return
            
        print("\n🌈 Displaying color palette...")
        try:
            fig, ax = plt.subplots(1, len(colors), figsize=(len(colors), 2))
            for i, color in enumerate(colors):
                ax[i].add_patch(Rectangle((0,0), 1, 1, color=color))
                ax[i].axis('off')
                ax[i].set_title(color)
            plt.tight_layout()
            
            if self.config["debug_images"]:
                debug_file = os.path.join(self.config["debug_path"], "palette.png")
                plt.savefig(debug_file)
                print(f"  ✔ Palette saved to: {debug_file}")
            
            plt.show()
        except Exception as e:
            print(f"  ❌ Failed to display palette: {str(e)}")
            traceback.print_exc()

    def update_alacritty_colors(self, colors: List[str]) -> bool:
        """Update Alacritty terminal colors"""
        if not colors:
            return False
            
        try:
            print("\n🖥️ Updating Alacritty colors...")
            config_path = self.config["alacritty_config"]
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Create TOML content
            content = f"""# Colors generated from wallpaper
[colors]
primary = {{
    background = "{colors[0]}"
    foreground = "{colors[-1]}"
}}

cursor = {{
    text = "{colors[0]}"
    cursor = "{colors[-1]}"
}}

normal = {{
    black = "{colors[0]}"
    red = "{colors[1]}"
    green = "{colors[2]}"
    yellow = "{colors[3]}"
    blue = "{colors[4]}"
    magenta = "{colors[1] if len(colors) > 1 else colors[0]}"
    cyan = "{colors[2] if len(colors) > 2 else colors[1]}"
    white = "{colors[-1]}"
}}

bright = {{
    black = "{colors[0]}"
    red = "{colors[1]}"
    green = "{colors[2]}"
    yellow = "{colors[3]}"
    blue = "{colors[4]}"
    magenta = "{colors[1] if len(colors) > 1 else colors[0]}"
    cyan = "{colors[2] if len(colors) > 2 else colors[1]}"
    white = "{colors[-1]}"
}}
"""
            with open(config_path, 'w') as f:
                f.write(content)
            
            print(f"  ✔ Alacritty colors updated at: {config_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update Alacritty colors: {str(e)}")
            traceback.print_exc()
            return False

    def update_windows_accent_color(self, colors: List[str]) -> bool:
        """Update Windows accent color (first color in palette)"""
        if not colors:
            return False
            
        try:
            print("\n🪟 Updating Windows accent color...")
            accent_color = colors[0].lstrip('#')
            bgr_color = f"{accent_color[4:6]}{accent_color[2:4]}{accent_color[0:2]}"
            dword_value = int(bgr_color, 16)
            
            # Set registry key
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "AccentColorMenu", 0, winreg.REG_DWORD, dword_value)
            
            print(f"  ✔ Windows accent color set to: {colors[0]}")
            print("  ⚠️ Note: You may need to log out/restart for changes to take effect")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update Windows accent color: {str(e)}")
            traceback.print_exc()
            return False

    def update_komorebi_borders(self, colors: List[str]) -> bool:
        """Update Komorebi window manager border colors"""
        if not colors:
            return False
            
        try:
            print("\n🖼️ Updating Komorebi border colors...")
            config_path = self.config["komorebi_config"]
            
            # Read existing config or create new
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
                
            # Update border colors
            config["active_window_border"] = colors[1] if len(colors) > 1 else colors[0]
            config["inactive_window_border"] = colors[0]
            
            # Write back to file
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"  ✔ Komorebi borders updated at: {config_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update Komorebi borders: {str(e)}")
            traceback.print_exc()
            return False

    def update_powershell_colors(self, colors: List[str]) -> bool:
        """Update PowerShell profile colors"""
        if not colors:
            return False
            
        try:
            print("\n💻 Updating PowerShell colors...")
            profile_path = self.config["powershell_profile"]
            
            # Create content
            content = f"""# Colors generated from wallpaper
$Host.PrivateData.ErrorForegroundColor = "{colors[1]}" 
$Host.PrivateData.ErrorBackgroundColor = "{colors[0]}"
$Host.PrivateData.WarningForegroundColor = "{colors[3]}"
$Host.PrivateData.WarningBackgroundColor = "{colors[0]}"
$Host.PrivateData.DebugForegroundColor = "{colors[2]}"
$Host.PrivateData.DebugBackgroundColor = "{colors[0]}"
$Host.PrivateData.VerboseForegroundColor = "{colors[4]}"
$Host.PrivateData.VerboseBackgroundColor = "{colors[0]}"
$Host.PrivateData.ProgressForegroundColor = "{colors[4]}"
$Host.PrivateData.ProgressBackgroundColor = "{colors[0]}"

# Set PSReadLine options
Set-PSReadLineOption -Colors @{{
    "Command" = "{colors[2]}"
    "Parameter" = "{colors[4]}"
    "Operator" = "{colors[3]}"
    "Variable" = "{colors[1]}"
    "String" = "{colors[4]}"
    "Number" = "{colors[3]}"
    "Member" = "{colors[1]}"
    "Default" = "{colors[-1]}"
}}
"""
            # Write to profile
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            with open(profile_path, 'w') as f:
                f.write(content)
            
            print(f"  ✔ PowerShell colors updated at: {profile_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update PowerShell colors: {str(e)}")
            traceback.print_exc()
            return False

    def update_windows_terminal_theme(self, colors: List[str]) -> bool:
        """Update Windows Terminal theme"""
        if not colors:
            return False
            
        try:
            print("\n🔮 Updating Windows Terminal theme...")
            settings_path = self.config["windows_terminal_settings"]
            
            # Read existing settings or create new
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {"profiles": {"defaults": {}}, "schemes": []}
                
            # Create new theme
            theme_name = "WallpaperTheme"
            new_theme = {
                "name": theme_name,
                "background": colors[0],
                "black": colors[0],
                "blue": colors[4] if len(colors) > 4 else colors[1],
                "brightBlack": colors[0],
                "brightBlue": colors[4] if len(colors) > 4 else colors[1],
                "brightCyan": colors[2],
                "brightGreen": colors[2],
                "brightPurple": colors[1],
                "brightRed": colors[1],
                "brightWhite": colors[-1],
                "brightYellow": colors[3],
                "cyan": colors[2],
                "foreground": colors[-1],
                "green": colors[2],
                "purple": colors[1],
                "red": colors[1],
                "white": colors[-1],
                "yellow": colors[3]
            }
            
            # Update or add theme
            theme_exists = False
            for i, scheme in enumerate(settings.get("schemes", [])):
                if scheme["name"] == theme_name:
                    settings["schemes"][i] = new_theme
                    theme_exists = True
                    break
            
            if not theme_exists:
                settings.setdefault("schemes", []).append(new_theme)
            
            # Set as default
            settings["profiles"]["defaults"]["colorScheme"] = theme_name
            
            # Write back to file
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
            
            print(f"  ✔ Windows Terminal theme updated at: {settings_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update Windows Terminal theme: {str(e)}")
            traceback.print_exc()
            return False

    def update_yasb_styles(self, colors: List[str]) -> bool:
        """Update Yet Another Status Bar (YASB) styles"""
        if not colors:
            return False
            
        try:
            print("\n📊 Updating YASB styles...")
            styles_path = self.config["yasb_styles"]
            
            # Create CSS content
            content = f"""/* YASB styles generated from wallpaper */
:root {{
    --background: {colors[0]};
    --foreground: {colors[-1]};
    --primary: {colors[4] if len(colors) > 4 else colors[1]};
    --secondary: {colors[2]};
    --alert: {colors[1]};
    --warning: {colors[3]};
}}

body {{
    background-color: var(--background);
    color: var(--foreground);
}}
"""
            # Write to styles file
            os.makedirs(os.path.dirname(styles_path), exist_ok=True)
            with open(styles_path, 'w') as f:
                f.write(content)
            
            print(f"  ✔ YASB styles updated at: {styles_path}")
            return True
        except Exception as e:
            print(f"  ❌ Failed to update YASB styles: {str(e)}")
            traceback.print_exc()
            return False

    def launch_new_powershell(self) -> None:
        """Launch a new PowerShell window to show changes"""
        try:
            print("\n🚀 Launching new PowerShell window to show changes...")
            
            ps_script = """
            Write-Host '=== WALLPAPER COLOR APPLIER ===' -ForegroundColor Cyan
            Write-Host 'New PowerShell session with updated colors!' -ForegroundColor Green
            Write-Host 'If colors don''t appear, run: . $PROFILE' -ForegroundColor Yellow
            Write-Host 'Press any key to close this window...' -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
            """
            
            subprocess.Popen(
                f'start powershell.exe -NoExit -Command "{ps_script}"',
                shell=True
            )
        except Exception as e:
            print(f"  ⚠️ Couldn't launch new PowerShell: {str(e)}")

    def run(self) -> None:
        """Main execution method"""
        try:
            print("🎨 Starting Wallpaper Color Extractor...")
            
            # 1. Capture wallpaper
            wallpaper = self.capture_wallpaper_screenshot()
            if not wallpaper:
                raise Exception("Failed to capture wallpaper screenshot")
            
            # 2. Extract colors
            palette = self.get_dominant_colors(wallpaper)
            if not palette:
                raise Exception("Failed to extract colors from wallpaper")
            
            self.show_color_palette(palette)
            
            # 3. Apply to applications
            updates = {
                "Alacritty": self.update_alacritty_colors(palette),
                "Windows Accent": self.update_windows_accent_color(palette),
                "Komorebi": self.update_komorebi_borders(palette),
                "PowerShell": self.update_powershell_colors(palette),
                "Windows Terminal": self.update_windows_terminal_theme(palette),
                "YASB": self.update_yasb_styles(palette),
            }
            
            # Print summary
            print("\n✅ Done! Summary of changes:")
            for name, success in updates.items():
                status = "✔" if success else "❌"
                print(f"{status} {name}")
            
            # 4. Launch new PowerShell
            self.launch_new_powershell()
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    extractor = WallpaperColorExtractor()
    extractor.run()
