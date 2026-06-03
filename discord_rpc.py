import threading
import json
import time
import os

try:
    import requests
except ImportError:
    requests = None

class DiscordWebhook:
    def __init__(self):
        self.webhook_url = ""
        self.connected = False

    def connect(self, webhook_url, on_status_change=None):
        self.webhook_url = webhook_url
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            print("Invalid Discord Webhook URL.")
            self.connected = False
            if on_status_change:
                on_status_change(False)
            return

        self.connected = True
        print("Discord Webhook Connected!")
        self.send_embed(
            title="Wheel of Luck",
            description="✨ The Wheel of Luck is ready to spin! ✨",
            color=0x3498db
        )
        if on_status_change:
            on_status_change(True)

    def disconnect(self):
        self.connected = False

    def send_embed(self, title, description, color=0x3498db, image_path=None):
        if not self.connected or not self.webhook_url:
            return
        if not requests:
            print("Cannot send webhook: 'requests' module not installed.")
            return
            
        def _send():
            try:
                embed = {
                    "title": title,
                    "description": description,
                    "color": color,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                
                payload = {
                    "username": "Wheel of Luck",
                    "embeds": [embed]
                }
                
                files = {}
                if image_path and os.path.exists(image_path):
                    filename = os.path.basename(image_path)
                    embed["thumbnail"] = {"url": f"attachment://{filename}"}
                    
                    with open(image_path, "rb") as f:
                        file_data = f.read()
                        
                    files = {
                        "file": (filename, file_data)
                    }
                    data = {"payload_json": json.dumps(payload)}
                    res = requests.post(self.webhook_url, data=data, files=files, timeout=5)
                else:
                    res = requests.post(self.webhook_url, json=payload, timeout=5)
                    
                if res.status_code >= 400:
                    print(f"Webhook failed with status {res.status_code}: {res.text}")
                    
            except Exception as e:
                print("Failed to send webhook message:", e)
                
        threading.Thread(target=_send, daemon=True).start()
