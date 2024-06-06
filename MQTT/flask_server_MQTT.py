import time
import adafruit_dht
import board
import math, threading
from gpiozero import LED, MotionSensor
from grove.grove_light_sensor_v1_2 import GroveLightSensor
from flask import Flask
from flask_mqtt import Mqtt
import json
import signal

t = 100
# temperature exterieure : 
Ti_ref = 18.0
Tn =  0.0
Tn_1 = 0.0
Tn_2 = 0.0
Cn = 0.0
Cn_1 = 0.0
Vn = 0.0
Kp = 0.26
Tau_i = 74.82

delta = 0.1
dTn = Ti_ref - Tn
dTn_1 = 0.0
# Constants for the second-order system
K = 20
Tau1 = 8
Tau2 = 50
A = (Tau1 + Tau2) / (Tau1 * Tau2)
B = 1 / (Tau1 * Tau2)
denum = 1 + (delta * A) + (delta * delta * B)
a = (2 + (A * delta)) / denum
b = -1 / denum
c = (K * B * delta * delta) / denum

valve = 0.0
extemp = 0.0
hysteresis = 0.5
dist = 0.0
prev_dist = 0.0
a_dist = delta/Tau2
a_integral = Kp * delta / Tau_i
sensor_data_error = None

app = Flask(__name__)

app.config['MQTT_BROKER_URL'] = '10.40.46.121'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'mqtt_user'
app.config['MQTT_PASSWORD'] = 'mqttuser'

mqtt = Mqtt(app)

LightSensorPIN = 2
MotionSensorPIN = 16

@mqtt.on_connect()
def handle_connect(client, userdata, flags,rc):
    if rc == 0:
       print('Connected successfully')
       mqtt.subscribe('homeassistant/data')
       mqtt.subscribe('homeassistant/led/set')
       mqtt.subscribe('homeassistant/params/first')
       mqtt.subscribe('homeassistant/params/second')
       mqtt.subscribe('homeassistant/params/pi')
       mqtt.subscribe('homeassistant/extemp')
       mqtt.subscribe('homeassistant/ack')
    else:
       print('Bad connection. Code:', rc)   

dhtDevice = adafruit_dht.DHT11(board.D18, use_pulseio=False)
sensor = GroveLightSensor(LightSensorPIN)
PIR = MotionSensor(MotionSensorPIN)
led = LED(24)

@mqtt.on_message()
def handle_message(client, userdata, message):
    global sensor_data_error, delta, tau,t, z, wn, Tau_i, Kp, Ti_ref, extemp
    if message.topic == 'homeassistant/data':
        try:
            pir = PIR.value
            if pir == 1:
               motion = 'on'
            else:
               motion = 'off'
            lux = sensor.light
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
    elif message.topic == 'homeassistant/params/second':
        payload = json.loads(message.payload.decode('utf-8'))
        z = float(payload['z'])
        wn = float(payload['wn'])
        delta = float(payload['delta'])
        t = float(payload['t'])
    elif message.topic == 'homeassistant/params/pi':
        print('here')
        payload = json.loads(message.payload.decode('utf-8'))
        Tau_i = float(payload['taui'])
        Kp = float(payload['kp'])
        Ti_ref = float(payload['tiref']) 
        print(f'changed to {Tau_i}, {Kp}, {Ti_ref}')  
    elif message.topic == 'homeassistant/ack':
        current_time = time.time()
        payload = json.loads(message.payload.decode('utf-8'))
        sent_time = payload['timestamp']
        round_trip_time = current_time - sent_time
        print(f'round_trip_time for PI :{round_trip_time}' )
    elif message.topic == 'homeassistant/extemp':
        global extemp
        payload = json.loads(message.payload.decode('utf-8'))
        extemp = float(payload['extemp'])
    elif message.topic == 'homeassistant/led/set':
        payload = message.payload.decode('utf-8')
        print(payload)
        state = payload
        if payload == 'on':
            led.on()
        elif payload == 'off':
            led.off()   
        mqtt.publish('homeassistant/led/state', state)

#ON OFF Logic 
def ISR_ON_OFF(signum, frame):
   global Ti_ref, Tn, Tn_1, Tn_2, a, b, c, extemp, dist, prev_dist, a_dist,  valve
   prev_valve = valve
   Ti = Tn + dist
   # replace Ti by Tn if no disturbance
   if (Ti_ref - Ti) > hysteresis :
      valve = 1
   elif (Ti_ref - Ti) < (-hysteresis) :
      valve = 0
   else :
      valve = prev_valve
   dist = a_dist * (extemp - prev_dist) +  prev_dist
   # Calculate the output of the system
   Tn = (a * Tn_1) + (b * Tn_2) + (c * valve) 
   # Update state variables
   Tn_2 = Tn_1
   Tn_1 = Tn
   prev_dist = dist
   #if system without disturbance is desired, send Tn as 'val' else send Ti
   val = {'val': Ti, 'ref': Ti_ref, 'valve': valve} 
   mqtt.publish('homeassistant/onoff', json.dumps(val))
   #print(val)

# PI Anti-Windup
def ISR_PI_ANTIWINDUP(signum, frame):
   current_time = time.time()
   global Ti_ref, Tn, dTn, dTn_1, Tn_1, Tn_2, Cn, Cn_1, Kp, a, b, c, Vn, dist, extemp, a_dist, a_integral 
   Ti = Tn + dist
   dist = a_dist * (extemp - dist) +  dist
   # Calculate the error, replace by Tn if no disturbance
   dTn = Ti_ref - Ti
   # anti-windup : stopping the integral when saturation is reached
   if Cn >= 1 or Cn < 0: 
      integral = Cn_1
   else :
      integral = Cn_1 + a_integral * dTn
   # Calculate the control signal (PI controller)
   Cn = integral + Kp * (dTn - dTn_1)
   # actuator saturation
   if Cn < 0:
      Vn = 0
   elif Cn > 1:
      Vn = 1
   else:
      Vn = Cn
   # Calculate the output of the system
   Tn = a * Tn_1 + b * Tn_2 + c * Vn
   # Update state variables
   dTn_1 = dTn
   Tn_2 = Tn_1
   Tn_1 = Tn
   Cn_1 = Cn
   #if system without disturbance is desired, send Tn as 'val' else send Ti
   val = { 'val': Ti, 'ref': Ti_ref, 'cn': Cn, 'extemp': extemp, 'timestamp': current_time } 
   mqtt.publish('homeassistant/pi/antiwindup', json.dumps(val))
   #print(val)

#PI  
def ISR_PI(signum, frame):
   global Ti_ref, Tn, dTn, dTn_1, Tn_1, Tn_2, Cn, Cn_1, Kp, a_integral, a, b, c, Vn
   dTn = Ti_ref - Tn
   # Calculate the control signal (PI controller)
   Cn = Cn_1 + Kp * (dTn - dTn_1) + a_integral * dTn
   # actuator saturation
   if Cn < 0:
      Vn = 0
   elif Cn > 0 and Cn < 1:
      Vn = Cn
   else:
      Vn = 1
   # Calculate the output of the system
   Tn = a * Tn_1 + b * Tn_2 + c * Vn

   # Update state variables
   dTn_1 = dTn
   Tn_2 = Tn_1
   Tn_1 = Tn
   Cn_1 = Cn
   val = { 'val': Tn, 'ref': Ti_ref, 'cn': Cn, 'vn': Vn } 
   mqtt.publish('homeassistant/pi/windup', json.dumps(val))
   #print(val)
'''   
#default params for first order
tau = 20
#default params for second order
z = 0.7
wn = 0.285
#second order model        
def ISR_SECOND(signum, frame):
   global Xn, Xn_1, Xn_2, En, delta
   #print(Xn)
   A = 2 * z * wn
   B = wn * wn
   denum = 1 + (delta*A) + (delta*delta*B)
   a = (2 + (A * delta)) / denum
   b = -1 / denum
   c = ( B * delta*delta ) / denum
   val = { 'val': Xn }
   #print(f'using {delta} and {z} and {wn}')
   mqtt.publish('homeassistant/second', json.dumps(val)) 
   Xn = a * Xn_1 + b * Xn_2 + c * En
   Xn_2 = Xn_1
   Xn_1 = Xn   
   En = 1.0 if not En_toggle else 0.0    
#first order model
def ISR_FIRST(signum, frame):
   global Xn, Xn_1, En, delta, tau, t
   a = tau/(delta+tau)
   c = delta/(delta+tau)
   #print(Xn)
   val = { 'val': Xn, 'timestamp': time.time() }
   #print(f'using {delta} and {tau} and {t}')
   mqtt.publish('homeassistant/first', json.dumps(val)) 
   Xn = a * Xn_1 + c * En
   Xn_1 = Xn
   En = 1.0 if not En_toggle else 0.0 
'''     
# uncomment to use the specific ISR
signal.signal(signal.SIGALRM, ISR_ON_OFF)
#signal.signal(signal.SIGALRM, ISR_PI_ANTIWINDUP)
#signal.signal(signal.SIGALRM, ISR_PI)    
signal.setitimer(signal.ITIMER_REAL, delta,delta)

if __name__ == '__main__':
   threading.Thread(target = lambda: app.run(debug=True, port=5001, host='0.0.0.0')).start()
   while True:
      time.sleep(t)
      
