import time 
from picamera import PiCamera
from datetime import datetime
import os
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

setup_done = False
timestamp_toggle = True
sequence = 1
camera = PiCamera(resolution=(640, 320), framerate=30)

def toggle (channel):
    global timestamp_toggle
    timestamp_toggle = not timestamp_toggle

def program_start(channel):
    global setup_done
    setup_done = not setup_done

GPIO.add_event_detect(17, GPIO.FALLING, callback=toggle, bouncetime=200)
GPIO.add_event_detect(4, GPIO.FALLING, callback=program_start, bouncetime=200)

while True:

 
  camera.iso = 200
  time.sleep(2)
  sequence = 3
  iteration = 0
  time.sleep(2)

  #Define the directory where to save data
  file_dir = f'/mnt/data-storage/data-capture_{sequence}/'
  img_dir = f'/mnt/data-storage/data-capture_{sequence}/image-capture/'
 
  #Create folders if Necessary

  if not os.path.exists(file_dir):
    os.makedirs(file_dir)
  if not os.path.exists(img_dir):
    os.makedirs(img_dir)

  lcd.clear
  lcd.cursor_pos = (0,0)
  lcd.write_string('Press button 2 to')
  lcd.cursor_pos = (1,0)
  lcd.write_string('toggle timestamp')
  time.sleep(3)

  while setup_done is False:
    lcd.clear()
    lcd.write_string(f'timestamp {timestamp_toggle}')
    time.sleep(0.2)
    if setup_done == True:
      lcd.clear()
      lcd.cursor_pos = (0,0)
      lcd.write_string(f'Image capture {sequence}')
      lcd.cursor_pos = (1,0)
      lcd.write_string('starting in 3s')
      time.sleep(3)  
    
  lcd.clear
  while iteration < 300:
    if timestamp_toggle == True:
      current_time = time.strftime("%Y%m%d-%H%M%S")
      image_path_timestamp = os.path.join(img_dir, f'image_{current_time}.jpg')
      camera.capture(image_path_timestamp, resize=(640, 320))
      lcd.clear()
      lcd.cursor_pos = (0,0)
      lcd.write_string(f'{iteration} Images Saved')
      lcd.cursor_pos = (1,0)
      lcd.write_string(f'with timestamp')
      iteration +=1


    if timestamp_toggle == False:
      image_path_cont = os.path.join(img_dir, f'image_{iteration}.jpg')
      camera.capture(image_path_cont, resize=(640, 320))
      lcd.clear()
      lcd.cursor_pos = (0,0)
      lcd.write_string(f'{iteration} Images Saved')
      iteration +=1
  

    if iteration == 300:
      lcd.clear()
      lcd.cursor_pos = (0,0)
      lcd.write_string('Image Capture Done')
      sequence +=1
      setup_done = not setup_done
      time.sleep(3)
      break
    
    