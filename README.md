# Server Room Monitoring System with MQTT

This project implements a secure IoT-based monitoring system for a server room environment using MQTT protocol, providing real-time temperature monitoring and motion detection with encrypted communications.

## Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/yourusername/TNE20003-MonitoringSystemWithMQTT.git
cd TNE20003-MonitoringSystemWithMQTT
```

2. Create a Python virtual environment (recommended):

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

1. Start User 1 (Administrator) interface:

```bash
python User1_web.py
```

Access the interface at: http://localhost:5000

2. Start User 2 (Operator) interface:

```bash
python User2_web.py
```

Access the interface at: http://localhost:5001

## Configuration

The system settings are centralized in `config.json`. You can modify:

-   MQTT broker settings
-   Default temperature thresholds
-   Alarm time settings
-   Port configurations

## Security

-   All MQTT communications are encrypted using Fernet encryption
-   The encryption key is automatically generated on first run
-   Sensitive data is transmitted through private MQTT channels
