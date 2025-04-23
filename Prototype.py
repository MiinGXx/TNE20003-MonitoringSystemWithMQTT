import random
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

# Simulate temperature and motion
def generate_temperature():
    return round(random.uniform(22, 42), 1)

def detect_motion():
    return random.choice(["Motion Detected", "No Motion"])

def handle_temperature(temp):
    return "ON" if temp > 30 else "OFF"

def handle_motion(motion):
    now = datetime.now()
    hour = now.hour
    if motion == "Motion Detected" and (hour < 9 or hour >= 18):
        return "ALERT"
    return "IGNORE"

class MonitoringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skibidi Monitoring Service")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        self.is_dark_mode = True

        # Style setup
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="white", background="#1e1e1e")
        style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10))

        # Title
        ttk.Label(root, text="SKIBIDI MONITORING SERVICE", style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(10, 15))

        # Temperature display
        ttk.Label(root, text="TEMPERATURE:").grid(row=1, column=0, padx=10, sticky="w")
        self.temp_label = ttk.Label(root, text="-- °C", style="Status.TLabel")
        self.temp_label.grid(row=1, column=1, sticky="w")

        # Motion status
        ttk.Label(root, text="MOTION:").grid(row=2, column=0, padx=10, sticky="w")
        self.motion_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.motion_label.grid(row=2, column=1, sticky="w")

        # Cooling system status
        ttk.Label(root, text="COOLING:").grid(row=3, column=0, padx=10, sticky="w")
        self.cooling_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.cooling_label.grid(row=3, column=1, sticky="w")

        # Alarm status
        ttk.Label(root, text="ALARM:").grid(row=4, column=0, padx=10, sticky="w")
        self.alarm_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.alarm_label.grid(row=4, column=1, sticky="w")

        # Event log display
        ttk.Label(root, text="RECENT EVENTS:").grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
        self.event_log = scrolledtext.ScrolledText(root, width=50, height=10, bg="#2e2e2e", fg="white", font=("Consolas", 10))
        self.event_log.grid(row=6, column=0, columnspan=3, padx=10, pady=(0, 10))

        # Buttons
        self.cooling_button = ttk.Button(root, text="ACTIVATE COOLING", command=self.activate_cooling)
        self.cooling_button.grid(row=7, column=0, padx=10, pady=10)

        self.alarm_button = ttk.Button(root, text="CONFIGURE ALARM", command=self.reset_alarm)
        self.alarm_button.grid(row=7, column=1, padx=10, pady=10)

        self.mode_button = ttk.Button(root, text="Switch to Light Mode", command=self.toggle_mode)
        self.mode_button.grid(row=7, column=2, padx=10, pady=10)

        # System monitoring loop
        self.running = True
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def toggle_mode(self):
        if self.is_dark_mode:
            self.root.configure(bg="white")
            self.mode_button.configure(text="Switch to Dark Mode")
        else:
            self.root.configure(bg="#1e1e1e")
            self.mode_button.configure(text="Switch to Light Mode")
        self.is_dark_mode = not self.is_dark_mode

    def activate_cooling(self):
        self.cooling_label.config(text="Manual ON", foreground="cyan")
        self.log_event("Manual cooling command issued.")

    def reset_alarm(self):
        self.alarm_label.config(text="IDLE", foreground="green")
        self.log_event("Alarm manually reset.")

    def log_event(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.event_log.insert(tk.END, f"{timestamp} {msg}\n")
        self.event_log.see(tk.END)

    def monitor_loop(self):
        while self.running:
            temp = generate_temperature()
            motion = detect_motion()

            cooling = handle_temperature(temp)
            alarm = handle_motion(motion)

            # Update UI
            self.temp_label.config(text=f"{temp} °C")
            self.motion_label.config(text=motion)

            # Cooling label color
            if cooling == "ON":
                self.cooling_label.config(text="ON", foreground="dodgerblue")
                self.log_event(f"Cooling activated (Temp: {temp}°C)")
            else:
                self.cooling_label.config(text="OFF", foreground="white")

            # Alarm label color
            if alarm == "ALERT":
                self.alarm_label.config(text="ACTIVE", foreground="red")
                self.log_event("Unauthorized motion detected after hours!")
            else:
                self.alarm_label.config(text="IDLE", foreground="white")

            time.sleep(10)

    def stop(self):
        self.running = False

# Entry point
def run_gui():
    root = tk.Tk()
    app = MonitoringApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    run_gui()
