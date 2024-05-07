
import time
import datetime
import adafruit_dht
import board
import jwt
from gpiozero import LED, Button
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from flask import Flask, jsonify, request
from flask_mqtt import Mqtt
import json

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = '10.40.46.91'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'mqtt_user'
app.config['MQTT_PASSWORD'] = 'mqttuser'

mqtt = Mqtt(app)

@mqtt.on_connect()
def handle_connect(client, userdata, flags,rc):
    if rc == 0:
       print('Connected successfully')
       mqtt.subscribe('homeassistant/led/set')
    else:
       print('Bad connection. Code:', rc)
       
@mqtt.on_message()
def handle_message(client, userdata, message):
    if message.topic == 'homeassistant/led/set':
        payload = message.payload.decode('utf-8')
        print(payload)
        state = payload
        if payload == 'on':
            led.on()
        elif payload == 'off':
            led.off()   
    mqtt.publish('homeassistant/led/state', state)
    
    
LedPIN = 16
ButtonPIN = 17
LightSensorPIN = 2

SECRET_KEY = 'vErYsEcuREeEeEeSeCreTTTkEyyyyyyYyYyY'
users= {
    'bourezg': 'passwordofbourezg'
}

dhtDevice = adafruit_dht.DHT11(board.D18, use_pulseio=False)
sensor = GroveLightSensor(LightSensorPIN)
led = LED(LedPIN)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
        
    if username not in users or users[username] != password:
        return jsonify({'message': 'invalid uservame or password'}), 401
        
    token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days = 30)},SECRET_KEY)
    
    return jsonify({'token': token}), 200
 
@app.route('/data')
def data():

    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 401
        
    try: 
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['username']
        lux = sensor.light
        try:
            temp = dhtDevice.temperature
            humid = dhtDevice.humidity
        except RuntimeError as err:
            print(err.args[0])
            return jsonify({'message': 'failed to retrieve sensor data'}), 500
        sensor_data = { 'lux' : lux, 'temp' : temp, 'humid': humid}
        mqtt.publish('homeassistant/sensor', json.dumps(sensor_data))
        return jsonify(sensor_data), 200
    
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401
        
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')