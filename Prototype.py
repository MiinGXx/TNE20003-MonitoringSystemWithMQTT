import random
import time
import threading
from datetime import datetime
import tkinter as tk    
from tkinter import ttk, scrolledtext
import paho.mqtt.client as mqtt

# MQTT Setup
MQTT_BROKER = "192.168.12.100"
TEMP_TOPIC = "public/server-room/temp"
MOTION_TOPIC = "public/server-room/motion"
COOLING_CONTROL_TOPIC = "public/server-room/cooling"
ALARM_CONTROL_TOPIC = "public/server-room/alarm"

# MQTT Client Setup
# Replace 'yourStudentID' with your actual student ID
client = mqtt.Client()
client.username_pw_set("102779797", "102779797")
import customtkinter as ctk
import threading

def generate_temperature():
    return round(random.uniform(22, 42), 1)

def detect_motion():
    return random.choice(["Motion Detected", "No Motion"])

def handle_temperature(temp):
    return "ON" if temp > 30 else "OFF"

class MonitoringApp:
    def __init__(self, root):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = root
        self.root.title("Skibidi Monitoring Service")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)

        self.is_dark_mode = True
        self.alarm_enabled = True
        self.alarm_start_time = 18
        self.alarm_end_time = 9

        # GUI Setup
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), foreground="white", background="#1e1e1e")
        style.configure("Status.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10))
        self.root.resizable(True, True)  # Enable window resizing
        self.root.geometry("750x400")  # Adjusted window size to better fit content

        ttk.Label(root, text="SKIBIDI MONITORING SERVICE", style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(10, 15))
        # Title
        self.title_label = ctk.CTkLabel(root, text="SKIBIDI MONITORING SERVICE", font=("Segoe UI", 20, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), padx=10, sticky="w")

        ttk.Label(root, text="TEMPERATURE:").grid(row=1, column=0, padx=10, sticky="w")
        self.temp_label = ttk.Label(root, text="-- °C", style="Status.TLabel")
        self.temp_label.grid(row=1, column=1, sticky="w")
        # Temperature display
        self.temp_label = ctk.CTkLabel(root, text="TEMPERATURE: -- °C", font=("Segoe UI", 14))
        self.temp_label.grid(row=1, column=0, padx=10, sticky="w")

        ttk.Label(root, text="MOTION:").grid(row=2, column=0, padx=10, sticky="w")
        self.motion_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.motion_label.grid(row=2, column=1, sticky="w")
        # Motion status
        self.motion_label = ctk.CTkLabel(root, text="MOTION: --", font=("Segoe UI", 14))
        self.motion_label.grid(row=2, column=0, padx=10, sticky="w")

        ttk.Label(root, text="COOLING:").grid(row=3, column=0, padx=10, sticky="w")
        self.cooling_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.cooling_label.grid(row=3, column=1, sticky="w")
        # Cooling system status
        self.cooling_label = ctk.CTkLabel(root, text="COOLING: --", font=("Segoe UI", 14))
        self.cooling_label.grid(row=3, column=0, padx=10, sticky="w")

        ttk.Label(root, text="ALARM:").grid(row=4, column=0, padx=10, sticky="w")
        self.alarm_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.alarm_label.grid(row=4, column=1, sticky="w")
        # Alarm status
        self.alarm_label = ctk.CTkLabel(root, text="ALARM: --", font=("Segoe UI", 14))
        self.alarm_label.grid(row=4, column=0, padx=10, sticky="w")

        ttk.Label(root, text="RECENT EVENTS:").grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
        self.event_log = scrolledtext.ScrolledText(root, width=50, height=10, bg="#2e2e2e", fg="white", font=("Consolas", 10))
        self.event_log.grid(row=6, column=0, columnspan=3, padx=10, pady=(0, 10))
        # Event log display aligned to the right
        self.event_log = ctk.CTkTextbox(root, width=400, height=300) 
        self.event_log.grid(row=0, column=2, rowspan=6, padx=10, pady=10, sticky="n")

        self.cooling_button = ttk.Button(root, text="ACTIVATE COOLING", command=self.activate_cooling)
        self.cooling_button.grid(row=7, column=0, padx=10, pady=10)
        # Buttons
        self.cooling_button = ctk.CTkButton(root, text="ACTIVATE COOLING", command=self.activate_cooling)
        self.cooling_button.grid(row=5, column=0, padx=10, pady=10)

        self.alarm_button = ttk.Button(root, text="CONFIGURE ALARM", command=self.configure_alarm)
        self.alarm_button.grid(row=7, column=1, padx=10, pady=10)
        self.alarm_button = ctk.CTkButton(root, text="CONFIGURE ALARM", command=self.reset_alarm)
        self.alarm_button.grid(row=5, column=1, padx=10, pady=10)

        # Light/Dark mode toggle
        self.mode_toggle = ctk.CTkSwitch(root, text="Light/Dark Mode", command=self.toggle_mode)
        self.mode_toggle.grid(row=6, column=0, columnspan=2, pady=10, padx=10, sticky="w")
        self.mode_toggle.select()

        # System monitoring loop
        self.running = True
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def toggle_mode(self):
        self.root.configure(bg="white" if self.is_dark_mode else "#1e1e1e")
        self.mode_button.configure(text="Switch to Dark Mode" if self.is_dark_mode else "Switch to Light Mode")
        self.is_dark_mode = not self.is_dark_mode

    def activate_cooling(self):
        self.cooling_label.configure(text="COOLING: Manual ON")
        self.log_event("Manual cooling command issued.")

    def reset_alarm(self):
        self.alarm_label.configure(text="ALARM: IDLE")
        self.log_event("Alarm manually reset.")

    def toggle_mode(self):
        if self.mode_toggle.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def log_event(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.event_log.insert("end", f"{timestamp} {msg}\n")
        self.event_log.see("end")

    def monitor_loop(self):
        while self.running:
            temp = generate_temperature()
            motion = detect_motion()

            cooling = handle_temperature(temp)
            alarm = self.handle_motion(motion)

            self.temp_label.config(text=f"{temp} °C")
            self.motion_label.config(text=motion)
            # Update UI
            self.temp_label.configure(text=f"TEMPERATURE: {temp} °C")
            self.motion_label.configure(text=f"MOTION: {motion}")

            client.publish(TEMP_TOPIC, str(temp))
            client.publish(MOTION_TOPIC, motion)

            if cooling == "ON":
                self.cooling_label.config(text="AUTO ON", foreground="dodgerblue")
                self.cooling_label.configure(text="COOLING: ON")
                self.log_event(f"Cooling activated (Temp: {temp}°C)")
            else:
                self.cooling_label.configure(text="COOLING: OFF")

            if alarm == "ALERT":
                self.alarm_label.configure(text="ALARM: ACTIVE")
                self.log_event("Unauthorized motion detected after hours!")
                client.publish(ALARM_CONTROL_TOPIC, "ALERT")
            else:
                self.alarm_label.configure(text="ALARM: IDLE")

            time.sleep(10)

    def stop(self):
        self.running = False
        client.loop_stop()
        client.disconnect()

# Entry point
def run_gui():
    root = ctk.CTk()
    app = MonitoringApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    run_gui()
