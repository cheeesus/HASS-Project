import time
import signal
import datetime
import adafruit_dht
import board
import jwt
import math, threading
from gpiozero import LED, Button, MotionSensor
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from flask import Flask, jsonify, request
from flask_mqtt import Mqtt
import json

a = 1/1.01
b = -0.6
c = 0.01/1.01

Xn = 0.0
Xn_1 = 0.0
Xn_2 = 0.0
En = 1.0
En_toggle = False

sensor_data_error = None
app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = '10.40.46.121'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'mqtt_user'
app.config['MQTT_PASSWORD'] = 'mqttuser'

mqtt = Mqtt(app)
    
LedPIN = 16
ButtonPIN = 17 
LightSensorPIN = 2
MotionSensorPIN = 5
SECRET_KEY = 'vErYsEcuREeEeEeSeCreTTTkEyyyyyyYyYyY'
users= {
    'bourezg': 'passwordofbourezg'
}
@mqtt.on_connect()
def handle_connect(client, userdata, flags,rc):
    if rc == 0:
       print('Connected successfully')
       mqtt.subscribe('homeassistant/data')
       mqtt.subscribe('homeassistant/led/set')
       mqtt.subscribe('homeassistant/params')
       mqtt.subscribe('homeassistant/ack')
    else:
       print('Bad connection. Code:', rc)   

dhtDevice = adafruit_dht.DHT11(board.D18, use_pulseio=False)
sensor = GroveLightSensor(LightSensorPIN)
'''PIR = MotionSensor(MotionSensorPIN)
led = LED(LedPIN)'''
   
@mqtt.on_message()
def handle_message(client, userdata, message):
    global sensor_data_error
    if message.topic == 'homeassistant/params':
        payload = json.loads(message.payload.decode('utf-8'))
        #print(payload['a'])
    elif message.topic == 'homeassistant/ack':
        current_time = time.time()
        payload = json.loads(message.payload.decode('utf-8'))
        sent_time = payload['timestamp']
        round_trip_time = current_time - sent_time
        print(f'round_trip_time :{round_trip_time}' )
    elif message.topic == 'homeassistant/led/set':
        payload = message.payload.decode('utf-8')
        print(payload)
        state = payload
        if payload == 'on':
            led.on()
        elif payload == 'off':
            led.off()   
        mqtt.publish('homeassistant/led/state', state)
    elif message.topic == 'homeassistant/data':
        lux = sensor.light
        pir = PIR.value
        if pir == 1:
           motion = 'on'
        else:
           motion = 'off'
        try:
            temp = dhtDevice.temperature
            humid = dhtDevice.humidity
        except RuntimeError as err:
            print(err.args[0])
            sensor_data_error = 'Failed to retrieve sensor data'
            return
        sensor_data_error = None
        sensor_data = { 'lux' : lux, 'temp' : temp, 'humid': humid, 'motion' : motion}
        print(sensor_data)
        mqtt.publish('homeassistant/sensor', json.dumps(sensor_data))
#second order model        
'''def ISR(signum, frame):
   global Xn, Xn_1, Xn_2, En
   #print(Xn)
   val = { 'val': Xn }
   mqtt.publish('homeassistant/speedtest', json.dumps(val)) 
   Xn = a * Xn_1 + b * Xn_2 + c * En
   Xn_2 = Xn_1
   Xn_1 = Xn     '''  
#first order model
def ISR(signum, frame):
   global Xn, Xn_1, En
   #print(Xn)
   val = { 'val': Xn, 'timestamp': time.time() }
   mqtt.publish('homeassistant/energy', json.dumps(val)) 
   Xn = a * Xn_1 + c * En
   Xn_1 = Xn
   En = 1.0 if not En_toggle else 0.0
   
signal.signal(signal.SIGALRM, ISR)
signal.setitimer(signal.ITIMER_REAL, 0.01,0.01)
 
 
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


if __name__ == '__main__':
   threading.Thread(target = lambda: app.run(debug=True, port=5001, host='0.0.0.0')).start()
   while True:
      time.sleep(50)
      En_toggle = not En_toggle
