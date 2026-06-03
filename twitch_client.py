import socket
import threading

class TwitchClient:
    def __init__(self, channel, token, on_spin_command):
        self.channel = channel.lower().strip()
        self.token = token.strip() if token.strip().startswith('oauth:') else f'oauth:{token.strip()}'
        self.on_spin_command = on_spin_command
        self.sock = None
        self.running = False
        self.thread = None

    def start(self):
        if not self.channel or not self.token: return False
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        if self.sock:
            try: self.sock.close()
            except: pass

    def _listen(self):
        self.sock = socket.socket()
        try:
            self.sock.connect(('irc.chat.twitch.tv', 6667))
            self.sock.send(f"PASS {self.token}\n".encode('utf-8'))
            self.sock.send(f"NICK justinfan12345\n".encode('utf-8')) # Anonymous read-only nick
            self.sock.send(f"JOIN #{self.channel}\n".encode('utf-8'))
            
            while self.running:
                resp = self.sock.recv(2048).decode('utf-8')
                if resp.startswith('PING'):
                    self.sock.send("PONG\n".encode('utf-8'))
                elif len(resp) > 0:
                    lines = resp.split('\n')
                    for line in lines:
                        if "PRIVMSG" in line and "!spin" in line.lower():
                            self.on_spin_command()
        except Exception as e:
            print("Twitch Client Error:", e)
