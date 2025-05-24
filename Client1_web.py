from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from datetime import datetime, time as dt_time
from utils.encryption import EncryptionManager
import json
import paho.mqtt.client as mqtt
import threading
import time
import random

# Load configuration
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

# Initialize config
config_data = load_config()

# Global variables
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins for development
mqtt_client = None
publish_thread = None
mqtt_thread = None
encryption_manager = EncryptionManager()

# Global configuration
config = config_data['default_settings']

# MQTT Settings
primary_broker = config_data['mqtt']['primary_broker']
fallback_broker = config_data['mqtt']['fallback_broker']
port = config_data['mqtt']['port']
motion_topic = config_data['mqtt']['topics']['motion']
temperature_topic = config_data['mqtt']['topics']['temperature']
cooling_topic = config_data['mqtt']['topics']['cooling']
config_topic = config_data['mqtt']['topics']['config']

# Time configuration
def is_time_between(current_time, start_time_str, end_time_str):
    # Convert string times to datetime.time objects
    start_time = dt_time.fromisoformat(start_time_str)
    end_time = dt_time.fromisoformat(end_time_str)
    current = current_time.time()  # Get time component of datetime
    
    if start_time <= end_time:
        # Simple case: start time is before end time (e.g., 09:00 to 17:00)
        return start_time <= current <= end_time
    else:
        # Overnight case: start time is after end time (e.g., 22:00 to 06:00)
        return current >= start_time or current <= end_time

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    if rc == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe([(cooling_topic, 0), (temperature_topic, 0), (motion_topic, 0)])
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
            decrypted_message = encryption_manager.decrypt(msg.payload)
            socketio.emit('cooling_command', {'data': decrypted_message})
        elif msg.topic == temperature_topic:
            temperature = float(encryption_manager.decrypt(msg.payload))
            socketio.emit('temperature', {'data': temperature})
        elif msg.topic == motion_topic:
            motion_message = encryption_manager.decrypt(msg.payload)
            socketio.emit('motion', {'data': motion_message})
        elif msg.topic == config_topic:
            config_updates = json.loads(encryption_manager.decrypt(msg.payload))
            for key, value in config_updates.items():
                if key in config:
                    config[key] = value
            socketio.emit('config_update', {'data': config})
    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
def connect_mqtt():
    print("Setting up MQTT client...")
    mqtt_client = mqtt.Client()
    
    # Try primary broker first
    try:
        print(f"Attempting to connect to primary broker at {primary_broker}:{port}")
        mqtt_client.username_pw_set("102779797", "102779797")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.connect(primary_broker, port, 60)
        return mqtt_client
    except Exception as e:
        print(f"Failed to connect to primary broker: {e}")
        
        # Try fallback broker
        try:
            print(f"Attempting to connect to fallback broker at {fallback_broker}:{port}")
            mqtt_client = mqtt.Client()  # Create new client instance
            mqtt_client.on_connect = on_connect
            mqtt_client.on_disconnect = on_disconnect
            mqtt_client.on_message = on_message
            mqtt_client.connect(fallback_broker, port, 60)
            return mqtt_client
        except Exception as e:
            print(f"Failed to connect to fallback broker: {e}")
            raise

# MQTT initialization
def init_mqtt():
    global mqtt_client, mqtt_thread, publish_thread
    
    if mqtt_client is not None:
        return  # Already initialized
        
    try:
        mqtt_client = connect_mqtt()
        
        # Start MQTT loop in a separate thread
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()

        # Start publishing in a separate thread
        publish_thread = threading.Thread(target=generate_and_publish)
        publish_thread.daemon = True
        publish_thread.start()
        
    except Exception as e:
        print(f"Error initializing MQTT: {e}")
        mqtt_client = None

def cleanup():
    global mqtt_client, mqtt_thread, publish_thread
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None
    
    # The threads are daemon threads, so they will be terminated automatically

def generate_and_publish():
    while True:
        try:
            current_time = datetime.now()
            
            # Generate temperature data
            temperature = round(random.uniform(20, 30), 2)
            
            # Publish to MQTT
            if mqtt_client:
                # Encrypt and publish temperature
                temp_msg = f"{temperature}"
                encrypted_temp = encryption_manager.encrypt(temp_msg)
                mqtt_client.publish(temperature_topic, encrypted_temp)
                socketio.emit('temperature', {'data': temperature})
                print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Published temperature: {temp_msg}°C")
                
                # Generate motion detection
                motion = random.choice([True, False])
                if motion:
                    # Create the base motion message
                    motion_message = "Motion detected!"
                    log_message = motion_message
                    
                    # Check if motion alert should be triggered
                    if config['alarm_enabled']:
                        # Check if current time is within alarm hours
                        is_alarm_time = is_time_between(
                            current_time,
                            config['alarm_start'],
                            config['alarm_end']
                        )
                        if is_alarm_time:
                            log_message += " [ALARM HOURS - Alert triggered!]"
                            print(f"Alarm triggered! Time: {current_time.strftime('%H:%M:%S')}, Start: {config['alarm_start']}, End: {config['alarm_end']}")
                            socketio.emit('alert', {'data': "Motion detected during alarm hours!"})
                    
                    # Emit both messages - one for display, one for log
                    socketio.emit('motion', {'data': motion_message, 'log_message': log_message})
                    
                    # Encrypt and publish motion message
                    encrypted_motion = encryption_manager.encrypt(log_message)
                    mqtt_client.publish(motion_topic, encrypted_motion)
                    print(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Published motion: {log_message}")
            
        except Exception as e:
            print(f"Error in generate_and_publish: {e}")
            socketio.emit('mqtt_status', {'status': 'error'})
        
        # Sleep for exactly 5 seconds between iterations
        time.sleep(5)

@app.route('/')
def index():
    return render_template('client1.html')

@app.route('/config', methods=['GET', 'POST'])
def update_config():
    if request.method == 'POST':
        data = request.get_json()
        if 'temp_threshold' in data:
            config['temp_threshold'] = float(data['temp_threshold'])
            # Encrypt and publish the new threshold to MQTT
            if mqtt_client:
                encrypted_config = encryption_manager.encrypt(json.dumps({'temp_threshold': config['temp_threshold']}))
                mqtt_client.publish(config_topic, encrypted_config)
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
        print("Initializing MQTT...")
        init_mqtt()
        print("Starting Flask-SocketIO server...")
        socketio.run(app, debug=False, port=5000, host='0.0.0.0')
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        print("Cleaning up...")
        cleanup()
