# Home Automation System
This repository contains the code for an IoT system that uses both MQTT and RESTful APIs in a Home Assistant Server. In addition to that, an emulation of a temperature regulation system using two correctors (Proportional Integral with anti-WindUp effect and an ON/OFF corrector with hysterisis). the temperature regulation system is available only in the MQTT version.

## Structure
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
* Please make sure you run your python files in a virtual environement.
Example
Here is an example of an automation that turns on a light when motion is detected and light intensity is low:
```yaml
- id: "1714987031054"
  alias: Turn off light when intensity is high
  description: ""
  trigger:
    - platform: state
      entity_id:
        - binary_sensor.motion
      to: "on"
    - platform: numeric_state
      entity_id:
        - sensor.light
      below: 299
  condition: []
  action:
    - service: mqtt.publish
      data:
        topic: homeassistant/led/set
        payload: "on"
  mode: single
```
This automation specifies that when the Light intensity is low and there is motion detected in the area. the LED light is turned on by sending a payload 'on' to the `homeassistant/led/set` topic

### Notes
* The code is written for educational purposes only.
* Please refer to the documentation of the specific libraries used in this repository for more information.
