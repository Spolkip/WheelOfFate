import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import math
import random
import time
import threading
import os

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class WheelOfLuckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wheel of Luck")
        self.canvas = tk.Canvas(root, width=500, height=500, bg='white')
        self.canvas.pack()

        self.center = (250, 250)
        self.radius = 200
        self.options = []
        self.colors = ["red", "green", "yellow", "blue", "magenta", "cyan"]
        self.current_angle = 0
        self.spin_speed = 0
        self.spinning = False
        self.stopping = False
        self.spin_start_time = 0

        self.load_options()

        # Buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Spin", command=self.start_spin).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Stop", command=self.stop_spin).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Add Option", command=self.add_option).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Remove Option", command=self.remove_option).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="Shuffle", command=self.shuffle_options).grid(row=0, column=4, padx=5)
        tk.Button(button_frame, text="Save", command=self.save_options).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(button_frame, text="Load", command=self.load_options).grid(row=1, column=1, padx=5, pady=5)

        self.result_label = tk.Label(root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        self.draw_wheel()

    def draw_wheel(self, angle_offset=0):
        self.canvas.delete("all")
        num_segments = len(self.options)
        if num_segments == 0:
            self.canvas.create_text(250, 250, text="No options!", font=("Arial", 16), fill="black")
            return

        angle_per_segment = 360 / num_segments

        for i, option in enumerate(self.options):
            start_angle = angle_offset + i * angle_per_segment
            color = self.colors[i % len(self.colors)]
            self.canvas.create_arc(
                self.center[0] - self.radius, self.center[1] - self.radius,
                self.center[0] + self.radius, self.center[1] + self.radius,
                start=start_angle, extent=angle_per_segment,
                fill=color, outline="black"
            )
            mid_angle = math.radians(start_angle + angle_per_segment / 2)
            x = self.center[0] + math.cos(mid_angle) * (self.radius / 1.5)
            y = self.center[1] - math.sin(mid_angle) * (self.radius / 1.5)
            self.canvas.create_text(x, y, text=option, fill="white", font=("Arial", 10), anchor="center")

        # Arrow
        self.canvas.create_polygon(240, 10, 260, 10, 250, 30, fill="black")

    def start_spin(self):
        if self.spinning or not self.options:
            return
        self.spinning = True
        self.stopping = False
        self.spin_speed = random.uniform(20, 30)
        self.spin_start_time = time.time()
        self.result_label.config(text="")
        self.animate_spin()

    def stop_spin(self):
        if self.spinning:
            self.stopping = True

    def animate_spin(self):
        if not self.spinning:
            return

        elapsed = time.time() - self.spin_start_time
        if elapsed >= 5:
            self.stop_spin()

        self.current_angle = (self.current_angle + self.spin_speed) % 360
        self.draw_wheel(angle_offset=self.current_angle)

        if self.stopping:
            self.spin_speed *= 0.96
            if self.spin_speed < 0.5:
                self.spinning = False
                self.show_result()
                return

        self.root.after(20, self.animate_spin)

    def show_result(self):
        angle_per_segment = 360 / len(self.options)
        selected_index = int(((360 - self.current_angle + angle_per_segment / 2) % 360) // angle_per_segment)
        result = self.options[selected_index]
        self.result_label.config(text=f"🎉 You won: {result} 🎉")

        if SOUND_AVAILABLE:
            threading.Thread(target=lambda: winsound.MessageBeep()).start()

        self.animate_confetti()

    def animate_confetti(self):
        for _ in range(50):
            x = random.randint(10, 490)
            y = random.randint(10, 490)
            color = random.choice(self.colors)
            size = random.randint(2, 6)
            self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")
        self.root.after(1000, self.draw_wheel)

    def add_option(self):
        new_option = simpledialog.askstring("Add Option", "Enter new option:")
        if new_option and new_option not in self.options:
            self.options.append(new_option)
            self.draw_wheel()

    def remove_option(self):
        if not self.options:
            messagebox.showinfo("Remove Option", "No options to remove.")
            return
        selected = simpledialog.askstring("Remove Option", f"Options:\n{', '.join(self.options)}\n\nEnter one to remove:")
        if selected in self.options:
            self.options.remove(selected)
            self.draw_wheel()

    def shuffle_options(self):
        random.shuffle(self.options)
        self.draw_wheel()

    def save_options(self):
        with open("options.txt", "w", encoding="utf-8") as f:
            for opt in self.options:
                f.write(opt + "\n")
        messagebox.showinfo("Save", "Options saved to options.txt")

    def load_options(self):
        if os.path.exists("options.txt"):
            with open("options.txt", "r", encoding="utf-8") as f:
                self.options = [line.strip() for line in f if line.strip()]
        elif not self.options:
            self.options = [
                "Free Coffee", "50% Off", "Free Dessert", "Try Again",
                "VIP Treatment", "$100 Gift Card", "Free Meal",
                "10% Off", "Mystery Prize", "Free Appetizer",
                "20% Off", "Loyalty Points"
            ]
        self.draw_wheel()


if __name__ == "__main__":
    root = tk.Tk()
    app = WheelOfLuckApp(root)
    root.mainloop()
