from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins

# MQTT Settings
primary_broker = "192.168.12.100"
fallback_broker = "localhost"
port = 1883
temperature_topic = "public/server-room/temp"  # Public channel for temperature
cooling_topic = "public/server-room/cooling"  # Subscribe to cooling commands
config_topic = "public/server-room/config"  # Topic for configuration updates

# Global variables
mqtt_client = None
mqtt_thread = None
temp_threshold = 28.0  # Default threshold, will be updated from User1
manual_override = False  # Manual override state
manual_cooling = False  # Manual cooling state
last_temperature = None  # Store the last received temperature

# MQTT callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe([(temperature_topic, 0), (config_topic, 0)])
    socketio.emit('mqtt_status', {'status': 'connected'})

def on_message(client, userdata, msg):
    global temp_threshold, last_temperature
    try:
        if msg.topic == temperature_topic:
            temperature = float(msg.payload.decode())
            last_temperature = temperature  # Store the temperature
            print(f"Received temperature: {temperature}°C")
            
            # Emit temperature to all connected clients
            socketio.emit('temperature', {'data': temperature})
            
            # Only control cooling if manual override is not enabled
            if not manual_override:
                # Generate cooling command based on temperature and current threshold
                if temperature > temp_threshold:
                    cooling_command = "ON"
                else:
                    cooling_command = "OFF"
                
                # Publish cooling command and emit to clients    
                mqtt_client.publish(cooling_topic, cooling_command)
                print(f"Generated cooling command: {cooling_command} (current threshold: {temp_threshold}°C)")
                socketio.emit('cooling_command', {'data': cooling_command})
            
        elif msg.topic == config_topic:
            # Handle configuration updates
            config_data = json.loads(msg.payload.decode())
            if 'temp_threshold' in config_data:
                old_threshold = temp_threshold
                temp_threshold = float(config_data['temp_threshold'])
                print(f"Temperature threshold updated: {old_threshold}°C -> {temp_threshold}°C")
                # Emit the new threshold to clients
                socketio.emit('threshold_update', {'threshold': temp_threshold})
                print(f"Emitted threshold update to connected clients")

    except ValueError as e:
        print(f"Error processing message: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# MQTT client setup
def connect_mqtt():
    print("Setting up MQTT client...")
    mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)  # Use MQTT v5 protocol
    
    # Try primary broker first
    try:
        print(f"Attempting to connect to primary broker at {primary_broker}:{port}")
        mqtt_client.username_pw_set("102779797", "102779797")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(primary_broker, port, 60)
        return mqtt_client
    except Exception as e:
        print(f"Failed to connect to primary broker: {e}")
        
        # Try fallback broker
        try:
            print(f"Attempting to connect to fallback broker at {fallback_broker}:{port}")
            mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)  # Create new client instance with MQTT v5
            mqtt_client.on_connect = on_connect
            mqtt_client.on_message = on_message
            mqtt_client.connect(fallback_broker, port, 60)
            return mqtt_client
        except Exception as e:
            print(f"Failed to connect to fallback broker: {e}")
            raise

def init_mqtt():
    global mqtt_client, mqtt_thread
    
    if mqtt_client is not None:
        return  # Already initialized
        
    try:
        mqtt_client = connect_mqtt()
        
        # Start MQTT loop in a separate thread
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        
    except Exception as e:
        print(f"Error initializing MQTT: {e}")
        mqtt_client = None

def cleanup():
    global mqtt_client, mqtt_thread
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None

@app.route('/')
def index():
    return render_template('user2.html')

@socketio.on('manual_override')
def handle_manual_override(data):
    global manual_override, manual_cooling
    try:
        manual_override = data['enabled']
        if manual_override:
            manual_cooling = data['cooling']
            # Generate cooling command based on manual setting
            cooling_command = "ON" if manual_cooling else "OFF"
            mqtt_client.publish(cooling_topic, cooling_command)
            print(f"Manual override: Cooling set to {cooling_command}")
            socketio.emit('cooling_command', {'data': cooling_command})
        else:
            manual_cooling = False
            # Revert to automatic control - check current temperature
            if mqtt_client and last_temperature is not None:
                print("Manual override disabled - reverting to automatic control")
                # Simulate a new temperature message to trigger automatic control
                on_message(mqtt_client, None, type('obj', (), {
                    'topic': temperature_topic, 
                    'payload': str(last_temperature).encode()
                })())
        
        socketio.emit('override_status', {
            'manual_override': manual_override,
            'manual_cooling': manual_cooling
        })
    except Exception as e:
        print(f"Error in manual override: {e}")

if __name__ == '__main__':
    try:
        print("Initializing MQTT...")
        init_mqtt()
        print("Starting Flask-SocketIO server...")
        socketio.run(app, debug=False, port=5001, host='0.0.0.0')  # Set debug=False to prevent reloading
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        print("Cleaning up...")
        cleanup()
