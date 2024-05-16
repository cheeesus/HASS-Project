import time
import datetime
import adafruit_dht
import board
import jwt
from gpiozero import LED, Button
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from flask import Flask, render_template, jsonify, request


LedPIN = 16
ButtonPIN = 17
LightSensorPIN = 2

SECRET_KEY = 'vErYsEcuREeEeEeSeCreTTTkEyyyyyyYyYyY'
users= {
    'bourezg': 'passwordofbourezg'
}

app = Flask(__name__)

dhtDevice = adafruit_dht.DHT11(board.D18, use_pulseio=False)
sensor = GroveLightSensor(LightSensorPIN)
led = LED(LedPIN)

@app.route('/')
def index():
    now = datetime.datetime.now()
    timeString = now.strftime("%d/%m/%Y %H:%M")
    data = {
        'title' : 'Test Server',
        'time' : timeString,
    }
    return render_template('index.html', **data)
    
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
        
'''@app.route('/read')
def readDht():
    now = datetime.datetime.now()
    timeString = now.strftime("%d/%m/%Y %H:%M")
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print("Temp:{:.1f} C / Humidity: {}%".format(temperature, humidity))
    except RuntimeError as err:
        print(err.args[0])
    values = {
        'title' : 'Test Server',
        'time' : timeString,
        'temp' : temperature,
        'humid' : humidity
    }
    return render_template('index.html', **values)
'''    
@app.route('/data')
def data():
    sent_time = time.time()
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 400
    try: 
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['username']
        lux = sensor.light 
        try:
            temp = dhtDevice.temperature
            humid = dhtDevice.humidity
        except RuntimeError as err:
            print(err.args[0])
        rtt = time.time() - sent_time
        print(rtt)
        return jsonify({ 'lux' : lux, 'temp' : temp, 'humid': humid}), 200
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

@app.route('/led_state')
def ledState():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 400
    try: 
        val = led.value 
        if val == 0:
            state = 'off'
        if val == 1:
            state = 'on'
        return jsonify({'state': state}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
    
'''   
@app.route('/turnonlight', methods=['POST'])
def ledOnHandler():

    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'message': 'Missing token'}), 401
    try: 
        data = request.json
        if data['led'] == 'on' :
            led.on()
        return jsonify({}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401
    
    
@app.route('/turnofflight', methods=['POST'])
def ledOffHandler():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Missing token'}), 401
    try: 
        data = request.json
        if data['led'] == 'off' :
            led.off()
        return jsonify({}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid Token'}), 401
''' 
    

'''@app.route('/led/<action>')
def action(action):
    if action == 'on':
        led.on()
        ledState = led.value
    if action == 'off':
        led.off()
        ledState = led.value
    states = {
        'ledState' : ledState
    }
    return render_template('index.html', **states)
'''
