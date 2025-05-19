import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import math
import random
import time
import threading
import os
import json
from PIL import Image, ImageTk
import sys

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class WheelOfLuckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Wheel of Fortune ✨")
        self.root.geometry("800x700")
        self.root.minsize(700, 650)
        
        # Modern color scheme
        self.bg_color = "#2d3436"
        self.button_color = "#0984e3"
        self.button_hover = "#74b9ff"
        self.wheel_bg = "#dfe6e9"
        self.text_color = "#ffffff"
        self.highlight_color = "#fdcb6e"
        
        self.root.configure(bg=self.bg_color)
        
        # Load images (fallback if images not found)
        self.load_images()
        
        # App state
        self.center = (400, 300)
        self.radius = 250
        self.options = []
        self.colors = [
            "#e17055", "#00b894", "#fdcb6e", "#6c5ce7", 
            "#e84393", "#00cec9", "#fab1a0", "#a29bfe",
            "#fd79a8", "#55efc4", "#ffeaa7", "#74b9ff"
        ]
        self.current_angle = 0
        self.spin_speed = 0
        self.spinning = False
        self.stopping = False
        self.spin_start_time = 0
        self.confetti_particles = []
        self.last_result = ""
        self.history = []
        self.sound_enabled = True
        self.dark_mode = False
        
        # Create UI
        self.create_widgets()
        
        # Load initial options
        self.load_options()
        
        # Start confetti background thread
        self.confetti_thread_running = True
        self.confetti_thread = threading.Thread(target=self.update_confetti, daemon=True)
        self.confetti_thread.start()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_images(self):
        """Load images with fallback to colored rectangles if images not found"""
        self.images = {}
        image_files = {
            'spin': 'spin.png',
            'stop': 'stop.png',
            'add': 'add.png',
            'remove': 'remove.png',
            'shuffle': 'shuffle.png',
            'save': 'save.png',
            'load': 'load.png',
            'settings': 'settings.png',
            'history': 'history.png',
            'logo': 'logo.png'
        }
        
        # Create fallback images
        for name in image_files.keys():
            try:
                img = Image.open(image_files[name])
                img = img.resize((24, 24), Image.Resampling.LANCZOS)
                self.images[name] = ImageTk.PhotoImage(img)
            except:
                # Create a colored rectangle as fallback
                img = Image.new('RGB', (24, 24), self.get_fallback_color(name))
                self.images[name] = ImageTk.PhotoImage(img)
    
    def get_fallback_color(self, name):
        """Return color for fallback icons"""
        colors = {
            'spin': '#00b894',
            'stop': '#d63031',
            'add': '#0984e3',
            'remove': '#e17055',
            'shuffle': '#6c5ce7',
            'save': '#00cec9',
            'load': '#fdcb6e',
            'settings': '#636e72',
            'history': '#a29bfe',
            'logo': '#ffffff'
        }
        return colors.get(name, '#000000')

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self.header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        if 'logo' in self.images:
            self.logo_label = tk.Label(
                self.header_frame, 
                image=self.images['logo'], 
                bg=self.bg_color
            )
            self.logo_label.pack(side=tk.LEFT, padx=5)
        
        self.title_label = tk.Label(
            self.header_frame, 
            text="✨ Wheel of Fortune ✨", 
            font=("Arial", 24, "bold"), 
            fg=self.highlight_color,
            bg=self.bg_color
        )
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Wheel canvas
        self.canvas_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=600, 
            height=500, 
            bg=self.wheel_bg,
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
        
        # Control buttons
        self.control_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.control_frame.pack(fill=tk.X, pady=(10, 5))
        
        # Main action buttons
        self.spin_button = self.create_button("Spin", 'spin', self.start_spin)
        self.spin_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = self.create_button("Stop", 'stop', self.stop_spin, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.add_button = self.create_button("Add", 'add', self.add_option)
        self.add_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.remove_button = self.create_button("Remove", 'remove', self.remove_option)
        self.remove_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.shuffle_button = self.create_button("Shuffle", 'shuffle', self.shuffle_options)
        self.shuffle_button.grid(row=0, column=4, padx=5, pady=5)
        
        # Secondary buttons
        self.save_button = self.create_button("Save", 'save', self.save_options)
        self.save_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.load_button = self.create_button("Load", 'load', self.load_options)
        self.load_button.grid(row=1, column=1, padx=5, pady=5)
        
        self.settings_button = self.create_button("Settings", 'settings', self.show_settings)
        self.settings_button.grid(row=1, column=2, padx=5, pady=5)
        
        self.history_button = self.create_button("History", 'history', self.show_history)
        self.history_button.grid(row=1, column=3, padx=5, pady=5)
        
        # Result display
        self.result_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.result_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.result_label = tk.Label(
            self.result_frame, 
            text="", 
            font=("Arial", 18, "bold"), 
            fg=self.highlight_color,
            bg=self.bg_color
        )
        self.result_label.pack()
        
        # Status bar
        self.status_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(
            self.status_frame, 
            text="Ready", 
            font=("Arial", 10), 
            fg="#b2bec3",
            bg=self.bg_color,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
        
        # Configure grid weights for buttons
        for i in range(5):
            self.control_frame.grid_columnconfigure(i, weight=1)
    
    def create_button(self, text, image_key, command, state=tk.NORMAL):
        """Create a styled button with icon"""
        btn = tk.Button(
            self.control_frame,
            text=text,
            image=self.images.get(image_key),
            compound=tk.LEFT,
            command=command,
            state=state,
            bg=self.button_color,
            fg=self.text_color,
            activebackground=self.button_hover,
            activeforeground=self.text_color,
            font=("Arial", 10, "bold"),
            borderwidth=0,
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        
        # Add hover effects
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.button_hover))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.button_color))
        
        return btn
    
    def draw_wheel(self, angle_offset=0):
        """Draw the wheel with current options"""
        self.canvas.delete("all")
        num_segments = len(self.options)
        
        if num_segments == 0:
            self.canvas.create_text(
                self.center[0], self.center[1], 
                text="Add options to begin!", 
                font=("Arial", 16), 
                fill="black"
            )
            return
        
        angle_per_segment = 360 / num_segments
        
        # Draw wheel segments
        for i, option in enumerate(self.options):
            start_angle = angle_offset + i * angle_per_segment
            color = self.colors[i % len(self.colors)]
            
            # Draw segment
            self.canvas.create_arc(
                self.center[0] - self.radius, self.center[1] - self.radius,
                self.center[0] + self.radius, self.center[1] + self.radius,
                start=start_angle, extent=angle_per_segment,
                fill=color, outline="white", width=2
            )
            
            # Draw option text
            mid_angle = math.radians(start_angle + angle_per_segment / 2)
            text_radius = self.radius * 0.7
            x = self.center[0] + math.cos(mid_angle) * text_radius
            y = self.center[1] - math.sin(mid_angle) * text_radius
            
            # Split long text into multiple lines
            words = option.split()
            lines = []
            current_line = []
            max_chars = 10
            
            for word in words:
                if len(' '.join(current_line + [word])) <= max_chars:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw each line of text
            line_height = 15
            for j, line in enumerate(lines):
                offset = (len(lines) - 1) * line_height / 2
                self.canvas.create_text(
                    x, y - offset + j * line_height,
                    text=line,
                    fill="white",
                    font=("Arial", 10, "bold"),
                    anchor="center",
                    angle=-start_angle - angle_per_segment / 2
                )
        
        # Draw center circle
        self.canvas.create_oval(
            self.center[0] - 30, self.center[1] - 30,
            self.center[0] + 30, self.center[1] + 30,
            fill="#2d3436", outline="white", width=2
        )
        
        # Draw arrow pointer
        arrow_size = 20
        self.canvas.create_polygon(
            self.center[0] - arrow_size, 50,
            self.center[0] + arrow_size, 50,
            self.center[0], 80,
            fill="#d63031", outline="white", width=2
        )
        
        # Draw decorative circle around arrow
        self.canvas.create_oval(
            self.center[0] - arrow_size - 10, 50 - arrow_size - 10,
            self.center[0] + arrow_size + 10, 50 + arrow_size + 10,
            outline="#fdcb6e", width=3, dash=(5, 3)
        )
    
    def start_spin(self):
        """Start spinning the wheel"""
        if self.spinning or not self.options:
            return
            
        self.spinning = True
        self.stopping = False
        self.spin_speed = random.uniform(20, 30)
        self.spin_start_time = time.time()
        self.result_label.config(text="")
        self.status_label.config(text="Spinning...")
        
        # Update button states
        self.spin_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Play sound if available
        if SOUND_AVAILABLE and self.sound_enabled:
            threading.Thread(target=self.play_spin_sound).start()
        
        self.animate_spin()
    
    def play_spin_sound(self):
        """Play spinning sound effect"""
        try:
            for _ in range(3):
                winsound.Beep(800, 100)
                time.sleep(0.05)
        except:
            pass
    
    def stop_spin(self):
        """Begin stopping the wheel"""
        if self.spinning:
            self.stopping = True
            self.status_label.config(text="Stopping...")
            
            # Play stop sound
            if SOUND_AVAILABLE and self.sound_enabled:
                threading.Thread(target=lambda: winsound.Beep(1200, 300)).start()
    
    def animate_spin(self):
        """Animate the spinning wheel"""
        if not self.spinning:
            return
        
        elapsed = time.time() - self.spin_start_time
        
        # Auto-stop after 5 seconds if not manually stopped
        if elapsed >= 5 and not self.stopping:
            self.stop_spin()
        
        # Update wheel position
        self.current_angle = (self.current_angle + self.spin_speed) % 360
        self.draw_wheel(angle_offset=self.current_angle)
        
        # Apply deceleration if stopping
        if self.stopping:
            self.spin_speed *= 0.96
            
            # Add random fluctuations to make stopping more natural
            if random.random() < 0.3:
                self.spin_speed *= random.uniform(0.9, 1.1)
            
            # Complete stop
            if self.spin_speed < 0.5:
                self.spinning = False
                self.show_result()
                return
        
        # Continue animation
        self.root.after(20, self.animate_spin)
    
    def show_result(self):
        """Display the winning option"""
        angle_per_segment = 360 / len(self.options)
        selected_index = int(((360 - self.current_angle + angle_per_segment / 2) % 360) // angle_per_segment)
        result = self.options[selected_index]
        self.last_result = result
        
        # Update UI
        self.result_label.config(text=f"🎉 Winner: {result} 🎉")
        self.status_label.config(text=f"Last result: {result}")
        
        # Add to history
        self.history.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "result": result
        })
        
        # Update button states
        self.spin_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Play win sound
        if SOUND_AVAILABLE and self.sound_enabled:
            threading.Thread(target=self.play_win_sound).start()
        
        # Start confetti animation
        self.start_confetti()
    
    def play_win_sound(self):
        """Play winning sound sequence"""
        try:
            winsound.Beep(1000, 200)
            time.sleep(0.1)
            winsound.Beep(1200, 200)
            time.sleep(0.1)
            winsound.Beep(1500, 300)
        except:
            pass
    
    def start_confetti(self):
        """Initialize confetti particles"""
        self.confetti_particles = []
        for _ in range(100):
            self.confetti_particles.append({
                'x': random.randint(0, self.canvas.winfo_width()),
                'y': random.randint(-50, 0),
                'size': random.randint(5, 15),
                'color': random.choice(self.colors),
                'speed': random.uniform(2, 5),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-5, 5),
                'shape': random.choice(['circle', 'square', 'triangle'])
            })
        
        self.animate_confetti()
    
    def animate_confetti(self):
        """Animate confetti falling"""
        if not self.confetti_particles:
            return
            
        self.canvas.delete("confetti")
        
        for particle in self.confetti_particles[:]:
            # Update position
            particle['y'] += particle['speed']
            particle['rotation'] += particle['rotation_speed']
            
            # Remove particles that fall off screen
            if particle['y'] > self.canvas.winfo_height():
                self.confetti_particles.remove(particle)
                continue
            
            # Draw particle
            x, y = particle['x'], particle['y']
            size = particle['size']
            color = particle['color']
            
            if particle['shape'] == 'circle':
                self.canvas.create_oval(
                    x, y, x + size, y + size,
                    fill=color, outline="", tags="confetti"
                )
            elif particle['shape'] == 'square':
                points = [
                    x, y,
                    x + size, y,
                    x + size, y + size,
                    x, y + size
                ]
                self.canvas.create_polygon(
                    points,
                    fill=color, outline="", tags="confetti"
                )
            else:  # triangle
                points = [
                    x + size/2, y,
                    x + size, y + size,
                    x, y + size
                ]
                self.canvas.create_polygon(
                    points,
                    fill=color, outline="", tags="confetti"
                )
        
        # Continue animation if there are still particles
        if self.confetti_particles:
            self.root.after(30, self.animate_confetti)
        else:
            # Redraw wheel when confetti is done
            self.draw_wheel(angle_offset=self.current_angle)
    
    def update_confetti(self):
        """Background thread to occasionally add more confetti"""
        while self.confetti_thread_running:
            if random.random() < 0.1 and not self.spinning and self.last_result:
                self.root.after(0, self.add_random_confetti)
            time.sleep(1)
    
    def add_random_confetti(self):
        """Add a few random confetti particles"""
        for _ in range(5):
            self.confetti_particles.append({
                'x': random.randint(0, self.canvas.winfo_width()),
                'y': random.randint(-50, 0),
                'size': random.randint(5, 15),
                'color': random.choice(self.colors),
                'speed': random.uniform(2, 5),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-5, 5),
                'shape': random.choice(['circle', 'square', 'triangle'])
            })
        
        if not any(tag == "confetti" for tag in self.canvas.find_all()):
            self.animate_confetti()
    
    def add_option(self):
        """Add a new option to the wheel"""
        new_option = simpledialog.askstring(
            "Add Option", 
            "Enter new option:",
            parent=self.root
        )
        
        if new_option and new_option.strip():
            if new_option not in self.options:
                self.options.append(new_option.strip())
                self.draw_wheel()
                self.status_label.config(text=f"Added: {new_option.strip()}")
            else:
                messagebox.showwarning(
                    "Duplicate Option", 
                    "This option already exists!",
                    parent=self.root
                )
    
    def remove_option(self):
        """Remove an option from the wheel"""
        if not self.options:
            messagebox.showinfo(
                "No Options", 
                "There are no options to remove.",
                parent=self.root
            )
            return
            
        # Create a selection dialog
        selection_dialog = tk.Toplevel(self.root)
        selection_dialog.title("Remove Option")
        selection_dialog.geometry("300x400")
        selection_dialog.resizable(False, False)
        selection_dialog.configure(bg=self.bg_color)
        
        tk.Label(
            selection_dialog, 
            text="Select option to remove:",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(pady=10)
        
        listbox = tk.Listbox(
            selection_dialog,
            selectmode=tk.SINGLE,
            font=("Arial", 11),
            bg="#636e72",
            fg="white",
            selectbackground=self.button_color,
            selectforeground="white"
        )
        
        for option in self.options:
            listbox.insert(tk.END, option)
        
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def remove_selected():
            selected = listbox.curselection()
            if selected:
                removed = self.options.pop(selected[0])
                self.draw_wheel()
                self.status_label.config(text=f"Removed: {removed}")
                selection_dialog.destroy()
        
        tk.Button(
            selection_dialog,
            text="Remove Selected",
            command=remove_selected,
            bg="#d63031",
            fg="white",
            activebackground="#ff7675",
            activeforeground="white",
            font=("Arial", 10, "bold")
        ).pack(pady=10)
    
    def shuffle_options(self):
        """Randomly shuffle the options"""
        if self.options:
            random.shuffle(self.options)
            self.draw_wheel()
            self.status_label.config(text="Options shuffled")
    
    def save_options(self):
        """Save options to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="wheel_options.json",
            title="Save Options"
        )
        
        if file_path:
            try:
                data = {
                    "options": self.options,
                    "last_result": self.last_result,
                    "history": self.history
                }
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                
                self.status_label.config(text=f"Options saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror(
                    "Save Error", 
                    f"Failed to save options:\n{str(e)}",
                    parent=self.root
                )
    
    def load_options(self):
        """Load options from a file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Load Options"
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.options = data.get("options", [])
                self.last_result = data.get("last_result", "")
                self.history = data.get("history", [])
                
                self.draw_wheel()
                self.status_label.config(text=f"Loaded {len(self.options)} options from {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror(
                    "Load Error", 
                    f"Failed to load options:\n{str(e)}",
                    parent=self.root
                )
        elif not self.options:
            # Default options if no file selected and no current options
            self.options = [
                "Free Coffee", "50% Off", "Free Dessert", 
                "VIP Treatment", "$100 Gift Card", "Free Meal",
                "10% Off", "Mystery Prize", "Free Appetizer",
                "20% Off", "Loyalty Points", "Try Again"
            ]
            self.draw_wheel()
    
    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("Settings")
        settings_dialog.geometry("400x300")
        settings_dialog.resizable(False, False)
        settings_dialog.configure(bg=self.bg_color)
        
        # Sound toggle
        sound_var = tk.BooleanVar(value=self.sound_enabled)
        tk.Checkbutton(
            settings_dialog,
            text="Enable Sounds",
            variable=sound_var,
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            selectcolor=self.bg_color
        ).pack(pady=10, anchor=tk.W, padx=20)
        
        # Theme toggle
        theme_var = tk.BooleanVar(value=self.dark_mode)
        tk.Checkbutton(
            settings_dialog,
            text="Dark Mode",
            variable=theme_var,
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            selectcolor=self.bg_color
        ).pack(pady=10, anchor=tk.W, padx=20)
        
        # Wheel color options
        tk.Label(
            settings_dialog,
            text="Wheel Colors:",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(pady=(20, 5), anchor=tk.W, padx=20)
        
        color_frame = tk.Frame(settings_dialog, bg=self.bg_color)
        color_frame.pack(fill=tk.X, padx=20)
        
        for i, color in enumerate(self.colors[:6]):  # Show first 6 colors as examples
            tk.Label(
                color_frame,
                text="",
                bg=color,
                width=4,
                height=2,
                relief=tk.RAISED
            ).grid(row=0, column=i, padx=2)
        
        # Save button
        def save_settings():
            self.sound_enabled = sound_var.get()
            self.dark_mode = theme_var.get()
            settings_dialog.destroy()
            self.status_label.config(text="Settings updated")
        
        tk.Button(
            settings_dialog,
            text="Save Settings",
            command=save_settings,
            bg=self.button_color,
            fg="white",
            activebackground=self.button_hover,
            activeforeground="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        ).pack(pady=20)
    
    def show_history(self):
        """Show history of previous results"""
        if not self.history:
            messagebox.showinfo(
                "No History", 
                "No spin history available yet.",
                parent=self.root
            )
            return
            
        history_dialog = tk.Toplevel(self.root)
        history_dialog.title("Spin History")
        history_dialog.geometry("500x400")
        history_dialog.configure(bg=self.bg_color)
        
        tk.Label(
            history_dialog,
            text="Previous Results:",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.highlight_color
        ).pack(pady=10)
        
        # Create a scrollable frame
        canvas = tk.Canvas(
            history_dialog,
            bg=self.bg_color,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            history_dialog,
            orient="vertical",
            command=canvas.yview
        )
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add history items (newest first)
        for item in reversed(self.history):
            frame = tk.Frame(
                scrollable_frame,
                bg="#636e72",
                padx=10,
                pady=5,
                relief=tk.RAISED,
                bd=1
            )
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                frame,
                text=item["time"],
                font=("Arial", 10),
                bg="#636e72",
                fg="#dfe6e9"
            ).pack(anchor=tk.W)
            
            tk.Label(
                frame,
                text=item["result"],
                font=("Arial", 12, "bold"),
                bg="#636e72",
                fg="#fdcb6e"
            ).pack(anchor=tk.W)
    
    def on_close(self):
        """Handle window close event"""
        self.confetti_thread_running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WheelOfLuckApp(root)
    root.mainloop()