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

def update_alacritty_colors(palette):
    """Update Alacritty colors.toml with new colors"""
    alacritty_config = os.path.expanduser("~\\AppData\\Roaming\\alacritty\\colors.toml")
    
    try:
        print(f"\n🔄 Updating Alacritty colors at: {alacritty_config}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(alacritty_config), exist_ok=True)

        # Create template with new colors
        template = f"""# Colors generated from wallpaper
[colors.primary]
background = "#{palette[0][0]:02x}{palette[0][1]:02x}{palette[0][2]:02x}"
foreground = "#{palette[-1][0]:02x}{palette[-1][1]:02x}{palette[-1][2]:02x}"

[colors.normal]
black = "#{palette[0][0]:02x}{palette[0][1]:02x}{palette[0][2]:02x}"
red = "#{palette[1][0]:02x}{palette[1][1]:02x}{palette[1][2]:02x}"
green = "#{palette[2][0]:02x}{palette[2][1]:02x}{palette[2][2]:02x}"
yellow = "#{palette[3][0]:02x}{palette[3][1]:02x}{palette[3][2]:02x}"
blue = "#{palette[4][0]:02x}{palette[4][1]:02x}{palette[4][2]:02x}"
magenta = "#{palette[5][0]:02x}{palette[5][1]:02x}{palette[5][2]:02x}"
cyan = "#{palette[6][0]:02x}{palette[6][1]:02x}{palette[6][2]:02x}"
white = "#{palette[7][0]:02x}{palette[7][1]:02x}{palette[7][2]:02x}"

[colors.bright]
black = "#{min(255, palette[0][0]+40):02x}{min(255, palette[0][1]+40):02x}{min(255, palette[0][2]+40):02x}"
red = "#{min(255, palette[1][0]+40):02x}{min(255, palette[1][1]+40):02x}{min(255, palette[1][2]+40):02x}"
green = "#{min(255, palette[2][0]+40):02x}{min(255, palette[2][1]+40):02x}{min(255, palette[2][2]+40):02x}"
yellow = "#{min(255, palette[3][0]+40):02x}{min(255, palette[3][1]+40):02x}{min(255, palette[3][2]+40):02x}"
blue = "#{min(255, palette[4][0]+40):02x}{min(255, palette[4][1]+40):02x}{min(255, palette[4][2]+40):02x}"
magenta = "#{min(255, palette[5][0]+40):02x}{min(255, palette[5][1]+40):02x}{min(255, palette[5][2]+40):02x}"
cyan = "#{min(255, palette[6][0]+40):02x}{min(255, palette[6][1]+40):02x}{min(255, palette[6][2]+40):02x}"
white = "#{min(255, palette[7][0]+40):02x}{min(255, palette[7][1]+40):02x}{min(255, palette[7][2]+40):02x}"
"""
        # Write the new config
        with open(alacritty_config, 'w', encoding='utf-8') as f:
            f.write(template)

        print("  ✔ Successfully updated Alacritty colors!")
        return True

    except Exception as e:
        print(f"  ❌ Failed to update Alacritty: {str(e)}")
        traceback.print_exc()
        return False

def update_windows_accent_color(palette):
    """Update Windows accent color via registry"""
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("  ⚠️ Skipping accent color (run as admin to enable)")
            return
            
        accent = palette[3]
        bgr = (min(255, accent[2]) << 16) | (min(255, accent[1]) << 8) | min(255, accent[0])
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                          "Software\\Microsoft\\Windows\\DWM",
                          0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "AccentColor", 0, winreg.REG_DWORD, bgr)
        print("  ✔ Updated Windows accent color (may need logout)")
    except Exception as e:
        print(f"  ❌ Failed to update accent color: {str(e)}")

def update_komorebi_borders(palette):
    """Update Komorebi window manager borders while preserving all other settings"""
    komorebi_config = "C:\\Users\\Mike\\komorebi.json"
    
    try:
        print(f"\n🔄 Updating Komorebi borders at: {komorebi_config}")
        
        # 1. Verify the config file exists
        if not os.path.exists(komorebi_config):
            print(f"  ❌ Error: Komorebi config not found at {komorebi_config}")
            return False

        # 2. Read the existing config
        with open(komorebi_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 3. Update only the border colors
        new_border_colors = {
            "single": f"#{palette[4][0]:02x}{palette[4][1]:02x}{palette[4][2]:02x}",
            "stack": f"#{palette[7][0]:02x}{palette[7][1]:02x}{palette[7][2]:02x}",
            "monocle": f"#{palette[3][0]:02x}{palette[3][1]:02x}{palette[3][2]:02x}",
            "unfocused": f"#{palette[0][0]:02x}{palette[0][1]:02x}{palette[0][2]:02x}55"  # 55 adds transparency
        }
        
        # Preserve existing border_colours if they exist, or create new
        if "border_colours" in config:
            config["border_colours"].update(new_border_colors)
        else:
            config["border_colours"] = new_border_colors
        
        # 4. Write back the updated config
        with open(komorebi_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("  ✔ Successfully updated Komorebi border colors!")
        return True

    except Exception as e:
        print(f"  ❌ Failed to update Komorebi: {str(e)}")
        traceback.print_exc()
        return False

def update_powershell_colors(palette):
    """Update PowerShell console colors with detailed debugging"""
    print("\n🔄 Updating PowerShell colors...")
    
    try:
        # 1. Verify and create profile path
        profile_path = os.path.expanduser(POWERSHELL_COLORS)
        profile_dir = os.path.dirname(profile_path)
        print(f"🔍 PowerShell profile location: {profile_path}")
        
        if not os.path.exists(profile_dir):
            print(f"📂 Creating directory: {profile_dir}")
            os.makedirs(profile_dir)
        
        # 2. Color mapping - using standard console colors
        console_colors = {
            'Black': (0, 0, 0),
            'DarkBlue': (0, 0, 128),
            'DarkGreen': (0, 128, 0),
            'DarkCyan': (0, 128, 128),
            'DarkRed': (128, 0, 0),
            'DarkMagenta': (128, 0, 128),
            'DarkYellow': (128, 128, 0),
            'Gray': (192, 192, 192),
            'DarkGray': (128, 128, 128),
            'Blue': (0, 0, 255),
            'Green': (0, 255, 0),
            'Cyan': (0, 255, 255),
            'Red': (255, 0, 0),
            'Magenta': (255, 0, 255),
            'Yellow': (255, 255, 0),
            'White': (255, 255, 255)
        }
        
        # 3. Find nearest PowerShell color
        def find_nearest_color(target_rgb):
            min_distance = float('inf')
            nearest = 'Black'
            for name, rgb in console_colors.items():
                distance = sum((a-b)**2 for a,b in zip(target_rgb, rgb))
                if distance < min_distance:
                    min_distance = distance
                    nearest = name
            return nearest
        
        # 4. Generate the PowerShell script
        ps_script = f"""# PowerShell color scheme generated from wallpaper
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Main console colors
$Host.UI.RawUI.BackgroundColor = 'Black'
$Host.UI.RawUI.ForegroundColor = 'White'

# Error and warning colors
$Host.PrivateData.ErrorForegroundColor = '{find_nearest_color(palette[1])}'
$Host.PrivateData.WarningForegroundColor = '{find_nearest_color(palette[3])}'
$Host.PrivateData.DebugForegroundColor = '{find_nearest_color(palette[6])}'
$Host.PrivateData.VerboseForegroundColor = '{find_nearest_color(palette[2])}'
$Host.PrivateData.ProgressForegroundColor = '{find_nearest_color(palette[4])}'

# PSReadLine syntax highlighting
if (Get-Module -Name PSReadLine) {{
    Set-PSReadLineOption -Colors @{{
        Command    = '{find_nearest_color(palette[4])}'
        Parameter  = '{find_nearest_color(palette[7])}'
        Operator   = '{find_nearest_color(palette[5])}'
        String     = '{find_nearest_color(palette[2])}'
        Number     = '{find_nearest_color(palette[3])}'
        Comment    = '{find_nearest_color(palette[0])}'
        Default    = 'White'
    }}
}}
else {{
    Write-Warning "PSReadLine module not loaded - syntax highlighting not applied"
}}
"""
        # 5. Write the profile file
        print(f"📝 Writing to profile: {profile_path}")
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(ps_script)
        
        # 6. Verify the file was created
        if os.path.exists(profile_path):
            print("✅ PowerShell profile updated successfully!")
            print("\n🛠️ IMPORTANT: You must do one of these to see changes:")
            print("1. Start a NEW PowerShell session")
            print("2. Or run this command in current session:")
            print(f"   . {profile_path}")
        else:
            print("❌ Failed to create PowerShell profile file")
            
    except Exception as e:
        print(f"❌ Error updating PowerShell colors: {str(e)}")
        traceback.print_exc()
    
    # 7. Additional troubleshooting help
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Verify profile exists: Test-Path $PROFILE")
    print("2. Check content: Get-Content $PROFILE")
    print("3. Check PSReadLine is installed: Get-Module PSReadLine")
    print("4. Install PSReadLine if needed: Install-Module PSReadLine -Force")

# Additional function for contrast adjustment
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

# Updated YASB function with contrast adjustment
def update_yasb_styles(palette):
    """Update YASB styles.css with extracted palette colors"""
    yasb_styles = os.path.expanduser("~\\AppData\\Local\\yasb\\styles.css")
    yasb_backup = yasb_styles + ".backup"

    try:
        print(f"\n🔄 Updating YASB styles at: {yasb_styles}")

        # Create backup if it doesn't exist
        if not os.path.exists(yasb_backup) and os.path.exists(yasb_styles):
            shutil.copy2(yasb_styles, yasb_backup)
            print(f"  ✔ Created backup at: {yasb_backup}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(yasb_styles), exist_ok=True)

        # Adjust contrast for readability
        background = palette[0]
        foreground = adjust_contrast(palette[-1], background)

        # Generate new CSS with colors from palette
        css_content = f"""/* YASB styles generated from wallpaper colors */
#yasb {{
  background-color: #{background[0]:02x}{background[1]:02x}{background[2]:02x}AA;
  color: #{foreground[0]:02x}{foreground[1]:02x}{foreground[2]:02x};
}}
"""
        # Write the new CSS file
        with open(yasb_styles, 'w', encoding='utf-8') as f:
            f.write(css_content)

        print(f"  ✔ Updated YASB styles with extracted colors")

        # Restart YASB
        print("  🔄 Restarting YASB to apply changes...")
        subprocess.run("taskkill /f /im yasb.exe", shell=True, stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.Popen("yasb", shell=True, start_new_session=True,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        print("  ✔ YASB restarted successfully!")

        return True

    except Exception as e:
        print(f"  ❌ Failed to update YASB styles: {str(e)}")
        traceback.print_exc()
        return False

def launch_new_powershell():
    """Launch a new PowerShell window to show changes and keep it open"""
    try:
        print("\n🚀 Launching new PowerShell window to show changes...")
        
        # Create a more robust PowerShell command that will stay open
        ps_command = """
        Write-Host '=== WALLPAPER COLOR APPLIER ===' -ForegroundColor Cyan
        Write-Host 'New PowerShell session with updated colors!' -ForegroundColor Green
        Write-Host 'If colors don''t appear, run: . $PROFILE' -ForegroundColor Yellow
        Write-Host 'Press any key to close this window...' -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        """
        
        # Use START to launch in a new window and keep it open
        subprocess.Popen(f'start powershell.exe -NoExit -Command "{ps_command}"', 
                        shell=True)
        
    except Exception as e:
        print(f"  ⚠️ Couldn't launch new PowerShell: {str(e)}")

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
        print(f"- YASB styles: {os.path.expanduser('~\\AppData\\Local\\yasb\\styles.css')}")
        
        # 4. Launch new PowerShell window to show changes
        launch_new_powershell()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
