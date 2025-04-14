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

# ===== CONFIGURATION =====
KOMOREBI_CONFIG = "C:\\Users\\Mike\\komorebi.json"
POWERSHELL_COLORS = "C:\\Users\\Mike\\Documents\\WindowsPowerShell\\Microsoft.PowerShell_profile.ps1"

def capture_wallpaper_screenshot():
    """Capture screenshot of wallpaper without windows"""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        
        # Minimize windows temporarily
        user32.keybd_event(0x5B, 0, 0, 0)  # Win key
        user32.keybd_event(0x44, 0, 0, 0)  # D key
        time.sleep(1)
        
        # Capture screenshot
        screenshot = ImageGrab.grab(bbox=(0, 0, width, height))
        
        # Restore windows
        user32.keybd_event(0x5B, 0, 0x2, 0)
        user32.keybd_event(0x44, 0, 0x2, 0)
        
        # Save debug image
        debug_path = os.path.join(os.path.expanduser("~"), "walldesk_debug.jpg")
        screenshot.save(debug_path)
        print(f"  ✔ Saved debug image to: {debug_path}")
        
        return screenshot
        
    except Exception as e:
        print(f"  ❌ Screenshot failed: {str(e)}")
        return None

def update_powershell_profile(palette, profile_path):
    """Update the PowerShell profile with colors while preserving existing content."""
    try:
        print(f"\n🔄 Updating PowerShell profile at: {profile_path}")

        # Ensure the PowerShell profile directory exists
        profile_dir = os.path.dirname(profile_path)
        os.makedirs(profile_dir, exist_ok=True)

        # Read existing profile content
        if os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        # Ensure `Import-Module PSReadLine` exists
        if not any("Import-Module PSReadLine" in line for line in lines):
            lines.insert(0, "Import-Module PSReadLine\n")  # Add it to the top of the file

        # Add palette-based coloring (example)
        color_commands = [
            f"$Host.UI.RawUI.BackgroundColor = 'Black'",
            f"$Host.UI.RawUI.ForegroundColor = 'DarkGreen'",
            f"Clear-Host"
        ]

        # Replace or append colors section
        start_marker = "# BEGIN PALETTE COLORS"
        end_marker = "# END PALETTE COLORS"
        start_idx = next((i for i, line in enumerate(lines) if start_marker in line), None)
        end_idx = next((i for i, line in enumerate(lines) if end_marker in line), None)

        if start_idx is not None and end_idx is not None:
            # Replace existing colors
            lines[start_idx:end_idx + 1] = [start_marker + "\n"] + [cmd + "\n" for cmd in color_commands] + [end_marker + "\n"]
        else:
            # Append new colors
            lines.append("\n" + start_marker + "\n")
            lines.extend(cmd + "\n" for cmd in color_commands)
            lines.append(end_marker + "\n")

        # Write back to the profile
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("  ✔ PowerShell profile updated successfully!")

    except Exception as e:
        print(f"  ❌ Failed to update PowerShell profile: {str(e)}")

def main():
    try:
        print("🖼️ Starting Wallpaper Color Extractor...")
        
        # 1. Capture wallpaper
        print("\n📸 Step 1: Capturing wallpaper...")
        wallpaper = capture_wallpaper_screenshot()
        if not wallpaper:
            raise Exception("Failed to capture wallpaper screenshot")
        
        # 2. Extract colors
        print("\n🎨 Step 2: Extracting colors...")
        palette = get_dominant_colors(wallpaper)
        if palette is None:
            raise Exception("Failed to extract colors from wallpaper")
        
        show_color_palette(palette)
        
        # 3. Apply to applications
        print("\n🔄 Step 3: Applying colors...")
        update_alacritty_colors(palette)
        update_windows_accent_color(palette)
        update_komorebi_borders(palette)
        update_powershell_colors(palette)
        update_yasb_styles(palette)  # Add YASB support
        
        print("\n✅ Done! Summary of changes:")
        print(f"- Alacritty config: {os.path.expanduser('~\\AppData\\Roaming\\alacritty\\colors.toml')}")
        print(f"- Windows accent color updated (may need logout)")
        print(f"- Komorebi config: {KOMOREBI_CONFIG}")
        print(f"- PowerShell profile: {POWERSHELL_COLORS}")
        print(f"- YASB styles: {os.path.expanduser('~\\.config\\yasb\\styles.css')}")
        
        # 4. Launch new PowerShell window to show changes
        launch_new_powershell()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
