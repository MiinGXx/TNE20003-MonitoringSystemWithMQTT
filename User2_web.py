from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT Settings
broker = "192.168.12.100"
port = 1883
temperature_topic = "public/server-room/temp"  # Public channel for temperature
cooling_topic = "public/server-room/cooling"  # Subscribe to cooling commands

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set("102779797", "102779797")

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(temperature_topic)

def on_message(client, userdata, msg):
    if msg.topic == temperature_topic:
        temperature = float(msg.payload.decode())
        socketio.emit('temperature', {'data': temperature})
        
        # Generate cooling command based on temperature
        if temperature > 25:
            cooling_command = "Activate cooling"
        else:
            cooling_command = "Deactivate cooling"
            
        mqtt_client.publish(cooling_topic, cooling_command)
        socketio.emit('cooling_command', {'data': cooling_command})

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(broker, port, 60)

# Start MQTT loop in a separate thread
mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
mqtt_thread.daemon = True
mqtt_thread.start()

@app.route('/')
def index():
    return render_template('user2.html')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
