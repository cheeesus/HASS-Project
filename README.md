# Home Automation System
This repository contains the code for a home automation system that uses both MQTT and RESTful APIs.

##Structure
The repository is organized into two main directories:

* ### MQTT: Contains the code for the MQTT-based communication.
* ### RESTful: Contains the code for the RESTful API.
Each directory contains the following files:

* `automations.yaml`: Defines the automations that the system will perform. replace your automations.yaml file in your Home Assistant with it.
* `configurations.yaml`: Contains the configuration settings for the system. replace your configurations.yaml file in your Home Assistant with it.
* `flask_server_*.py`: The Flask server code for the respective communication protocol. It should run on another Raspberry Pi that is connected to the sensors.
  
## Requirements
To run this system, you will need the following packages:

* Python 3.6 or later
* Flask
* paho-mqtt
You can install these packages using pip:
```
$ pip install flask paho-mqtt
```
## Usage
### Configure the system:
Edit the `configurations.yaml` file in both the MQTT and RESTful directories to set the desired configuration settings, such as the MQTT broker address and the RESTful API endpoint.
Define the automations:
Edit the `automations.yaml` file in both the MQTT and RESTful directories to define the automations that the system will perform. For example, you can define an automation that turns on a light when a motion sensor is triggered.
### Run the servers:
* Run the `flask_server_MQTT.py` file to start the MQTT server.
* Run the `flask_server_RESTful.py` file to start the RESTful API server.
Example
Here is an example of an automation that turns on a light when a motion sensor is triggered:

```yaml
- name: "Turn on light when motion detected"
  trigger:
    - platform: mqtt
      topic: "motion_sensor/state"
      payload: "on"
  action:
    - service: light.turn_on
      entity_id: light.living_room_light
```
This automation specifies that when the MQTT topic "motion_sensor/state" receives a message with the payload "on", the light entity "light.living_room_light" will be turned on.

### Notes
* The code is written for educational purposes and may not be suitable for production environments.
* Please refer to the documentation of the specific libraries used in this repository for more information.
Please feel free to contribute to this project by submitting pull requests or opening issues.
