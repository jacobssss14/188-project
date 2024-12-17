import time 
from picamera import PiCamera
from datetime import datetime
import os
import math
import smbus
import csv
import threading
from gps import *
from config import sequence

#Configure GPS Module

gpsd = None #seting the global variable
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next()
#Configure Accelerometer
class MPU6050:
    def __init__(self, bus=1, address=0x68):
        self.bus = smbus.SMBus(bus)
        self.address = address

        # Wake up the MPU6050
        self.bus.write_byte_data(self.address, 0x6B, 0)

        # Configure accelerometer (±2g range)
        self.bus.write_byte_data(self.address, 0x1C, 0)

    def read_raw_data(self, addr):
        high = self.bus.read_byte_data(self.address, addr)
        low = self.bus.read_byte_data(self.address, addr + 1)
        value = (high << 8) | low
        if value > 32767:
            value -= 65536
        return value

    def get_acceleration(self):
        x = self.read_raw_data(0x3B)
        y = self.read_raw_data(0x3D)
        z = self.read_raw_data(0x3F)

        # Convert to acceleration in g
        ax = x / 16384.0
        ay = y / 16384.0
        az = z / 16384.0

        return (ax, ay, az)
    
mpu = MPU6050()

#Configure Light Sensor

DEVICE     = 0x23 # Default device I2C address

POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value

# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23

#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

def convertToNumber(data):
  # Simple function to convert 2 bytes of data
  # into a decimal number. Optional parameter 'decimals'
  # will round to specified number of decimal places.
  result=(data[1] + (256 * data[0])) / 1.2
  return (result)

def readLight(addr=DEVICE):
  # Read data from I2C interface
  data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
  return convertToNumber(data)

iteration = 1
camera = PiCamera(resolution=(640, 320))
#camera.iso = 800
camera.start_preview()
#camera.shutter_speed = 8000
gpsp = GpsPoller()
gpsp.start()
time.sleep(2)
#Define the directory where to save data
file_dir = f'/home/pi/data-storage/data-capture_{sequence}/'
img_dir = f'/home/pi/data-storage/data-capture_{sequence}/image-capture/'
filename = f'/home/pi/data-storage/data-capture_{sequence}/data.csv'
 
data = []

#Create Folders when necessary

if not os.path.exists(file_dir):
  os.makedirs(file_dir)
if not os.path.exists(img_dir):
  os.makedirs(img_dir)

time.sleep(3)

with open(filename, 'w', newline='') as csvfile:
  csvwriter = csv.writer(csvfile)
  csvwriter.writerow(['Timestamp', 'Lux', 'Acceleration', 'Velocity'])
  begin_time = time.time()
  while iteration < 301:
    start_time = time.time() 
    timestamp_temp = datetime.now()
    timestamp = timestamp_temp.strftime('%H%M%S.%f')
    image_path_timestamp = os.path.join(img_dir, f'image_{timestamp}.jpg')
    lightLevel=readLight()
    ax, ay, az = mpu.get_acceleration()
    total_accel = math.sqrt(ax * ax + ay * ay + az * az)
    velocity = gpsd.fix.speed
    row_data = [timestamp, f"{lightLevel:.3f}", f"{total_accel:.3f}", f"{velocity:.3f}"]
    data.append(row_data)
    csvwriter.writerow(row_data)
    camera.capture(image_path_timestamp)
    print("Lux: ", lightLevel)
    print("Acceleration: ", total_accel)
    print("Velocity: ", velocity)
    print(f'{iteration} Images Saved with timestamp')  
    current_time = time.time()
    time_elapsed = current_time-start_time
    sleep_time = 0.2 - time_elapsed
    if sleep_time >= 0: 
      time.sleep(sleep_time)
    print("Sample Time: ", time_elapsed)
    iteration +=1
    if iteration == 301:
      end_time = time.time()
      total_time = end_time - begin_time
      print("Total Time: ", total_time)
      gpsp.running = False
      gpsp.join() # wait for the thread to finish what it's doing
      print('Data Capture Done')
      sequence +=1
      time.sleep(3)
      break
    

