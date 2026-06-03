import customtkinter as ctk
import tkinter as tk

class StatsDashboard:
    @staticmethod
    def show(parent, history, theme_colors):
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Detailed Statistics")
        dialog.geometry("600x450")
        dialog.attributes("-topmost", True)
        
        if not history:
            ctk.CTkLabel(dialog, text="No spin history available! Spin the wheel first.", font=("Arial", 16)).pack(pady=50)
            return
            
        tabview = ctk.CTkTabview(dialog)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_overall = tabview.add("Overall Stats")
        tab_leaderboard = tabview.add("Leaderboards")
        
        counts = {}
        player_counts = {}
        for h in history:
            res = h["result"]
            player = h.get("player", "Guest")
            
            counts[res] = counts.get(res, 0) + 1
            if player not in player_counts:
                player_counts[player] = {"spins": 0, "results": {}}
            player_counts[player]["spins"] += 1
            player_counts[player]["results"][res] = player_counts[player]["results"].get(res, 0) + 1
            
        total_spins = len(history)
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Overall Stats
        header = ctk.CTkFrame(tab_overall)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header, text=f"Total Spins: {total_spins}", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(header, text=f"Luckiest: {sorted_counts[0][0]}", font=("Arial", 14, "bold"), text_color="#55efc4").pack(side="left", padx=20)
        ctk.CTkLabel(header, text=f"Unluckiest: {sorted_counts[-1][0]}", font=("Arial", 14, "bold"), text_color="#ff7675").pack(side="left", padx=20)
        
        frame = ctk.CTkFrame(tab_overall)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        canvas_bg = frame._apply_appearance_mode(frame._fg_color)
        canvas = tk.Canvas(frame, bg=canvas_bg, highlightthickness=0, width=300, height=300)
        canvas.pack(side="left", padx=20, pady=20)
        
        center_x, center_y, radius = 150, 150, 130
        current_angle = 0
        
        legend_frame = ctk.CTkScrollableFrame(frame, width=200)
        legend_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        for i, (result, count) in enumerate(sorted_counts):
            extent = (count / total_spins) * 360
            color = theme_colors[i % len(theme_colors)]
            canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=current_angle, extent=extent, fill=color, outline=canvas_bg, width=2
            )
            current_angle += extent
            pct = int(count/total_spins * 100)
            ctk.CTkLabel(legend_frame, text=f"■ {result}: {count} ({pct}%)", text_color=color, font=("Arial", 13, "bold"), anchor="w").pack(fill="x", pady=2)
            
        # Leaderboards
        lb_scroll = ctk.CTkScrollableFrame(tab_leaderboard)
        lb_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        sorted_players = sorted(player_counts.items(), key=lambda x: x[1]["spins"], reverse=True)
        for i, (player, stats) in enumerate(sorted_players):
            p_frame = ctk.CTkFrame(lb_scroll)
            p_frame.pack(fill="x", pady=5)
            
            top_res = sorted(stats["results"].items(), key=lambda x: x[1], reverse=True)[0]
            
            ctk.CTkLabel(p_frame, text=f"#{i+1} {player}", font=("Arial", 16, "bold"), text_color="#fdcb6e").pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(p_frame, text=f"Wins/Spins: {stats['spins']}").pack(side="left", padx=20)
            ctk.CTkLabel(p_frame, text=f"Luckiest Item: {top_res[0]} ({top_res[1]} times)").pack(side="left", padx=20)
