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

# Simulated sensor data
def generate_temperature():
    return round(random.uniform(22, 42), 1)

def detect_motion():
    return random.choice(["Motion Detected", "No Motion"])

def handle_temperature(temp):
    return "ON" if temp > 30 else "OFF"

class MonitoringApp:
    def __init__(self, root):
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

        ttk.Label(root, text="SKIBIDI MONITORING SERVICE", style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(10, 15))

        ttk.Label(root, text="TEMPERATURE:").grid(row=1, column=0, padx=10, sticky="w")
        self.temp_label = ttk.Label(root, text="-- °C", style="Status.TLabel")
        self.temp_label.grid(row=1, column=1, sticky="w")

        ttk.Label(root, text="MOTION:").grid(row=2, column=0, padx=10, sticky="w")
        self.motion_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.motion_label.grid(row=2, column=1, sticky="w")

        ttk.Label(root, text="COOLING:").grid(row=3, column=0, padx=10, sticky="w")
        self.cooling_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.cooling_label.grid(row=3, column=1, sticky="w")

        ttk.Label(root, text="ALARM:").grid(row=4, column=0, padx=10, sticky="w")
        self.alarm_label = ttk.Label(root, text="--", style="Status.TLabel")
        self.alarm_label.grid(row=4, column=1, sticky="w")

        ttk.Label(root, text="RECENT EVENTS:").grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w")
        self.event_log = scrolledtext.ScrolledText(root, width=50, height=10, bg="#2e2e2e", fg="white", font=("Consolas", 10))
        self.event_log.grid(row=6, column=0, columnspan=3, padx=10, pady=(0, 10))

        self.cooling_button = ttk.Button(root, text="ACTIVATE COOLING", command=self.activate_cooling)
        self.cooling_button.grid(row=7, column=0, padx=10, pady=10)

        self.alarm_button = ttk.Button(root, text="CONFIGURE ALARM", command=self.configure_alarm)
        self.alarm_button.grid(row=7, column=1, padx=10, pady=10)

        self.mode_button = ttk.Button(root, text="Switch to Light Mode", command=self.toggle_mode)
        self.mode_button.grid(row=7, column=2, padx=10, pady=10)

        self.alarm_toggle_button = ttk.Button(root, text="TOGGLE ALARM", command=self.toggle_alarm)
        self.alarm_toggle_button.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        # MQTT Callback Setup
        client.on_message = self.on_mqtt_message
        client.connect(MQTT_BROKER)
        client.subscribe(COOLING_CONTROL_TOPIC)
        client.subscribe(ALARM_CONTROL_TOPIC)
        client.loop_start()

        self.running = True
        threading.Thread(target=self.monitor_loop, daemon=True).start()

    def toggle_mode(self):
        self.root.configure(bg="white" if self.is_dark_mode else "#1e1e1e")
        self.mode_button.configure(text="Switch to Dark Mode" if self.is_dark_mode else "Switch to Light Mode")
        self.is_dark_mode = not self.is_dark_mode

    def activate_cooling(self):
        self.cooling_label.config(text="Manual ON", foreground="cyan")
        self.log_event("Manual cooling command issued.")
        client.publish(COOLING_CONTROL_TOPIC, "ON")

    def toggle_alarm(self):
        self.alarm_enabled = not self.alarm_enabled
        status = "ENABLED" if self.alarm_enabled else "DISABLED"
        self.alarm_label.config(text=status, foreground="green" if self.alarm_enabled else "gray")
        self.log_event(f"Alarm {status.lower()} by user.")

    def configure_alarm(self):
        def save_config():
            try:
                start = int(start_time_entry.get())
                end = int(end_time_entry.get())
                if 0 <= start < 24 and 0 <= end < 24:
                    self.alarm_start_time = start
                    self.alarm_end_time = end
                    self.log_event(f"Alarm time range set to {start}:00 - {end}:00.")
                    config_window.destroy()
                else:
                    error_label.config(text="Invalid range! Use 0–23.")
            except ValueError:
                error_label.config(text="Invalid input! Integers only.")

        config_window = tk.Toplevel(self.root)
        config_window.title("Configure Alarm Time")
        config_window.geometry("300x200")
        config_window.resizable(False, False)

        ttk.Label(config_window, text="Start Time (0–23):").pack(pady=5)
        start_time_entry = ttk.Entry(config_window)
        start_time_entry.insert(0, str(self.alarm_start_time))
        start_time_entry.pack(pady=5)

        ttk.Label(config_window, text="End Time (0–23):").pack(pady=5)
        end_time_entry = ttk.Entry(config_window)
        end_time_entry.insert(0, str(self.alarm_end_time))
        end_time_entry.pack(pady=5)

        error_label = ttk.Label(config_window, text="", foreground="red")
        error_label.pack(pady=5)
        ttk.Button(config_window, text="Save", command=save_config).pack(pady=10)

    def log_event(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.event_log.insert(tk.END, f"{timestamp} {msg}\n")
        self.event_log.see(tk.END)

    def handle_motion(self, motion):
        now = datetime.now()
        hour = now.hour
        if self.alarm_enabled and motion == "Motion Detected" and (
            (self.alarm_start_time <= hour < 24) or (0 <= hour < self.alarm_end_time)
        ):
            return "ALERT"
        return "IGNORE"

    def on_mqtt_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        if topic == COOLING_CONTROL_TOPIC:
            self.cooling_label.config(text=f"Remote {payload}", foreground="cyan")
            self.log_event(f"Received cooling command: {payload}")
        elif topic == ALARM_CONTROL_TOPIC:
            self.alarm_label.config(text=f"Remote {payload}", foreground="red" if payload == "ALERT" else "white")
            self.log_event(f"Received alarm command: {payload}")

    def monitor_loop(self):
        while self.running:
            temp = generate_temperature()
            motion = detect_motion()

            cooling = handle_temperature(temp)
            alarm = self.handle_motion(motion)

            self.temp_label.config(text=f"{temp} °C")
            self.motion_label.config(text=motion)

            client.publish(TEMP_TOPIC, str(temp))
            client.publish(MOTION_TOPIC, motion)

            if cooling == "ON":
                self.cooling_label.config(text="AUTO ON", foreground="dodgerblue")
                self.log_event(f"Cooling activated (Temp: {temp}°C)")

            if alarm == "ALERT":
                self.alarm_label.config(text="ACTIVE", foreground="red")
                self.log_event("Unauthorized motion detected after hours!")
                client.publish(ALARM_CONTROL_TOPIC, "ALERT")
            else:
                self.alarm_label.config(text="IDLE", foreground="white")

            time.sleep(10)

    def stop(self):
        self.running = False
        client.loop_stop()
        client.disconnect()

# Entry point
def run_gui():
    root = tk.Tk()
    app = MonitoringApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    run_gui()
