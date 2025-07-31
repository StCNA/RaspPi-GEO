from picamera2 import Picamera2, Preview
from libcamera import controls #allows us to configure the camera to suit our requirments
import time
from pynput.keyboard import Key, Listener

current_key = None

def on_key_press(key):
    global current_key
    try: 
        current_key = key.char
    except AttributeError:
        current_key = key
        
def on_key_release(key):
    pass

picam2 = Picamera2()
picam2.start(show_preview=True)
time.sleep(10)

picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
picam2.start(show_preview=True)

listener = Listener(on_press = on_key_press, on_release = on_key_release)
listener.start()

print("camera started. press \'q\' \n press \'x\' to exit")

try:
    while True:
        if current_key == 'q':
            picam2.capture_file('photo.jpg')
            current_key = None
        elif current_key == 'x':
            print("Done...")
            break
except KeyboardInterrupt:
    print("program interupt")
        
        
        
finally:
    picam2.stop()
    listener.stop()
   


