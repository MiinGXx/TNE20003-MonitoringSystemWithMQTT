from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time
import random

app = Flask(__name__)
socketio = SocketIO(app)

# Global configuration
config = {
    'temp_threshold': 28.0,  # Default temperature threshold
    'alert_enabled': True
}


# MQTT Settings
broker = "192.168.12.100"
port = 1883
motion_topic = "102779797/server-room/motion"  # Private channel for motion
temperature_topic = "public/server-room/temp"  # Public channel for temperature
cooling_topic = "public/server-room/cooling"  # Subscribe to cooling commands

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe(cooling_topic)
        socketio.emit('mqtt_status', {'status': 'connected'})
    else:
        print(f"Failed to connect to MQTT broker with code {rc}")
        socketio.emit('mqtt_status', {'status': 'disconnected'})

def on_disconnect(client, userdata, rc):
    print(f"Disconnected from MQTT broker with code {rc}")
    socketio.emit('mqtt_status', {'status': 'disconnected'})

def on_message(client, userdata, msg):
    try:
        if msg.topic == cooling_topic:
            message = msg.payload.decode()
            socketio.emit('cooling_command', {'data': message})
            # Log cooling command
            logger.log_data(None, None, message)
    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
try:
    print("Setting up MQTT client...")
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set("102779797", "102779797")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    
    print(f"Attempting to connect to broker at {broker}:{port}")
    mqtt_client.connect(broker, port, 60)
except Exception as e:
    print(f"Error setting up MQTT client: {e}")

# Start MQTT loop in a separate thread
mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
mqtt_thread.daemon = True
mqtt_thread.start()

def generate_and_publish():
    while True:
        try:
            # Generate temperature data
            temperature = round(random.uniform(20, 30), 2)
            mqtt_client.publish(temperature_topic, f"{temperature}")
            socketio.emit('temperature', {'data': temperature})
            
            # Check temperature threshold
            if temperature > config['temp_threshold'] and config['alert_enabled']:
                alert_message = f"High temperature alert: {temperature}°C"
                socketio.emit('alert', {'data': alert_message})

            # Generate motion detection
            motion = random.choice([True, False])
            if motion:
                mqtt_client.publish(motion_topic, "Motion detected!")
                socketio.emit('motion', {'data': "Motion detected!"})
            
            # Log data
            logger.log_data(temperature, motion, None)
            
        except Exception as e:
            print(f"Error in generate_and_publish: {e}")
            socketio.emit('mqtt_status', {'status': 'error'})
        
        time.sleep(10)

# Start publishing in a separate thread
publish_thread = threading.Thread(target=generate_and_publish)
publish_thread.daemon = True
publish_thread.start()

@app.route('/')
def index():
    return render_template('user1.html')

@app.route('/config', methods=['GET', 'POST'])
def update_config():
    if request.method == 'POST':
        data = request.get_json()
        if 'temp_threshold' in data:
            config['temp_threshold'] = float(data['temp_threshold'])
        if 'alert_enabled' in data:
            config['alert_enabled'] = bool(data['alert_enabled'])
        return jsonify({'status': 'success'})
    return jsonify(config)

@app.route('/historical-data')
def get_historical_data():
    data = logger.get_recent_data(50)  # Get last 50 records
    return jsonify(data)

if __name__ == '__main__':
    try:
        print("Starting Flask-SocketIO server...")
        socketio.run(app, debug=True, port=5000, host='0.0.0.0')
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        print("Cleaning up...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
