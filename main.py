import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import threading
import random
from constants import THEMES, ease_out_quart
from audio_manager import AudioManager
from profile_manager import ProfileManager
from dialogs import OptionDialog, ListboxDialog, HistoryDialog
from wheel_renderer import WheelRenderer
from twitch_client import TwitchClient
from stats_dashboard import StatsDashboard
from discord_rpc import DiscordWebhook

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class WheelOfLuckApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✨ Premium Wheel of Fortune ✨")
        self.geometry("1100x800")
        self.minsize(900, 600)

        self.app_state = {}
        self.angles = []
        self.last_slice_indices = []
        self.last_result = ""
        self.sidebar_visible = True
        
        self.spinning = False
        self.charging = False
        self.charge_start_time = 0
        self.spin_duration = 0
        self.spin_start_time = 0
        self.spin_start_angles = []
        self.spin_target_angles = []
        
        self.active_wheel_index = 0
        self.party_mode = False
        self.particle_thread_running = True
        
        self.audio_manager = AudioManager()
        self.profile_manager = ProfileManager(self.app_state, self.on_profile_changed)
        self.twitch_client = TwitchClient("", "", self.trigger_spin_from_twitch)
        self.discord_webhook = DiscordWebhook()
        
        for k in ["1", "2", "3", "4", "5"]:
            self.bind(f"<KeyPress-{k}>", lambda e, key=k: self.audio_manager.play_soundboard(key, self.app_state.get("soundboard", {})))
        
        self.setup_ui()
        self.renderer = WheelRenderer(self.canvas)
        
        self.profile_manager.initialize()
        
        self.particle_thread = threading.Thread(target=self.particle_worker, daemon=True)
        self.particle_thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Configure>", self.on_resize)

    def trigger_spin_from_twitch(self):
        self.after(0, self.on_spin_press, None)
        self.after(1000, self.on_spin_release, None)

    def on_profile_changed(self):
        self.update_profile_dropdown()
        self.theme_var.set(self.app_state.get("theme", "Default"))
        self.elimination_var.set(self.app_state.get("elimination_mode", False))
        self.particle_style_var.set(self.app_state.get("particle_style", "Confetti"))
        self.layout_style_var.set(self.app_state.get("layout_style", "Circle"))
        
        wheels = self.app_state.get("wheels", [])
        if self.active_wheel_index >= len(wheels):
            self.active_wheel_index = max(0, len(wheels)-1)
        self.update_wheel_tabs()
        players = self.app_state.get("players", ["Guest"])
        if hasattr(self, 'player_dropdown'):
            self.player_dropdown.configure(values=players)
            if self.player_var.get() not in players:
                self.player_var.set(players[0])
        
        # Reset angles based on wheels count
        self.angles = [0] * len(wheels)
        self.last_slice_indices = [-1] * len(wheels)
        self.flapper_bends = [0.0] * len(wheels)
        self.angular_velocities = [0.0] * len(wheels)
        
        self.audio_manager.bg_music = self.app_state.get("bg_music")
        if self.audio_manager.bg_music and self.audio_manager.enabled:
            self.audio_manager.play_bg_music(0.3)
            
        self.draw_wheel()

    def update_profile_dropdown(self):
        profiles = self.profile_manager.get_profiles_list()
        self.profile_dropdown.configure(values=profiles)
        self.profile_var.set(self.profile_manager.current_profile[:-5])

    def update_wheel_tabs(self):
        wheels = self.app_state.get("wheels", [])
        opts = [w["name"] for w in wheels]
        if not opts: opts = ["Wheel 1"]
        self.wheel_tab_var.set(opts[self.active_wheel_index])
        self.wheel_tab_dropdown.configure(values=opts)

    def switch_wheel_tab(self, val):
        wheels = self.app_state.get("wheels", [])
        for i, w in enumerate(wheels):
            if w["name"] == val:
                self.active_wheel_index = i
                break

    def get_active_options(self):
        wheels = self.app_state.get("wheels", [])
        if self.active_wheel_index < len(wheels):
            return wheels[self.active_wheel_index]["options"]
        return []

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Wheel of Fortune\n✨", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.controls_frame = ctk.CTkScrollableFrame(self.sidebar_frame)
        self.controls_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.controls_frame, text="Current Player", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.player_var = ctk.StringVar(value="Guest")
        self.player_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.player_var, values=["Guest"])
        self.player_dropdown.pack(fill="x", pady=(0, 5))
        
        def add_player():
            dialog = ctk.CTkInputDialog(text="Enter new player name:", title="New Player")
            name = dialog.get_input()
            if name:
                players = self.app_state.setdefault("players", ["Guest"])
                if name not in players:
                    players.append(name)
                    self.player_dropdown.configure(values=players)
                    self.player_var.set(name)
                    self.profile_manager.save_current_profile()
                    
        self.add_player_btn = ctk.CTkButton(self.controls_frame, text="Add Player", command=add_player)
        self.add_player_btn.pack(fill="x", pady=(0, 20))
        
        self.spin_btn = ctk.CTkButton(self.controls_frame, text="Hold to SPIN!", font=ctk.CTkFont(size=20, weight="bold"), height=50, fg_color="#e17055", hover_color="#d63031")
        self.spin_btn.pack(fill="x", pady=(0, 10))
        self.spin_btn.bind("<ButtonPress-1>", self.on_spin_press)
        self.spin_btn.bind("<ButtonRelease-1>", self.on_spin_release)
        
        self.party_btn = ctk.CTkButton(self.controls_frame, text="Party Mode (Fullscreen)", fg_color="#6c5ce7", hover_color="#a29bfe", command=self.toggle_party_mode)
        self.party_btn.pack(fill="x", pady=(0, 20))

        # Multi-Wheel Control
        ctk.CTkLabel(self.controls_frame, text="Manage Wheels", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        tab_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        tab_frame.pack(fill="x", pady=(0, 5))
        
        self.wheel_tab_var = ctk.StringVar(value="Wheel 1")
        self.wheel_tab_dropdown = ctk.CTkOptionMenu(tab_frame, variable=self.wheel_tab_var, command=self.switch_wheel_tab)
        self.wheel_tab_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def add_wheel():
            wheels = self.app_state.get("wheels", [])
            wheels.append({"name": f"Wheel {len(wheels)+1}", "options": []})
            self.active_wheel_index = len(wheels)-1
            self.on_profile_changed()
            self.profile_manager.save_current_profile()
            
        def remove_wheel():
            wheels = self.app_state.get("wheels", [])
            if len(wheels) > 1:
                wheels.pop(self.active_wheel_index)
                self.active_wheel_index = 0
                self.on_profile_changed()
                self.profile_manager.save_current_profile()
            else:
                messagebox.showwarning("Error", "You must have at least one wheel!")
                
        ctk.CTkButton(tab_frame, text="+", width=30, command=add_wheel).pack(side="left", padx=2)
        ctk.CTkButton(tab_frame, text="-", width=30, fg_color="#d63031", hover_color="#ff7675", command=remove_wheel).pack(side="left")

        # Options Management
        def show_add():
            OptionDialog.show(self, "Add Option", self.get_active_options(), self.app_state.get("wheels", []), self.draw_wheel, self.profile_manager.save_current_profile)
        def show_edit():
            ListboxDialog.show(self, "Edit Option", self.get_active_options(), lambda idx, d: OptionDialog.show(self, "Edit Option", self.get_active_options(), self.app_state.get("wheels", []), self.draw_wheel, self.profile_manager.save_current_profile, idx), "Edit", is_edit=True)
        def show_remove():
            def do_remove(idx, d):
                self.get_active_options().pop(idx)
                self.draw_wheel()
                self.profile_manager.save_current_profile()
            ListboxDialog.show(self, "Remove Option", self.get_active_options(), do_remove, "Remove")
            
        self.add_btn = ctk.CTkButton(self.controls_frame, text="Add Option to Wheel", command=show_add)
        self.add_btn.pack(fill="x", pady=(0, 5))
        self.edit_btn = ctk.CTkButton(self.controls_frame, text="Edit Option (Weights)", command=show_edit)
        self.edit_btn.pack(fill="x", pady=(0, 5))
        self.remove_btn = ctk.CTkButton(self.controls_frame, text="Remove Option", command=show_remove)
        self.remove_btn.pack(fill="x", pady=(0, 10))
        
        def load_preset(val):
            if val == "Select Preset...": return
            presets = {
                "Yes / No / Maybe": [{"name": "Yes", "weight": 1}, {"name": "No", "weight": 1}, {"name": "Maybe", "weight": 1}],
                "Truth or Dare": [{"name": "Truth", "weight": 1}, {"name": "Dare", "weight": 1}],
                "What's for Dinner?": [{"name": "Pizza", "weight": 1}, {"name": "Burgers", "weight": 1}, {"name": "Sushi", "weight": 1}, {"name": "Tacos", "weight": 1}, {"name": "Salad", "weight": 1}],
                "Roll a D20": [{"name": str(i), "weight": 1} for i in range(1, 21)]
            }
            if val in presets:
                wheels = self.app_state.get("wheels", [])
                if self.active_wheel_index < len(wheels):
                    wheels[self.active_wheel_index]["options"] = list(presets[val])
                    self.draw_wheel()
                    self.profile_manager.save_current_profile()
            self.preset_var.set("Select Preset...")

        self.preset_var = ctk.StringVar(value="Select Preset...")
        self.preset_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.preset_var, values=["Select Preset...", "Yes / No / Maybe", "Truth or Dare", "What's for Dinner?", "Roll a D20"], command=load_preset)
        self.preset_dropdown.pack(fill="x", pady=(0, 20))

        # Profiles
        ctk.CTkLabel(self.controls_frame, text="Profiles", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.profile_var = ctk.StringVar(value="default")
        self.profile_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.profile_var, command=self.profile_manager.switch_profile)
        self.profile_dropdown.pack(fill="x", pady=(0, 5))
        
        def new_profile():
            dialog = ctk.CTkInputDialog(text="Enter new profile name:", title="New Profile")
            name = dialog.get_input()
            if name: self.profile_manager.new_profile(name)

        self.new_profile_btn = ctk.CTkButton(self.controls_frame, text="New Profile", command=new_profile)
        self.new_profile_btn.pack(fill="x", pady=(0, 5))
        self.save_profile_btn = ctk.CTkButton(self.controls_frame, text="Save Profile", command=self.profile_manager.save_current_profile)
        self.save_profile_btn.pack(fill="x", pady=(0, 5))
        self.delete_profile_btn = ctk.CTkButton(self.controls_frame, text="Delete Profile", fg_color="#d63031", hover_color="#ff7675", command=self.profile_manager.delete_profile)
        self.delete_profile_btn.pack(fill="x", pady=(0, 5))
        
        self.import_btn = ctk.CTkButton(self.controls_frame, text="Import Profile", command=self.profile_manager.import_profile)
        self.import_btn.pack(fill="x", pady=(0, 5))
        self.export_btn = ctk.CTkButton(self.controls_frame, text="Export Profile", command=self.profile_manager.export_profile)
        self.export_btn.pack(fill="x", pady=(0, 20))

        # Settings
        ctk.CTkLabel(self.controls_frame, text="Appearance", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.theme_var = ctk.StringVar(value="Default")
        def change_theme(val):
            self.app_state["theme"] = val
            self.draw_wheel()
            self.profile_manager.save_current_profile()
        self.theme_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.theme_var, values=list(THEMES.keys()), command=change_theme)
        self.theme_dropdown.pack(fill="x", pady=(0, 5))
        
        self.layout_style_var = ctk.StringVar(value="Circle")
        def change_layout(val):
            self.app_state["layout_style"] = val
            self.draw_wheel()
            self.profile_manager.save_current_profile()
        self.layout_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.layout_style_var, values=["Circle", "Polygon", "Vertical Slot"], command=change_layout)
        self.layout_dropdown.pack(fill="x", pady=(0, 5))
        
        self.particle_style_var = ctk.StringVar(value="Confetti")
        def change_pstyle(val):
            self.app_state["particle_style"] = val
            self.profile_manager.save_current_profile()
        self.particle_dropdown = ctk.CTkOptionMenu(self.controls_frame, variable=self.particle_style_var, values=["Confetti", "Falling Money", "Fireworks"], command=change_pstyle)
        self.particle_dropdown.pack(fill="x", pady=(0, 5))

        def load_bg():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path:
                self.app_state["background_image"] = path
                self.draw_wheel()
                self.profile_manager.save_current_profile()
                
        def load_cp():
            path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if path:
                self.app_state["centerpiece_image"] = path
                self.draw_wheel()
                self.profile_manager.save_current_profile()
                
        self.set_bg_btn = ctk.CTkButton(self.controls_frame, text="Set Custom Background", command=load_bg)
        self.set_bg_btn.pack(fill="x", pady=(0, 5))
        self.set_cp_btn = ctk.CTkButton(self.controls_frame, text="Set Custom Centerpiece", command=load_cp)
        self.set_cp_btn.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.controls_frame, text="Gameplay & Audio", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        self.elimination_var = ctk.BooleanVar(value=False)
        def toggle_elimination():
            self.app_state["elimination_mode"] = self.elimination_var.get()
            self.profile_manager.save_current_profile()
        self.elimination_toggle = ctk.CTkSwitch(self.controls_frame, text="Winner Elimination", variable=self.elimination_var, command=toggle_elimination)
        self.elimination_toggle.pack(fill="x", pady=(0, 5))
        
        def toggle_snd():
            state = "ON" if self.audio_manager.toggle_sound() else "OFF"
            self.sound_btn.configure(text=f"Sound: {state}")
        self.sound_btn = ctk.CTkButton(self.controls_frame, text="Sound: ON", command=toggle_snd)
        self.sound_btn.pack(fill="x", pady=(0, 5))
        
        def toggle_tts():
            state = "ON" if self.audio_manager.toggle_tts() else "OFF"
            self.tts_btn.configure(text=f"TTS Announcer: {state}")
        self.tts_btn = ctk.CTkButton(self.controls_frame, text="TTS Announcer: ON", command=toggle_tts)
        self.tts_btn.pack(fill="x", pady=(0, 5))
        
        self.set_spin_sound_btn = ctk.CTkButton(self.controls_frame, text="Set Custom Spin Sound", command=self.audio_manager.load_spin_sound)
        self.set_spin_sound_btn.pack(fill="x", pady=(0, 5))
        self.set_win_sound_btn = ctk.CTkButton(self.controls_frame, text="Set Custom Win Sound", command=self.audio_manager.load_win_sound)
        self.set_win_sound_btn.pack(fill="x", pady=(0, 5))
        
        def set_bg():
            self.audio_manager.load_bg_music()
            if self.audio_manager.bg_music:
                self.app_state["bg_music"] = self.audio_manager.bg_music
                self.profile_manager.save_current_profile()
                
        self.set_bg_music_btn = ctk.CTkButton(self.controls_frame, text="Set Background Music", command=set_bg)
        self.set_bg_music_btn.pack(fill="x", pady=(0, 5))

        def configure_soundboard():
            dialog = ctk.CTkToplevel(self)
            dialog.title("Soundboard Config")
            dialog.geometry("300x350")
            dialog.attributes("-topmost", True)
            
            sb = self.app_state.setdefault("soundboard", {})
            for key in ["1", "2", "3", "4", "5"]:
                frame = ctk.CTkFrame(dialog, fg_color="transparent")
                frame.pack(fill="x", pady=5, padx=10)
                ctk.CTkLabel(frame, text=f"Key {key}:").pack(side="left")
                
                path_var = tk.StringVar(value="..."+sb[key][-15:] if key in sb else "Not set")
                ctk.CTkLabel(frame, textvariable=path_var, width=120, anchor="w").pack(side="left", padx=10)
                
                def set_snd(k=key, var=path_var):
                    p = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
                    if p:
                        sb[k] = p
                        var.set("..."+p[-15:])
                        self.profile_manager.save_current_profile()
                        
                ctk.CTkButton(frame, text="Set", width=40, command=set_snd).pack(side="right")
                
        self.soundboard_btn = ctk.CTkButton(self.controls_frame, text="Soundboard Hotkeys (1-5)", command=configure_soundboard)
        self.soundboard_btn.pack(fill="x", pady=(0, 20))
        
        def show_hist():
            HistoryDialog.show(self, self.app_state["history"], self.profile_manager.save_current_profile, self.profile_manager.export_history_csv)
        self.history_btn = ctk.CTkButton(self.controls_frame, text="Spin History & Export", command=show_hist)
        self.history_btn.pack(fill="x", pady=(0, 5))

        def show_stats():
            StatsDashboard.show(self, self.app_state["history"], THEMES.get(self.app_state.get("theme", "Default"), THEMES["Default"]))
        self.stats_btn = ctk.CTkButton(self.controls_frame, text="Detailed Statistics", command=show_stats)
        self.stats_btn.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.controls_frame, text="Integrations", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        def connect_discord():
            if self.discord_webhook.connected:
                self.discord_webhook.disconnect()
                self.discord_btn.configure(text="Connect Discord Webhook", fg_color="#7289DA")
                return

            dialog = ctk.CTkToplevel(self)
            dialog.title("Discord Webhook")
            dialog.geometry("400x150")
            dialog.attributes("-topmost", True)
            ctk.CTkLabel(dialog, text="Webhook URL:").pack(pady=5)
            id_entry = ctk.CTkEntry(dialog, width=350)
            id_entry.insert(0, self.app_state.get("discord_webhook_url", ""))
            id_entry.pack(pady=5)
            def do_connect():
                client_id = id_entry.get().strip()
                self.app_state["discord_webhook_url"] = client_id
                self.profile_manager.save_current_profile()
                self.discord_btn.configure(text="Connecting...", fg_color="#f39c12")
                
                def on_status(success):
                    if success:
                        self.after(0, lambda: self.discord_btn.configure(text="Discord: Connected (Disconnect)", fg_color="#2ecc71"))
                    else:
                        self.after(0, lambda: self.discord_btn.configure(text="Connect Discord Webhook", fg_color="#7289DA"))
                        self.after(0, lambda: messagebox.showerror("Discord Webhook", "Invalid Webhook URL."))
                        
                self.discord_webhook.connect(client_id, on_status)
                dialog.destroy()
            ctk.CTkButton(dialog, text="Connect", command=do_connect).pack(pady=10)
            
        self.discord_btn = ctk.CTkButton(self.controls_frame, text="Connect Discord Webhook", fg_color="#7289DA", hover_color="#89a1f5", command=connect_discord)
        self.discord_btn.pack(fill="x", pady=(0, 5))

        def connect_twitch():
            dialog = ctk.CTkToplevel(self)
            dialog.title("Twitch Auth")
            dialog.geometry("300x200")
            dialog.attributes("-topmost", True)
            
            ctk.CTkLabel(dialog, text="Channel Name:").pack(pady=5)
            chan_entry = ctk.CTkEntry(dialog)
            chan_entry.pack(pady=5)
            
            ctk.CTkLabel(dialog, text="OAuth Token:").pack(pady=5)
            tok_entry = ctk.CTkEntry(dialog, show="*")
            tok_entry.pack(pady=5)
            
            def do_connect():
                self.twitch_client.stop()
                self.twitch_client.channel = chan_entry.get().strip()
                self.twitch_client.token = tok_entry.get().strip()
                if self.twitch_client.start():
                    messagebox.showinfo("Twitch", "Connected successfully!", parent=dialog)
                    dialog.destroy()
            ctk.CTkButton(dialog, text="Connect", command=do_connect).pack(pady=10)
            
        self.twitch_btn = ctk.CTkButton(self.controls_frame, text="Connect to Twitch", fg_color="#6441a5", hover_color="#896bc8", command=connect_twitch)
        self.twitch_btn.pack(fill="x", pady=(0, 20))

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        def change_app_mode(val):
            ctk.set_appearance_mode(val)
            self.canvas_bg = self.main_frame._apply_appearance_mode(self.main_frame._fg_color)
            self.canvas.configure(bg=self.canvas_bg)
            self.draw_wheel()
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=change_app_mode)
        self.appearance_mode_optionemenu.grid(row=3, column=0, padx=20, pady=(10, 20))

        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.result_label = ctk.CTkLabel(self.main_frame, text="Ready to Spin!", font=ctk.CTkFont(size=28, weight="bold"), text_color="#fdcb6e")
        self.result_label.grid(row=0, column=0, pady=(20, 10))
        
        self.hamburger_btn = ctk.CTkButton(self.main_frame, text="≡", width=40, height=40, font=ctk.CTkFont(size=20), command=self.toggle_sidebar, fg_color="transparent", hover_color="#2d3436")
        self.hamburger_btn.place(x=10, y=10)

        self.canvas_bg = self.main_frame._apply_appearance_mode(self.main_frame._fg_color)
        self.canvas = tk.Canvas(self.main_frame, bg=self.canvas_bg, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

    def draw_wheel(self):
        if hasattr(self, 'renderer'):
            self.renderer.draw_all(self.app_state, self.angles, getattr(self, 'flapper_bends', None))

    def on_resize(self, event):
        if not self.spinning:
            self.draw_wheel()

    def toggle_party_mode(self):
        self.party_mode = True
        self.attributes("-fullscreen", True)
        self.sidebar_frame.grid_remove()
        self.hamburger_btn.place_forget()
        self.bind("<Escape>", self.exit_party_mode)
        self.result_label.configure(text="Party Mode! Press ESC to exit.")
        
    def exit_party_mode(self, event=None):
        self.party_mode = False
        self.attributes("-fullscreen", False)
        if self.sidebar_visible:
            self.sidebar_frame.grid()
        self.hamburger_btn.place(x=10, y=10)
        self.unbind("<Escape>")
        self.result_label.configure(text="Ready to Spin!")

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.grid_remove()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.grid()
            self.sidebar_visible = True

    def on_spin_press(self, event):
        if self.spinning: return
        wheels = self.app_state.get("wheels", [])
        if any(not w["options"] for w in wheels):
            messagebox.showwarning("Error", "All wheels must have at least one option!")
            return
            
        self.charge_start_time = time.time()
        self.charging = True
        self.spin_btn.configure(text="Charging...")
        self.audio_manager.set_bg_volume(1.0)
        self.animate_charge()

    def animate_charge(self):
        if not self.charging: return
        charge_time = time.time() - self.charge_start_time
        power = min(100, int((charge_time / 2.0) * 100))
        self.spin_btn.configure(text=f"Power: {power}%")
        if power < 100:
            self.after(50, self.animate_charge)

    def on_spin_release(self, event):
        if not self.charging: return
        self.charging = False
        charge_time = time.time() - self.charge_start_time
        power_factor = min(2.0, charge_time) / 2.0
        
        wheels = self.app_state.get("wheels", [])
        self.angular_velocities = []
        for i in range(len(wheels)):
            base_vel = 15.0 + (power_factor * 25.0)
            self.angular_velocities.append(base_vel + random.uniform(0, 5))

        self.spinning = True
        self.result_label.configure(text="Spinning...", text_color="#00cec9")
        self.spin_btn.configure(state="disabled", text="SPIN!")
        
        for i in range(len(wheels)):
            self.last_slice_indices[i] = self.get_slice_at_angle(i, self.angles[i])
            self.flapper_bends[i] = 0.0
            
        self.last_frame_time = time.time()
        self.animate_spin()

    def get_slice_at_angle(self, wheel_idx, angle):
        wheels = self.app_state.get("wheels", [])
        if wheel_idx >= len(wheels): return 0
        options = wheels[wheel_idx]["options"]
        if not options: return 0
        
        total_weight = sum(opt.get("weight", 1) for opt in options)
        pointer_angle = 90
        effective_angle = (pointer_angle - angle) % 360
        current_angle_sum = 0
        for i, opt in enumerate(options):
            angle_extent = (opt.get("weight", 1) / total_weight) * 360
            if current_angle_sum <= effective_angle < current_angle_sum + angle_extent:
                return i
            current_angle_sum += angle_extent
        return 0

    def animate_spin(self):
        if not self.spinning: return
        
        current_time = time.time()
        dt = current_time - self.last_frame_time
        if dt > 0.1: dt = 0.016
        self.last_frame_time = current_time
        
        wheels = self.app_state.get("wheels", [])
        all_stopped = True
        base_friction = 2.0
        
        for i in range(len(wheels)):
            vel = self.angular_velocities[i]
            if vel > 0:
                all_stopped = False
                
                self.angles[i] = (self.angles[i] + vel * (dt * 60.0)) % 360
                
                current_slice = self.get_slice_at_angle(i, self.angles[i])
                if current_slice != self.last_slice_indices[i]:
                    self.last_slice_indices[i] = current_slice
                    vel -= 1.0 # Peg resistance
                    if vel < 0: vel = 0
                    self.flapper_bends[i] = 1.0 # Snap flapper fully back
                    threading.Thread(target=self.audio_manager.play_spin_sound, daemon=True).start()
                
                if self.flapper_bends[i] > 0:
                    self.flapper_bends[i] -= dt * 5.0
                    if self.flapper_bends[i] < 0: self.flapper_bends[i] = 0.0
                
                vel -= base_friction * (dt * 60.0)
                if vel < 0: vel = 0
                self.angular_velocities[i] = vel
                
        self.draw_wheel()
        
        if all_stopped:
            self.spinning = False
            self.audio_manager.set_bg_volume(0.1)
            self.show_result()
        else:
            self.after(16, self.animate_spin)

    def show_result(self):
        wheels = self.app_state.get("wheels", [])
        results = []
        for i in range(len(wheels)):
            idx = self.get_slice_at_angle(i, self.angles[i])
            opt = wheels[i]["options"][idx]
            results.append((i, idx, opt["name"], opt.get("image", ""), opt.get("sound", ""), opt.get("sub_wheel", "None")))
            
        final_str = " + ".join([r[2] for r in results])
        self.last_result = final_str
        
        self.result_label.configure(text=f"🎉 Winner: {final_str} 🎉", text_color="#fdcb6e")
        self.spin_btn.configure(state="normal", text="Hold to SPIN!")
        image_path = results[0][3] if len(results) == 1 and results[0][3] else None
        self.discord_webhook.send_embed(
            title="🎉 We have a winner! 🎉",
            description=f"**{final_str}**",
            color=0xfdcb6e,
            image_path=image_path
        )
        
        self.app_state.setdefault("history", []).insert(0, {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "player": self.player_var.get(), "result": final_str})
        
        played_custom = False
        for r in results:
            snd = r[4]
            if snd and self.audio_manager.play_custom_option_sound(snd):
                played_custom = True
                
        if not played_custom:
            threading.Thread(target=self.audio_manager.play_win_sound, daemon=True).start()
            
        self.audio_manager.announce_winner(f"The winner is {final_str}!")
            
        self.renderer.spawn_particles(self.app_state.get("particle_style", "Confetti"), self.app_state.get("theme", "Default"))
        
        if self.app_state.get("elimination_mode", False):
            for r in reversed(results):
                w_idx, opt_idx, _, _, _, _ = r
                self.app_state["wheels"][w_idx]["options"].pop(opt_idx)
            self.draw_wheel()
            
        trigger_sub_wheels = []
        for r in results:
            img = r[3]
            if img:
                self.renderer.show_custom_option_image(img)
            sub_target = r[5]
            if sub_target and sub_target != "None":
                trigger_sub_wheels.append(sub_target)
                
        if trigger_sub_wheels:
            target = trigger_sub_wheels[0]
            def trigger():
                self.switch_wheel_tab(target)
                self.on_spin_press(None)
                self.after(500, self.on_spin_release, None)
            self.after(2500, trigger)
        else:
            self.after(5000, lambda: self.audio_manager.set_bg_volume(0.3))
            
        self.profile_manager.save_current_profile()

    def particle_worker(self):
        while self.particle_thread_running:
            if not self.spinning and self.last_result:
                if self.renderer.update_particles():
                    pass # it animated
            time.sleep(0.016) # ~60fps

    def on_close(self):
        self.particle_thread_running = False
        self.destroy()

if __name__ == "__main__":
    app = WheelOfLuckApp()
    app.mainloop()