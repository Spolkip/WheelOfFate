import math
import random
from PIL import Image, ImageTk
from constants import THEMES

class WheelRenderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.confetti_particles = []
        self.bg_photo = None
        self.cp_photo = None
        self.popup_photo = None
        self.cached_bg_path = None
        self.cached_cp_path = None

    def draw_all(self, app_state, angles, flapper_bends=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if self.bg_photo:
            self.draw_background(w, h, app_state.get("bg_path"))
            
        wheels = app_state.get("wheels", [])
        layout_style = app_state.get("layout_style", "Circle")
        if not wheels: return
        
        if not flapper_bends:
            flapper_bends = [0.0] * len(wheels)
        
        num_wheels = len(wheels)

        for i, wheel in enumerate(wheels):
            n = num_wheels
            radius = min(w / n, h) * 0.4
            cx = (i + 0.5) * (w / n)
            cy = h / 2
            theme = app_state.get("theme", "Default")
            cp_path = app_state.get("centerpiece_path")
            angle = angles[i] if i < len(angles) else 0
            bend = flapper_bends[i] if i < len(flapper_bends) else 0.0

            if layout_style == "Circle":
                self.draw_single_wheel(cx, cy, radius, wheel.get("options", []), angle, theme, cp_path, bend)
            elif layout_style == "Polygon":
                self.draw_polygon_wheel(wheel, angle, cx, cy, radius, THEMES.get(theme, THEMES["Default"]), bend)
            elif layout_style == "Vertical Slot":
                self.draw_vertical_slot(wheel, angle, cx, cy, radius, THEMES.get(theme, THEMES["Default"]))

    def draw_background(self, w, h, bg_path):
        if bg_path and bg_path != self.cached_bg_path:
            try:
                img = Image.open(bg_path).resize((int(w), int(h)), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(img)
                self.cached_bg_path = bg_path
            except:
                self.bg_photo = None
        if self.bg_photo:
            self.canvas.create_image(w/2, h/2, image=self.bg_photo)

    def draw_single_wheel(self, center_x, center_y, radius, options, current_angle, theme, cp_path, flapper_bend=0.0):
        if not options:
            self.canvas.create_text(center_x, center_y, text="Add options!", font=("Arial", 16, "bold"), fill="#a29bfe")
            return

        total_weight = sum(opt.get("weight", 1) for opt in options)
        if total_weight <= 0: return

        self.canvas.create_oval(center_x - radius - 5, center_y - radius + 15, center_x + radius + 15, center_y + radius + 15, fill="#1e1e1e", outline="")

        colors = THEMES.get(theme, THEMES["Default"])
        current_arc_start = current_angle

        for i, option in enumerate(options):
            weight = option.get("weight", 1)
            angle_extent = (weight / total_weight) * 360
            color = colors[i % len(colors)]
            
            self.canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=current_arc_start, extent=angle_extent,
                fill=color, outline="#2d3436", width=2
            )
            
            mid_angle = math.radians(current_arc_start + angle_extent / 2)
            text_radius = radius * 0.70
            x = center_x + math.cos(mid_angle) * text_radius
            y = center_y - math.sin(mid_angle) * text_radius
            
            words = str(option.get("name", "")).split()
            lines = []
            curr = []
            for w_ in words:
                if len(" ".join(curr + [w_])) <= 12:
                    curr.append(w_)
                else:
                    lines.append(" ".join(curr))
                    curr = [w_]
            if curr: lines.append(" ".join(curr))
            
            self.canvas.create_text(
                x, y,
                text="\n".join(lines), fill="#ffffff", font=("Arial", int(radius*0.05), "bold"),
                anchor="center", justify="center", angle=-current_arc_start - angle_extent / 2
            )
            
            current_arc_start += angle_extent
        
        # Centerpiece
        cp_size = int(radius * 0.25)
        drawn_cp = False
        if cp_path:
            if cp_path != self.cached_cp_path:
                try:
                    img = Image.open(cp_path).resize((cp_size*2, cp_size*2), Image.LANCZOS)
                    self.cp_photo = ImageTk.PhotoImage(img)
                    self.cached_cp_path = cp_path
                except:
                    self.cp_photo = None
            if self.cp_photo:
                self.canvas.create_image(center_x, center_y, image=self.cp_photo)
                drawn_cp = True
                
        if not drawn_cp:
            self.canvas.create_oval(center_x - cp_size, center_y - cp_size, center_x + cp_size, center_y + cp_size, fill="#2d3436", outline="#ffffff", width=3)
            self.canvas.create_oval(center_x - 15, center_y - 15, center_x + 15, center_y + 15, fill="#fdcb6e", outline="")

        # Draw flapper
        arrow_size = int(radius * 0.1)
        base_x, base_y = center_x, center_y - radius - 10
        tip_x, tip_y = center_x, center_y - radius + 20
        
        # Calculate rotation for flapper (max bend = 30 degrees backwards, which is positive or negative depending on spin direction. We assume counter-clockwise spin, so bend right = positive rotation)
        # Bend goes from 0.0 to 1.0
        bend_angle_rad = math.radians(flapper_bend * 30.0)
        
        # Function to rotate a point around the base (pivot)
        def rot_p(x, y):
            dx, dy = x - base_x, y - base_y
            rx = dx * math.cos(bend_angle_rad) - dy * math.sin(bend_angle_rad)
            ry = dx * math.sin(bend_angle_rad) + dy * math.cos(bend_angle_rad)
            return base_x + rx, base_y + ry
            
        p1 = rot_p(center_x - arrow_size, center_y - radius - 10)
        p2 = rot_p(center_x + arrow_size, center_y - radius - 10)
        p3 = rot_p(center_x, center_y - radius + 20)

        self.canvas.create_polygon(
            p1[0], p1[1],
            p2[0], p2[1],
            p3[0], p3[1],
            fill="#d63031", outline="#ffffff", width=2
        )

    def draw_polygon_wheel(self, wheel, angle_offset, center_x, center_y, radius, colors, flapper_bend=0.0):
        options = wheel["options"]
        if not options: return
        
        total_weight = sum(opt.get("weight", 1) for opt in options)
        current_arc_start = -angle_offset
        
        for i, option in enumerate(options):
            angle_extent = (option.get("weight", 1) / total_weight) * 360
            color = colors[i % len(colors)]
            
            p1_x = center_x + math.cos(math.radians(current_arc_start)) * radius
            p1_y = center_y - math.sin(math.radians(current_arc_start)) * radius
            p2_x = center_x + math.cos(math.radians(current_arc_start + angle_extent)) * radius
            p2_y = center_y - math.sin(math.radians(current_arc_start + angle_extent)) * radius
            
            self.canvas.create_polygon(
                center_x, center_y, p1_x, p1_y, p2_x, p2_y,
                fill=color, outline="#2b2b2b", width=3
            )
            
            mid_angle = math.radians(current_arc_start + angle_extent / 2)
            text_radius = radius * 0.70
            x = center_x + math.cos(mid_angle) * text_radius
            y = center_y - math.sin(mid_angle) * text_radius
            
            words = str(option.get("name", "")).split()
            lines = []
            curr = []
            for w_ in words:
                if len(" ".join(curr + [w_])) <= 12: curr.append(w_)
                else: lines.append(" ".join(curr)); curr = [w_]
            if curr: lines.append(" ".join(curr))
            
            self.canvas.create_text(
                x, y,
                text="\n".join(lines), fill="#ffffff", font=("Arial", int(radius*0.05), "bold"),
                anchor="center", justify="center", angle=-current_arc_start - angle_extent / 2
            )
            current_arc_start += angle_extent
            
        if self.cp_photo:
            self.canvas.create_image(center_x, center_y, image=self.cp_photo)
        else:
            self.canvas.create_oval(center_x - radius*0.2, center_y - radius*0.2, center_x + radius*0.2, center_y + radius*0.2, fill="#2b2b2b", outline="#ffffff", width=2)
            self.canvas.create_oval(center_x - radius*0.1, center_y - radius*0.1, center_x + radius*0.1, center_y + radius*0.1, fill="#fdcb6e")

        # Draw flapper
        arrow_size = int(radius * 0.1)
        base_x, base_y = center_x, center_y - radius - 10
        tip_x, tip_y = center_x, center_y - radius + 20
        
        bend_angle_rad = math.radians(flapper_bend * 30.0)
        
        def rot_p(x, y):
            dx, dy = x - base_x, y - base_y
            rx = dx * math.cos(bend_angle_rad) - dy * math.sin(bend_angle_rad)
            ry = dx * math.sin(bend_angle_rad) + dy * math.cos(bend_angle_rad)
            return base_x + rx, base_y + ry
            
        p1 = rot_p(center_x - arrow_size, center_y - radius - 10)
        p2 = rot_p(center_x + arrow_size, center_y - radius - 10)
        p3 = rot_p(center_x, center_y - radius + 20)

        self.canvas.create_polygon(
            p1[0], p1[1],
            p2[0], p2[1],
            p3[0], p3[1],
            fill="#d63031", outline="#ffffff", width=2
        )

    def draw_vertical_slot(self, wheel, angle_offset, center_x, center_y, radius, colors):
        options = wheel["options"]
        if not options: return
        slot_width = radius * 1.5
        total_height = radius * 2.0
        
        self.canvas.create_rectangle(center_x - slot_width/2, center_y - total_height/2, center_x + slot_width/2, center_y + total_height/2, fill="#2b2b2b", outline="#ffffff", width=4)
        
        total_weight = sum(opt.get("weight", 1) for opt in options)
        tape_height = total_height * max(1.5, len(options) * 0.2)
        pointer_angle = 90
        effective_angle = (pointer_angle - angle_offset) % 360
        
        for loop in [-1, 0, 1]:
            current_angle_sum = 0
            for i, opt in enumerate(options):
                angle_extent = (opt.get("weight", 1) / total_weight) * 360
                slice_mid_angle = current_angle_sum + angle_extent / 2
                angle_diff = slice_mid_angle - effective_angle + (loop * 360)
                y_pos = center_y + (angle_diff / 360) * tape_height
                slice_height = (angle_extent / 360) * tape_height
                
                if center_y - total_height/2 - slice_height/2 <= y_pos <= center_y + total_height/2 + slice_height/2:
                    color = colors[i % len(colors)]
                    self.canvas.create_rectangle(
                        center_x - slot_width/2 + 4, y_pos - slice_height/2,
                        center_x + slot_width/2 - 4, y_pos + slice_height/2,
                        fill=color, outline="#ffffff"
                    )
                    self.canvas.create_text(
                        center_x, y_pos,
                        text=opt.get("name", ""), fill="#ffffff", font=("Arial", int(radius*0.06), "bold")
                    )
                current_angle_sum += angle_extent
                
        self.canvas.create_polygon(
            center_x - slot_width/2 - 20, center_y,
            center_x - slot_width/2 - 5, center_y - 10,
            center_x - slot_width/2 - 5, center_y + 10,
            fill="#d63031", outline="#ffffff", width=2
        )
        self.canvas.create_polygon(
            center_x + slot_width/2 + 20, center_y,
            center_x + slot_width/2 + 5, center_y - 10,
            center_x + slot_width/2 + 5, center_y + 10,
            fill="#d63031", outline="#ffffff", width=2
        )

    def show_custom_option_image(self, path):
        if not path: return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        try:
            img = Image.open(path)
            img.thumbnail((int(w*0.5), int(h*0.5)), Image.LANCZOS)
            self.popup_photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(w/2, h/2, image=self.popup_photo, tags="popup_image")
        except Exception as e:
            print("Failed to load custom image:", e)

    def spawn_particles(self, style, theme, count=150):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        colors = THEMES.get(theme, THEMES["Default"])
        
        if style == "Falling Money":
            count = min(count, 40)
            
        for _ in range(count):
            if style == "Confetti":
                self.confetti_particles.append({
                    'type': 'confetti',
                    'x': random.randint(0, w),
                    'y': random.randint(-100, 0),
                    'size': random.randint(6, 12),
                    'color': random.choice(colors),
                    'speed_y': random.uniform(3, 8),
                    'speed_x': random.uniform(-2, 2),
                    'shape': random.choice(['circle', 'square'])
                })
            elif style == "Falling Money":
                self.confetti_particles.append({
                    'type': 'money',
                    'x': random.randint(0, w),
                    'y': random.randint(-100, 0),
                    'size': random.randint(15, 30),
                    'color': '#27ae60',
                    'speed_y': random.uniform(8, 15),
                    'speed_x': random.uniform(-1, 1)
                })
            elif style == "Fireworks":
                self.confetti_particles.append({
                    'type': 'firework_shell',
                    'x': random.randint(int(w*0.2), int(w*0.8)),
                    'y': h,
                    'target_y': random.randint(int(h*0.1), int(h*0.5)),
                    'color': random.choice(colors),
                    'speed_y': random.uniform(-15, -10),
                    'speed_x': random.uniform(-2, 2)
                })

    def spawn_explosion(self, x, y, color):
        for _ in range(40):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(3, 10)
            self.confetti_particles.append({
                'type': 'firework_spark',
                'x': x,
                'y': y,
                'size': random.randint(4, 8),
                'color': color,
                'speed_x': math.cos(angle) * speed,
                'speed_y': math.sin(angle) * speed,
                'life': 1.0
            })

    def update_particles(self):
        if not self.confetti_particles: return False
        self.canvas.delete("particles")
        h = self.canvas.winfo_height()
        
        alive_particles = []
        for p in self.confetti_particles:
            ptype = p.get('type')
            if ptype == 'confetti':
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                p['speed_y'] += 0.1
                if p['y'] < h:
                    alive_particles.append(p)
                    if p['shape'] == 'circle':
                        self.canvas.create_oval(p['x'], p['y'], p['x']+p['size'], p['y']+p['size'], fill=p['color'], outline="", tags="particles")
                    else:
                        self.canvas.create_rectangle(p['x'], p['y'], p['x']+p['size'], p['y']+p['size'], fill=p['color'], outline="", tags="particles")
            
            elif ptype == 'money':
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                p['speed_y'] += 0.05
                if p['y'] < h:
                    alive_particles.append(p)
                    self.canvas.create_rectangle(p['x'], p['y'], p['x']+p['size']*2, p['y']+p['size'], fill=p['color'], outline="#1e8449", tags="particles")
                    self.canvas.create_text(p['x']+p['size'], p['y']+p['size']/2, text="$", fill="#fff", font=("Arial", int(p['size']*0.6), "bold"), tags="particles")
            
            elif ptype == 'firework_shell':
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                if p['speed_y'] >= 0 or p['y'] <= p['target_y']:
                    self.spawn_explosion(p['x'], p['y'], p['color'])
                else:
                    if p['y'] > 0:
                        alive_particles.append(p)
                        self.canvas.create_oval(p['x']-4, p['y']-4, p['x']+4, p['y']+4, fill=p['color'], outline="", tags="particles")

            elif ptype == 'firework_spark':
                p['x'] += p['speed_x']
                p['y'] += p['speed_y']
                p['speed_y'] += 0.2
                p['life'] -= 0.02
                if p['life'] > 0 and p['y'] < h:
                    alive_particles.append(p)
                    size = p['size'] * p['life']
                    self.canvas.create_oval(p['x']-size, p['y']-size, p['x']+size, p['y']+size, fill=p['color'], outline="", tags="particles")

        self.confetti_particles = alive_particles
        return bool(self.confetti_particles)
