try:
    import copy
    #from Crypto.Cipher import AES
    from io import BytesIO
    import os # os module is used to work with the operating system, in this case used for mikdir (making directories)
    import numpy as np #images in python are stored as multi-dimensional arrays, numpy allows us to preform operations on these arays (manipulating pictures)
    #from picamera.array import PiRGBArray #PiRGBArray allows for capturing frames directly as NumPy arrays in RGB format
    from picamera2 import Picamera2
    import pickle #serializing and deserializing, convert pictures to byte form
    import RPi.GPIO as GPIO #gives us access to raspi GPIO breadboard, which gives us access to other functionallites 
    import socket #allows us to setup communcation between our two raspi's, client and server
    from subprocess import call 
    import sys
    sys.path.append('/home/pi/.local/lib/python3.5/site-packages/cv2') #
    import cv2 #imports opencv module
    import time
    from libcamera import controls
except Exception as e:
    print ("import python packages pbm")
    print (e)
    input("Press enter...")

#===========================================================================================================================
#===========================================================================================================================

####################################################################################################################
#                                                                                                                  #
#                                         #####  #       ###    ####   ####                                        #
#                                         #      #      #   #  #      #                                            #
#                                         #      #      #####   ###    ###                                         #
#                                         #      #      #   #      #      #                                        #
#                                         #####  #####  #   #  ####   ####                                         #
#                                                                                                                  #
####################################################################################################################

#===========================================================================================================================
#===========================================================================================================================

#class acts as a foundation for colour management in the code, i.e. Button_color = color_combi(50, 120, 0 )
class COLOR_COMBI (object):
    def __init__(self, RED = 0, GREEN = 0, BLUE = 0):
        self.RED = RED
        self.GREEN = GREEN
        self.BLUE = BLUE

#===========================================================================================================================
#===========================================================================================================================

class LocalCAM(object):

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    # DEFINE BASIC VARIABLES
    # map GPIO pin allocation
    TOP = 32
    RED = 36
    GREEN = 38
    BLUE = 40
    # list top light modes
    TOP_LIGHT = {"ON": 1, "OFF": 0, "white": 1, "black": 0}
     # list cameras and camera modes
    ROTATION = 0
    # list available resolutions
    CAM_RES = [(1920,1080), (2592,1944), (1296,972), (1296,730), (640,480)]
    # list available ISO, ISO controls light sensitivity, higher the value better low light
    CAM_ISO = [100,200]

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def __init__(self, cam_width=640, cam_height=480, im_width=640, im_height=480, iso=100):
        # mark cam as not ready
        self.MCready = False
        # initiate GPIO mode
        GPIO.setmode(GPIO.BOARD) # gpio pins are numbered from 1-40 in the way they show uo
        GPIO.setwarnings(False)
        # define GPIO allocations for LEDS
        GPIO.setup(self.TOP,GPIO.OUT)
        GPIO.setup(self.RED,GPIO.OUT)
        GPIO.setup(self.GREEN,GPIO.OUT) 
        GPIO.setup(self.BLUE,GPIO.OUT) # all of these are set on output mode
        # set initial values/modes for top light, background light and camera selection
        self.set_top_light(switch="ON")
        # set references
        self.camera = None
        self.rawCapture = None
        # set initial resolution and iso
        self.set_cam_resolution(cam_width, cam_height)
        self.set_im_resolution(im_width, im_height)
        self.set_cam_iso(iso)
        # initialize camera
        self.init_camera()
        #camera controls
        self.set_autofocus()
        # turn off top light and background light
        self.set_top_light(switch="OFF")
        # mark cam as ready
        self.MCready = True
        

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def set_top_light (self, switch = "OFF"):
        GPIO.output(self.TOP,self.TOP_LIGHT[switch])

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def set_cam_resolution(self, width=640, height=480):
        # make sure the value are integers and assemble the resolution tuple
        w = int(width)
        h = int(height)
        resolution = (w,h)
        # check that the resolution tuple is part of accepted values
        if resolution in self.CAM_RES:
            # set new resolution
            self.cam_resolution = resolution
            # release camera
            if self.camera:
                self.camera.close()
                self.camera = None
            # release rawCapture array
            if self.rawCapture:
                self.rawCapture.truncate(0)
                self.rawCapture = None
        else :
            # default on 640x480
            self.cam_resolution = (640,480)
            # release camera
            if self.camera:
                self.camera.close()
                self.camera = None
    '''=================================================================================================================='''
    '''=================================================================================================================='''
    
    def set_autofocus(self, mode="CONTINUOUS"):
        # Define accepted modes
        modes = {
            "CONTINUOUS": controls.AfModeEnum.Continuous,
            "MANUAL": controls.AfModeEnum.Manual,
            "AUTO": controls.AfModeEnum.Auto
        }
        # Check if mode is valid, default to CONTINUOUS if not
        if mode.upper() in modes:
            mode_setting = modes[mode.upper()]
        else:
            mode_setting = controls.AfModeEnum.Continuous
        # Default to continuous
        self.autofocus_mode = mode_setting
        # Store the setting
        
        if self.camera:
            self.camera.set_controls({"AfMode": mode_setting})
        # Apply to camera if it exists
         
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def set_im_resolution(self, width=640, height=480):
        # make sure the value are integers and assemble the resolution tuple
        w = int(width)
        h = int(height)
        resolution = (w,h)
        self.im_resolution = resolution
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def set_cam_iso(self, iso = 100):
        # make sure the value is an integer
        i = int(iso)
        # check that the iso is part of accepted values
        if i in self.CAM_ISO:
            self.iso = i
            # release camera
            if self.camera:
                self.camera.close()
                self.camera = None
            # release rawCapture array
            if self.rawCapture:
                self.rawCapture.truncate(0)
                self.rawCapture = None
        else :
            # default on iso 100
            self.iso = 100
            # release camera
            if self.camera:
                self.camera.close()
                self.camera = None

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def close(self):
        # release the camera
        if self.camera:
            self.camera.close()
            self.camera = None
        # set top light to off
        self.set_top_light(switch = "OFF")
        # release GPIO pins
        GPIO.cleanup()

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def init_camera(self):
        try:
            camera = Picamera2()
        
        # Configure camera with PiCamera2 syntax
            config = camera.create_still_configuration(
            main={"size": self.cam_resolution}  # Use resolution from your settings
            )
            camera.configure(config)
        
        # Start the camera
            camera.start()
        
        # Let the camera exposure settle
            time.sleep(4)
        
        # Set ISO equivalent (AnalogueGain) and white balance
            controls = {
                "AwbEnable": True,                    # Disable auto white balance  
                #"ColourGains": (1.4, 1.5),           # Set manual red and blue gains
                "AnalogueGain": self.iso / 100.0      # Convert ISO to gain (100 ISO = 1.0 gain)
            }
            camera.set_controls(controls)
        
            # NOW assign to self.camera
            self.camera = camera
        
            # Remove rawCapture - PiCamera2 doesn't need it
            # self.rawCapture = None  # Not needed for PiCamera2
        
            print("Camera initialized successfully")
        
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera = None
            raise
        

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def capture(self):
        if not self.camera:
            print("Camera not initialized")
            return None
        try:
            # PiCamera2 captures directly to numpy array
            image = self.camera.capture_array("main")

            # vestigial code, can be removed. 
            # Convert if needed for OpenCV compatibility, ensure in rgb
            #if len(image.shape) == 3:
             #   image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
            return image
        
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
    '''=================================================================================================================='''
    '''=================================================================================================================='''
    
    def get_preview_frame(self):
        if not self.camera:
            print("Camera is not currently running..")
            return None
        try:
            frame = self.camera.capture_array()
            return frame
        except Exception as e:
            print(f"Preview capture failed: {e}")
            return None
                
    '''=================================================================================================================='''
    '''=================================================================================================================='''

        
    def get_preview_image(self):
        return self.capture()  
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    
    def is_ready(self):
        return self.MCready and self.camera is not None
