from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time
import random
from datetime import datetime, time as dt_time

app = Flask(__name__)
socketio = SocketIO(app)

# Global configuration
config = {
    'temp_threshold': 28.0,  # Default temperature threshold
    'alert_enabled': True,
    'alarm_start': '18:00',
    'alarm_end': '09:00',
    'alarm_enabled': True
}

# MQTT Settings
broker = "192.168.12.100"
port = 1883
motion_topic = "102779797/server-room/motion"  # Private channel for motion
temperature_topic = "public/server-room/temp"  # Public channel for temperature
cooling_topic = "public/server-room/cooling"  # Subscribe to cooling commands

# Time configuration
def is_time_between(current_time, start_time_str, end_time_str):
    start_time = dt_time.fromisoformat(start_time_str)
    end_time = dt_time.fromisoformat(end_time_str)
    current = dt_time.fromisoformat(current_time.strftime('%H:%M:%S'))
    
    if start_time <= end_time:
        return start_time <= current <= end_time
    else:  # Handles overnight periods
        return current >= start_time or current <= end_time

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
            current_time = datetime.now()
            
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
                motion_message = "Motion detected!"
                # Check if within alarm time frame
                if (config['alarm_enabled'] and 
                    is_time_between(current_time, config['alarm_start'], config['alarm_end'])):
                    motion_message += " [ALARM HOURS - Alert triggered!]"
                    socketio.emit('alert', {'data': "Motion detected during alarm hours!"})
                
                mqtt_client.publish(motion_topic, motion_message)
                socketio.emit('motion', {'data': motion_message})
            
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

@app.route('/alarm-config', methods=['GET', 'POST'])
def alarm_config():
    if request.method == 'POST':
        data = request.get_json()
        if 'alarm_start' in data:
            config['alarm_start'] = data['alarm_start']
        if 'alarm_end' in data:
            config['alarm_end'] = data['alarm_end']
        if 'alarm_enabled' in data:
            config['alarm_enabled'] = bool(data['alarm_enabled'])
        return jsonify({'status': 'success'})
    return jsonify({
        'alarm_start': config['alarm_start'],
        'alarm_end': config['alarm_end'],
        'alarm_enabled': config['alarm_enabled']
    })

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
