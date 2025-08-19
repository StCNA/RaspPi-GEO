#!/usr/bin/ python3


############################################################################################
#------------------------------------------------------------------------------------------#
#------------------------IMPORTS FROM PYTHON PACKAGES--------------------------------------#
#------------------------------------------------------------------------------------------#
############################################################################################

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

class CAM(object):

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
        # set camera controls
        self.set_autofocus()
        # set initial resolution and iso
        self.set_cam_resolution(cam_width, cam_height)
        self.set_im_resolution(im_width, im_height)
        self.set_cam_iso(iso)
        # initialize camera
        self.init_camera()
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
            # release rawCapture array
            if self.rawCapture:
                self.rawCapture.truncate(0)
                self.rawCapture = None
    

    '''=================================================================================================================='''
    '''=================================================================================================================='''
    
    def set_autofocus(self, mode="CONTINUOUS"):
        # Define accepted modes, #get this to report back needed res  mode, needs to be auto in cont when cam object, return params.
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
            # release rawCapture array
            if self.rawCapture:
                self.rawCapture.truncate(0)
                self.rawCapture = None

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
                "AwbEnable": False,                    # Disable auto white balance  
                "ColourGains": (1.4, 1.5),           # Set manual red and blue gains
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
        
            # PiCamera2 returns RGB, but your code might expect BGR
            # Convert if needed for OpenCV compatibility
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
            return image
        
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None
       

#===========================================================================================================================
#===========================================================================================================================

class PC2RPi_server(object):

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    # list of authorized commands
    REQUEST = {
    "stop_conn": "stop_conn",
    "start_cam": "start_cam",
    "cam_ready": "cam_ready",
    "stop_cam": "stop_cam",
    "stop_server": "stop_server",
    "top_light_off": "top_light_off",
    "top_light_on": "top_light_on",
    "get_IM": "get_IM",
    "send_IM": "send_IM",
    "shutdown": "shutdown",
    "test": "test",
    "set_autofocus": "set_autofocus",
    "get_preview": "get_preview",
    "send_preview": "send_preview"
}
    cam_width=1296   #2592  #640
    cam_height=972   #1944   #480
    im_width=1296   #2592   #640
    im_height=972   #1944   #480
    iso=100
    tempfolder = "Temp/"

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def __init__(self, host="169.254.182.213", port=1515): #// Server on satelite, client on Pi2/main
        self.debug = True
        self.encryptionkey = "something"
        self.sock = None
        self.host = host
        self.port = port
        self.is_bound = False
        self.client_ip = ["169.254.182.214"] #//
        self.conn = None
        self.addr = None
        self.cam = CAM(cam_width=self.cam_width, cam_height=self.cam_height, im_width=self.im_width, im_height=self.im_height, iso=self.iso)
        # prepare variabes for final image
        self.IM = []
        self.IM_ready = False
        # if necessary eval background Cr Cb exclusion values
        if False:
            self.bg_Cr, self.bg_Cb, self.bg_CrW, self.bg_CbW = self.get_bg_exclusion_values()
            print ("bg_Cr: ", self.bg_Cr)
            print ("bg_Cb: ", self.bg_Cb)
            print ("bg_CrW", self.bg_CrW)
            print ("bg_CbW", self.bg_CbW)
        else:
            self.bg_Cr = {"cam1":128, "cam2":128, "cam3":128, "cam4":128}
            self.bg_Cb = {"cam1":119, "cam2":119, "cam3":119, "cam4":119}
            self.bg_CrW = {"cam1":8, "cam2":8, "cam3":8, "cam4":8}
            self.bg_CbW = {"cam1":7, "cam2":7, "cam3":7, "cam4":7}
        

    '''=================================================================================================================='''
    '''=================================================================================================================='''
    def do_encrypt(self, message):
        # encryption not active for now
        """ obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        ciphertext = obj.encrypt(message)
        return ciphertext """
        return message
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def do_decrypt(self, ciphertext):
        # decryption not active for now
        """ obj2 = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        message = obj2.decrypt(ciphertext)
        return message """
        return(ciphertext)

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def start_server(self):
        # check that cam is deployed
        if self.cam is None:
            self.cam = CAM(cam_width=self.cam_width, cam_height=self.cam_height, im_width=self.im_width, im_height=self.im_height, iso=self.iso)
        # create a socket to communicate with PC
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                      #internet comms  #tcp conect, actual connection
        except socket.error:
            print("failed to create socket")
            sys.exit()
        
        # bind the socket to the PC client
        try:
            server_address = ("", self.port)
            self.sock.bind(server_address)
            self.is_bound = True
        except socket.error:
            print("Failed to bind")
            sys.exit()

        # listen for incoming connections (server mode) with one connection at a time
        self.sock.listen(1)
        print(f"...Server listening on port {self.port}")
        print("Ready for client connections...")
        # act on connection and run request
        while True:
            server_on = True
            # wait for a connection
            self.conn, self.addr = self.sock.accept()
            print(self.addr)
            # verify that the connection comes from the right source
            if self.addr[0] in self.client_ip:
                try:
                    # get the message
                    data = self.get_message().decode("utf-8")
                   
                    # act on request
                    #------------------------------
                    ## check that request is authorized
                    if data not in self.REQUEST:
                        # if request is unknown, close the connection
                        self.conn.sendall('unknown request: {0}'.format(data).encode())
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "stop_conn" requested:
                    if data == self.REQUEST["stop_conn"]:
                        self.send_message(b'connection will be closed')
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "start_cam" requested
                    if data == self.REQUEST["start_cam"]:
                        # if cam is not deployed, deploy cam 
                        if self.cam is None:
                            self.cam = CAM(cam_width=self.cam_width, cam_height=self.cam_height, im_width=self.im_width, im_height=self.im_height, iso=self.iso)
                        self.send_message(b'cam started')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "cam_ready" requested
                    if data == self.REQUEST["cam_ready"]:
                        if self.cam is None:
                            self.send_message(b'cam not started')
                        else:
                            if self.cam.MCready:
                                self.send_message(b'cam ready')
                            else:
                                self.send_message(b'cam not ready')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "stop_cam" requested
                    if data == self.REQUEST["stop_cam"]:
                        if self.cam is None:
                            self.send_message(b'cam off')
                        else:
                            self.cam.close()
                            self.cam = None
                            self.send_message(b'cam off')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "stop_server" requested
                    if data == self.REQUEST["stop_server"]:
                        # if necessary shut down the cam
                        if self.cam is not None:
                            self.cam.close()
                            self.cam = None
                        self.send_message(b'shutting down the server')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                        server_on = False   # server_on will be checked at the end of the loop
                    #------------------------------
                    ## "top_light_off" requested
                    if data == self.REQUEST["top_light_off"]:
                        # check that cam is started
                        if self.cam is None:
                            self.send_message(b'cam not started')
                        # check that cam is ready
                        elif not self.cam.MCready:
                            self.send_message(b"cam not ready")
                        else:
                            # switch top light "off" and send confirmation message
                            self.cam.set_top_light(switch = "OFF")
                            self.send_message(b'top light off')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "top_light_on" requested
                    if data == self.REQUEST["top_light_on"]:
                        # check that cam is started
                        if self.cam is None:
                            self.send_message(b'cam not started')
                        # check that cam is ready
                        elif not self.cam.MCready:
                            self.send_message(b"cam not ready")
                        else:
                            # switch top light "on" and send confirmation message
                            self.cam.set_top_light(switch = "ON")
                            self.send_message(b'top light on')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "get_IM" requested
                    if data == self.REQUEST["get_IM"]:
                        # check that cam is started
                        if self.cam is None:
                            self.send_message(b'cam not started')
                        # check that cam is ready
                        elif not self.cam.MCready:
                            self.send_message(b"cam not ready")
                        else:
                            # get image
                            self.IM = self.cam.capture()
                            if self.debug:
                                cv2.imwrite("IM.png", self.IM) #saves a debug copy of the captured image
                                
                            # check IM_ready flag and send message
                            self.IM_ready = True
                            self.send_message(b'IM done')
                        # when finished, close the connection
                        import time
                        time.sleep(0.1)
                        
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "send_IM" requested
                    if data == self.REQUEST["send_IM"]:
                        if self.IM_ready:
                            transfer_ok = True
                            # send picture
                            if self.send_picture(I=self.IM) == False:
                                # if failed
                                transfer_ok = False
                                self.send_message(b"failed img transfer")
                            else:
                                # if transfer was ok, confirm that image acquisition is complete
                                if transfer_ok:
                                    self.send_message(b"all_images_transfered")
                        else:
                            # final image series not ready for transfer, send message
                            self.send_message(b'Image not ready for transfer')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                    #------------------------------
                    ## "shutdown" requested
                    if data == self.REQUEST["shutdown"]:
                        # send message to confirm that the shutdown process is about to start
                        self.send_message(b'starting_shutdown')
                        # close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                        # call command line for shutdown
                        call("sudo shutdown -h now", shell=True)
                    
                     #------------------------------
                     ## "set_autofocus" requested
                    if data == self.REQUEST["set_autofocus"]:
                        self.send_message(b'autofocus set')
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                        
                    #------------------------------
                    if data == self.REQUEST["test"]:
                        self.send_message(b'connection_Ok')
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                   #------------------------------
                    if data == self.REQUEST["get_preview"]:
                        # check that cam is started
                        if self.cam is None:
                            self.send_message(b'cam not started')
                        # check that cam is ready
                        elif not self.cam.MCready:
                            self.send_message(b"cam not ready")
                        else:
                            # get preview image
                            self.preview_IM = self.cam.capture()
                            if self.debug:
                                cv2.imwrite("preview.png", self.preview_IM) #saves a debug copy of the preview image
                                
                            # check preview_ready flag and send message
                            self.preview_ready = True
                            self.send_message(b'preview done')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                        
                    #------------------------------
                    ## "send_preview" requested
                    if data == self.REQUEST["send_preview"]:                       
                        # make sure the preview image is ready
                        if hasattr(self, 'preview_ready') and self.preview_ready:
                            transfer_ok = True
                            # send picture
                            if self.send_picture(I=self.preview_IM) == False:
                                # if failed
                                transfer_ok = False
                                self.send_message(b"failed preview transfer")
                            else:
                                # if transfer was ok, confirm that preview transfer is complete
                                if transfer_ok:
                                    self.send_message(b"preview_transfered")
                        else:
                            # preview not ready for transfer, send message
                            self.send_message(b'Preview not ready for transfer')
                        # when finished, close the connection
                        self.conn.close()
                        self.conn = None
                        self.addr = None
                                        
                    
        
                except Exception as e:
                    print("error in request management")
                    print(e)
            else:
                # if the client address is not identified, close the connection
                print("connection from unidentified client")
                self.conn.close()
                self.conn = None
                self.addr = None

            # if required, close the server and exit the loop
            if server_on == False:
                self.close_server()
                break

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def get_message(self, msize=4096):
        data = self.do_decrypt(self.conn.recv(msize))
        if msize == 4096:
                print(data)
        return data

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def send_message(self, message):
        try :
            self.conn.sendall(self.do_encrypt(message))
        except socket.error :
            print("failed to send message to client")

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def send_array(self, out):
        try :
            self.conn.sendall(self.do_encrypt(out))
        except socket.error :
            print("failed to send message to client")

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def getLargestOdd(self, nb):
         return ((nb) - 1 + ((nb) % 2))

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def send_picture(self, I):
        
        f = BytesIO() #in memory buffer / temp file in Ram
        print("BytesIO activated")
        np.savez_compressed(f,frame=I) # Save several arrays into a single file in compressed .npz format.
        # savez_compressed(fn, x=x, y=y).
        print("image compressed")
        f.seek(0)
        print("reposition cursor")
        out = f.read()
        print("tranfered to out")
        msize = len(f.getvalue())
        print("msize: {0}".format(msize))
        
        # tell client the picture is ready to be sent
        self.send_message("img_ready".encode())
        # wait for picture dimension call
        data = self.get_message().decode("utf-8")
        if data == "pic_dim":
            # send client the picture dimension
            self.send_message(str(I.shape).encode())
        else :
            return False
        # wait for message size call
        data = self.get_message().decode("utf-8")
        if data == "send_msize":
            # send client the message size
            self.send_message(str(msize).encode())
        else :
            return False
        # wait for picture transfer call
        data = self.get_message().decode("utf-8")
        if data == "send_pic":
            # send picture
            self.send_array(out)
            print("sent serialized picture")
        else:
            return False
        # wait for confirmation that picture transfered correctly
        data = self.get_message().decode("utf-8")
        if data == "pic_received":
            return True
        else:
             return False

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def close_server(self):
        self.sock.close()
        self.is_bound = False
        self.sock = None
        
 

#===========================================================================================================================
#===========================================================================================================================

####################################################################################################################
#                                                                                                                  #
#                           #####  #####         #   #   ###   #####  #   #                                        #
#                             #    #             ## ##  #   #    #    ##  #                                        #
#                             #    ###           # # #  #####    #    # # #                                        #
#                             #    #             #   #  #   #    #    #  ##                                        #
#                           #####  #             #   #  #   #  #####  #   #                                        #
#                                                                                                                  #
####################################################################################################################

#===========================================================================================================================
#===========================================================================================================================

if __name__ == "__main__":
    # launch system
    my_server = PC2RPi_server()
    my_server.start_server()
    # set readiness info