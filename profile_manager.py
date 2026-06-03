import os
import json
import shutil
import csv
from tkinter import filedialog, messagebox

class ProfileManager:
    def __init__(self, app_state, on_profile_changed):
        self.app_state = app_state
        self.on_profile_changed = on_profile_changed
        self.profiles_dir = "profiles"
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.current_profile = "default.json"

    def initialize(self):
        if not os.path.exists(os.path.join(self.profiles_dir, "default.json")):
            self._reset_state()
            self.save_current_profile()
            self.on_profile_changed()
        else:
            self.load_profile("default.json")

    def get_profiles_list(self):
        profiles = [f[:-5] for f in os.listdir(self.profiles_dir) if f.endswith(".json")]
        return profiles if profiles else ["default"]

    def switch_profile(self, profile_name):
        self.current_profile = profile_name + ".json"
        self.load_profile(self.current_profile)

    def load_profile(self, filename):
        path = os.path.join(self.profiles_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    if "wheels" in data:
                        self.app_state["wheels"] = data["wheels"]
                    else:
                        opts = data.get("options", [])
                        migrated_opts = []
                        for opt in opts:
                            if isinstance(opt, str):
                                migrated_opts.append({"name": opt, "weight": 1})
                            else:
                                migrated_opts.append(opt)
                        self.app_state["wheels"] = [{"name": "Wheel 1", "options": migrated_opts}]
                            
                    self.app_state["history"] = data.get("history", [])
                    self.app_state["theme"] = data.get("theme", "Default")
                    self.app_state["elimination_mode"] = data.get("elimination_mode", False)
                    self.app_state["background_image"] = data.get("background_image", None)
                    self.app_state["centerpiece_image"] = data.get("centerpiece_image", None)
                    self.app_state["particle_style"] = data.get("particle_style", "Confetti")
            except:
                self._reset_state()
        else:
            self._reset_state()
            
        self.current_profile = filename
        self.on_profile_changed()

    def _reset_state(self):
        self.app_state["wheels"] = [
            {"name": "Wheel 1", "options": [
                {"name": "Free Coffee", "weight": 1},
                {"name": "50% Off", "weight": 1},
                {"name": "$100 Gift Card", "weight": 0.5},
                {"name": "Try Again", "weight": 2}
            ]}
        ]
        self.app_state["history"] = []
        self.app_state["theme"] = "Default"
        self.app_state["elimination_mode"] = False
        self.app_state["background_image"] = None
        self.app_state["centerpiece_image"] = None
        self.app_state["particle_style"] = "Confetti"

    def save_current_profile(self):
        if not self.current_profile: return
        path = os.path.join(self.profiles_dir, self.current_profile)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.app_state, f, indent=2)

    def new_profile(self, name):
        filename = name.strip() + ".json"
        if not os.path.exists(os.path.join(self.profiles_dir, filename)):
            self._reset_state()
            self.current_profile = filename
            self.save_current_profile()
            self.on_profile_changed()
        else:
            messagebox.showwarning("Error", "Profile already exists!")

    def delete_profile(self):
        if self.current_profile == "default.json":
            messagebox.showwarning("Error", "Cannot delete the default profile!")
            return False
        if messagebox.askyesno("Delete", f"Delete profile '{self.current_profile[:-5]}'?"):
            path = os.path.join(self.profiles_dir, self.current_profile)
            if os.path.exists(path):
                os.remove(path)
            self.current_profile = "default.json"
            self.load_profile(self.current_profile)
            return True
        return False

    def import_profile(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            filename = os.path.basename(path)
            dest = os.path.join(self.profiles_dir, filename)
            shutil.copy2(path, dest)
            self.current_profile = filename
            self.load_profile(filename)

    def export_profile(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialfile=self.current_profile)
        if path:
            src = os.path.join(self.profiles_dir, self.current_profile)
            if os.path.exists(src):
                shutil.copy2(src, path)
                messagebox.showinfo("Export", "Profile exported successfully!")
                
    def export_history_csv(self):
        if not self.app_state.get("history"):
            messagebox.showinfo("History", "No history to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="spin_history.csv")
        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time", "Result"])
                    for item in self.app_state["history"]:
                        writer.writerow([item["time"], item["result"]])
                messagebox.showinfo("Export", "History exported to CSV successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {e}")
