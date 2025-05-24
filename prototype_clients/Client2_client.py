import paho.mqtt.client as mqtt
import time
import random

# MQTT Broker settings
MQTT_BROKER = "192.168.12.100"
TOPIC_1 = "public/server-room/temp"  # Subscribe to temperature updates from User 1
TOPIC_2 = "public/server-room/cooling"  # Publish cooling commands based on temperature

# MQTT Client Setup
client = mqtt.Client()
client.username_pw_set("102779797", "102779797")

# Callback when a message is received
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == TOPIC_1:
        try:
            temperature = float(payload)
            print(f"Received temperature reading: {temperature}°C")
            
            # Generate cooling command based on temperature
            if temperature > 30:
                cooling_command = "ON"
                print(f"Temperature too high! Sending cooling command: {cooling_command}")
            else:
                cooling_command = "OFF"
                print(f"Temperature normal. Sending cooling command: {cooling_command}")
                
            # Publish the cooling command to Topic 2
            client.publish(TOPIC_2, cooling_command)
            
        except ValueError:
            print(f"Received invalid temperature value: {payload}")

# Set up MQTT callbacks
client.on_message = on_message

# Connect to broker and subscribe to Topic 1
client.connect(MQTT_BROKER)
client.subscribe(TOPIC_1)

# Start the MQTT client loop
print("User 2 Client Started - Monitoring Temperature and Controlling Cooling")
print("Listening for temperature updates...")
client.loop_forever()
