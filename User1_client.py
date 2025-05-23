import paho.mqtt.client as mqtt
import time
import random
from datetime import datetime

# MQTT Broker settings
MQTT_BROKER = "192.168.12.100"
PRIVATE_MOTION_TOPIC = "102779797/server-room/motion"  # Private channel for motion
TOPIC_1 = "public/server-room/temp"  # Public channel for temperature
TOPIC_2 = "public/server-room/cooling"  # Subscribe to cooling commands

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set("102779797", "102779797")

# Callback when a message is received
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == TOPIC_2:
        print(f"Received cooling command: {payload}")

def generate_temperature():
    return round(random.uniform(22, 42), 1)

def detect_motion():
    return random.choice(["Motion Detected", "No Motion"])

# Set up MQTT callbacks
client.on_message = on_message

# Connect to broker and subscribe to Topic 2
client.connect(MQTT_BROKER)
client.subscribe(TOPIC_2)

# Start the loop in a non-blocking way
client.loop_start()

print("User 1 Client Started - Generating Temperature and Motion Data")
try:
    while True:
        # Generate and publish temperature (Topic 1 - public)
        temperature = generate_temperature()
        client.publish(TOPIC_1, str(temperature))
        print(f"Published temperature: {temperature}°C")

        # Generate and publish motion (Private channel)
        motion = detect_motion()
        client.publish(PRIVATE_MOTION_TOPIC, motion)
        print(f"Published motion status to private channel: {motion}")
        
        time.sleep(10)  # Wait for 10 seconds before next update

except KeyboardInterrupt:
    print("\nStopping the client...")
    client.loop_stop()
    client.disconnect()
