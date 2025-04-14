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
            traceback.print_exc()
            return False
