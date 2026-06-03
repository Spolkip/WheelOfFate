import pygame
import pyttsx3
import threading

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
from tkinter import filedialog, messagebox

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        try:
            self.tts_engine = pyttsx3.init()
        except:
            self.tts_engine = None
        self.custom_spin_sound = None
        self.custom_win_sound = None
        self.bg_music = None
        self.enabled = True
        self.tts_enabled = True

    def toggle_sound(self):
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.music.pause()
        elif self.bg_music and pygame.mixer.music.get_pos() != -1:
            pygame.mixer.music.unpause()
        return self.enabled

    def toggle_tts(self):
        self.tts_enabled = not self.tts_enabled
        return self.tts_enabled
        
    def load_bg_music(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if path:
            self.bg_music = path
            messagebox.showinfo("Sound Loaded", "Background music loaded successfully!")
            if self.enabled:
                self.play_bg_music()
                
    def play_bg_music(self, volume=0.3):
        if not self.enabled or not self.bg_music: return
        try:
            pygame.mixer.music.load(self.bg_music)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1) # Loop indefinitely
        except:
            pass

    def set_bg_volume(self, volume):
        if self.bg_music and self.enabled:
            pygame.mixer.music.set_volume(volume)

    def announce_winner(self, text):
        if not self.tts_enabled or not self.tts_engine: return
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
        threading.Thread(target=speak, daemon=True).start()

    def load_spin_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if path:
            self.custom_spin_sound = path
            messagebox.showinfo("Sound Loaded", "Custom spin sound loaded successfully!")

    def load_win_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")])
        if path:
            self.custom_win_sound = path
            messagebox.showinfo("Sound Loaded", "Custom win sound loaded successfully!")

    def play_custom_option_sound(self, path):
        if not self.enabled or not path: return False
        try:
            pygame.mixer.Sound(path).play()
            return True
        except:
            return False

    def play_soundboard(self, key, soundboard_dict):
        if not self.enabled: return False
        path = soundboard_dict.get(str(key))
        if not path: return False
        try:
            pygame.mixer.Sound(path).play()
            return True
        except:
            return False

    def play_spin_sound(self):
        if not self.enabled: return
        if self.custom_spin_sound:
            try: pygame.mixer.Sound(self.custom_spin_sound).play()
            except: pass
        elif SOUND_AVAILABLE:
            try: winsound.Beep(800, 50)
            except: pass

    def play_win_sound(self):
        if not self.enabled: return
        if self.custom_win_sound:
            try: pygame.mixer.Sound(self.custom_win_sound).play()
            except: pass
        elif SOUND_AVAILABLE:
            try:
                winsound.Beep(1000, 200)
                winsound.Beep(1200, 200)
                winsound.Beep(1500, 400)
            except: pass
