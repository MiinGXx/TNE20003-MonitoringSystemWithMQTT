from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time
import random

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT Settings
broker = "192.168.12.100"
port = 1883
motion_topic = "102779797/server-room/motion"  # Private channel for motion
temperature_topic = "public/server-room/temp"  # Public channel for temperature
cooling_topic = "public/server-room/cooling"  # Subscribe to cooling commands

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set("102779797", "102779797")

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(cooling_topic)

def on_message(client, userdata, msg):
    if msg.topic == cooling_topic:
        message = msg.payload.decode()
        socketio.emit('cooling_command', {'data': message})

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(broker, port, 60)

# Start MQTT loop in a separate thread
mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
mqtt_thread.daemon = True
mqtt_thread.start()

def generate_and_publish():
    while True:
        # Generate temperature data
        temperature = round(random.uniform(20, 30), 2)
        mqtt_client.publish(temperature_topic, f"{temperature}")
        socketio.emit('temperature', {'data': temperature})

        # Generate motion detection
        motion = random.choice([True, False])
        if motion:
            mqtt_client.publish(motion_topic, "Motion detected!")
            socketio.emit('motion', {'data': "Motion detected!"})
        
        time.sleep(10)

# Start publishing in a separate thread
publish_thread = threading.Thread(target=generate_and_publish)
publish_thread.daemon = True
publish_thread.start()

@app.route('/')
def index():
    return render_template('user1.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
