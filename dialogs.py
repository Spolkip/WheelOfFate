import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

class OptionDialog:
    @staticmethod
    def show(parent, title, options, all_wheels, draw_callback, save_callback, edit_index=None):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("380x550")
        dialog.attributes("-topmost", True)
        
        frame = ctk.CTkScrollableFrame(dialog)
        frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Option Name:").pack(pady=(10, 0))
        name_entry = ctk.CTkEntry(frame)
        name_entry.pack(pady=5, fill="x", padx=20)
        
        ctk.CTkLabel(frame, text="Weight (1-100):").pack(pady=(10, 0))
        weight_entry = ctk.CTkEntry(frame)
        weight_entry.pack(pady=5, fill="x", padx=20)
        
        img_path_var = tk.StringVar()
        snd_path_var = tk.StringVar()
        sub_wheel_var = ctk.StringVar(value="None")
        
        wheel_opts = ["None"] + [w["name"] for w in all_wheels]
        
        if edit_index is not None:
            opt = options[edit_index]
            name_entry.insert(0, opt.get("name", ""))
            weight_entry.insert(0, str(opt.get("weight", 1)))
            img_path_var.set(opt.get("image", ""))
            snd_path_var.set(opt.get("sound", ""))
            sub_wheel_var.set(opt.get("sub_wheel", "None"))
        else:
            weight_entry.insert(0, "1")
            
        ctk.CTkLabel(frame, text="Trigger Sub-Wheel on Win:").pack(pady=(10, 0))
        ctk.CTkOptionMenu(frame, variable=sub_wheel_var, values=wheel_opts).pack(pady=5, padx=20, fill="x")
            
        def select_img():
            p = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")], parent=dialog)
            if p: img_path_var.set(p)
            
        def select_snd():
            p = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3 *.ogg")], parent=dialog)
            if p: snd_path_var.set(p)
            
        ctk.CTkButton(frame, text="Select Custom Image", command=select_img, fg_color="#0984e3").pack(pady=10)
        ctk.CTkLabel(frame, textvariable=img_path_var, font=("Arial", 10), text_color="#aaa").pack(pady=0)
        
        ctk.CTkButton(frame, text="Select Custom Sound", command=select_snd, fg_color="#0984e3").pack(pady=10)
        ctk.CTkLabel(frame, textvariable=snd_path_var, font=("Arial", 10), text_color="#aaa").pack(pady=0)
            
        def save():
            name = name_entry.get().strip()
            weight_str = weight_entry.get().strip()
            if name:
                try:
                    weight = float(weight_str) if weight_str else 1.0
                    if weight <= 0: weight = 1.0
                except:
                    weight = 1.0
                    
                new_opt = {"name": name, "weight": weight, "image": img_path_var.get(), "sound": snd_path_var.get(), "sub_wheel": sub_wheel_var.get()}
                if edit_index is not None:
                    options[edit_index] = new_opt
                else:
                    options.append(new_opt)
                draw_callback()
                save_callback()
                dialog.destroy()
            else:
                messagebox.showwarning("Error", "Name cannot be empty!", parent=dialog)
                
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

class ListboxDialog:
    @staticmethod
    def show(parent, title, options, on_action_callback, action_name, is_edit=False):
        if not options: return
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("300x400")
        dialog.attributes("-topmost", True)
        
        listbox = tk.Listbox(dialog, font=("Arial", 12), bg="#2d3436", fg="#ffffff", selectbackground="#0984e3")
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for opt in options: 
            listbox.insert("end", f"{opt.get('name', '')} (W: {opt.get('weight', 1)})")
            
        def handle_action():
            sel = listbox.curselection()
            if sel:
                idx = sel[0]
                if is_edit:
                    dialog.attributes("-topmost", False)
                on_action_callback(idx, dialog)
                if not is_edit:
                    dialog.destroy()
                
        color = "#0984e3" if is_edit else "#d63031"
        hover = "#74b9ff" if is_edit else "#ff7675"
        ctk.CTkButton(dialog, text=action_name, command=handle_action, fg_color=color, hover_color=hover).pack(pady=10)

class HistoryDialog:
    @staticmethod
    def show(parent, history, save_callback, export_callback):
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Spin History")
        dialog.geometry("400x500")
        dialog.attributes("-topmost", True)
        
        frame = ctk.CTkScrollableFrame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def refresh_history():
            for widget in frame.winfo_children():
                widget.destroy()
            if not history:
                ctk.CTkLabel(frame, text="No history available.").pack(pady=20)
            else:
                for item in history:
                    ctk.CTkLabel(frame, text=f"{item['time']}\n{item['result']}", font=ctk.CTkFont(weight="bold"), anchor="w", justify="left").pack(fill="x", pady=5)
        
        refresh_history()
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        def clear_history():
            if messagebox.askyesno("Clear", "Clear spin history?", parent=dialog):
                history.clear()
                save_callback()
                refresh_history()
                
        ctk.CTkButton(btn_frame, text="Export CSV", command=export_callback).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Clear History", fg_color="#d63031", hover_color="#ff7675", command=clear_history).pack(side="right", expand=True, padx=5)
