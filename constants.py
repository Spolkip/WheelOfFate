THEMES = {
    "Default": ["#e17055", "#00b894", "#fdcb6e", "#6c5ce7", "#e84393", "#00cec9", "#fab1a0", "#a29bfe", "#fd79a8", "#55efc4", "#ffeaa7", "#74b9ff"],
    "Neon": ["#ff00ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000", "#0000ff"],
    "Pastel": ["#ffb3ba", "#ffdfba", "#ffffba", "#baffc9", "#bae1ff"],
    "Retro": ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"],
    "Monochrome": ["#333333", "#555555", "#777777", "#999999", "#bbbbbb", "#dddddd"]
}

def ease_out_quart(t):
    return 1 - pow(1 - t, 4)
