import time
import datetime
import adafruit_dht
import board
import jwt
from gpiozero import LED, MotionSensor
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from flask import Flask, render_template, jsonify, request

MotionSensorPIN = 5
LightSensorPIN = 2

SECRET_KEY = 'vErYsEcuREeEeEeSeCreTTTkEyyyyyyYyYyY'
users= {
    'USERNAME': 'PASSWORD'
}

app = Flask(__name__)

dhtDevice = adafruit_dht.DHT11(board.D18, use_pulseio=False)
sensor = GroveLightSensor(LightSensorPIN)
led = LED(16)
PIR = MotionSensor(MotionSensorPIN)
    
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
        return jsonify({'message': 'Missing token'}), 400
    try: 
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['username']
        try:
            lux = sensor.light 
            temp = dhtDevice.temperature
            humid = dhtDevice.humidity
        except RuntimeError as err:
            print(err.args[0])
        sensor_data = { 'lux' : lux, 'temp' : temp, 'humid': humid}
        return jsonify(sensor_data), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401
    

@app.route('/controllight', methods=['POST'])
def ledHandler():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 400
    try: 
        data = request.json
        if data['led'] == 'on' :
            led.on()
        if data['led'] == 'off' :
            led.off()
        return jsonify({}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401

@app.route('/states')
def ledState():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 400
    try: 
        val = led.value 
        if val == 0:
            ledState = 'off'
        if val == 1:
            ledState = 'on'
        pir = PIR.value
        if pir == 1:
           motion = 'on'
        else:
           motion = 'off'
        return jsonify({'led': ledState, 'motion': motion}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
