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
POWERSHELL_COLORS = os.path.expanduser("~\\Documents\\WindowsPowerShell\\Microsoft.PowerShell_profile.ps1")

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

def get_dominant_colors(image, num_colors=8):
    """Extract dominant colors from image"""
    try:
        img = image.copy()
        img.thumbnail((300, 300))
        
        pixels = np.array(img).reshape(-1, 3)
        hsv = colors.rgb_to_hsv(pixels/255)
        vibrant_mask = (hsv[:, 1] > 0.5) & (hsv[:, 2] > 0.3)
        if vibrant_mask.any():
            pixels = pixels[vibrant_mask]
        
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)
        
        palette = kmeans.cluster_centers_.astype(int)
        return sorted(palette, key=lambda c: 0.299*c[0] + 0.587*c[1] + 0.114*c[2])
        
    except Exception as e:
        print(f"  ❌ Color extraction failed: {str(e)}")
        return None

def show_color_palette(palette):
    """Display the extracted color palette"""
    fig, ax = plt.subplots(figsize=(10, 2))
    for i, color in enumerate(palette):
        norm_color = np.array(color)/255
        ax.add_patch(Rectangle((i, 0), 1, 1, color=norm_color))
        hex_code = to_hex(norm_color)
        ax.text(i + 0.5, 0.5, f"HEX: {hex_code}\nRGB: {tuple(color)}", 
                ha='center', va='center', color='white' if np.mean(color) < 128 else 'black')
    ax.set_xlim(0, len(palette))
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.title("Extracted Color Palette")
    plt.tight_layout()
    plt.show()

def adjust_contrast(color, background, threshold=4.5):
    """
    Adjust color to ensure it has sufficient contrast with the background.
    """
    def luminance(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast_ratio(l1, l2):
        return (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05)

    bg_luminance = luminance(background)
    fg_luminance = luminance(color)
    ratio = contrast_ratio(fg_luminance, bg_luminance)

    if ratio < threshold:
        adjustment = 1.2 if fg_luminance < bg_luminance else 0.8
        adjusted_color = [min(255, max(0, int(c * adjustment))) for c in color]
        return adjusted_color
    return color

def update_yasb_styles(palette):
    """Update YASB styles.css with extracted palette***

