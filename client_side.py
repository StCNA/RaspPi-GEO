############################################################################################
#------------------------------------------------------------------------------------------#
#------------------------IMPORTS FROM PYTHON PACKAGES--------------------------------------#
#------------------------------------------------------------------------------------------#
############################################################################################

try:
    import socket
    import sys
    import time
    import numpy as np
    import pickle #serializing and deserializing, convert pictures to byte form
    import ast
    import os
    from io import BytesIO
    #from Crypto.Cipher import AES         possible use for encrypted coms if necessary
    import logging
    # set the loggers
    logger = logging.getLogger("PilBud.scanner.client_side")
    BB_logger = logging.getLogger("BlackBox.scanner.client_side")
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

class PC2RPi_client():

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
        "send_preview": "send_preview",
        "get_project_data": "get_project_data",     
        "send_project_data": "send_project_data"
    }

    HOST_IP = {"Pi_1":"169.254.182.213"} #//
    
    # init PC to RPi client
    def __init__ (self, RPi="Pi_1", port=1515):
        try:
            self.encryptionkey = "something"
            self.sock = None
            self.RPi = RPi
            self.host = self.HOST_IP[RPi]
            self.port = port
        
        except Exception as e:
            # report error to logger and raise exception
            logger.error("PC2RPi_client - __init__ error: {0}".format(e))
            raise Exception ("PC2RPi_client - __init__ error: {0}".format(e))

    # define encryption function
    def do_encrypt(self, message):
        # encryption not active for now
        """ obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        ciphertext = obj.encrypt(message)
        return ciphertext """
        return message
    
    # define decryption function
    def do_decrypt(self, ciphertext):
        # decryption not active for now
        """ obj2 = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
        message = obj2.decrypt(ciphertext)
        return message """
        return(ciphertext)

    def connect_client(self):
        # create a socket to communicate with RPi server
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                      #internet comms  #tcp connection, actual connection
        except socket.error :
            # report error to logger
            logger.error("PC2RPi_client - failed to create socket")
            sys.exit()

        # connect the socket to the RPi server
        try :
            self.sock.connect((self.host, self.port))
        except socket.error :
            # report error to logger
            logger.error("PC2RPi_client - failed to connect client socket to RPi 1515 port")
            sys.exit()
    
    def request(self, message=''):
        
        if self.sock is None:
            self.connect_client()
        try:
            # check if request is authorized
            if (message not in self.REQUEST):
                logger.error("PC2RPi_client - unknown request")
                return False
                
            # send message to the RPi server and wait for reply
            self.send_message(message.encode())

            # act on reply
            #------------------------------
            ## "stop_conn" requested
            if message == self.REQUEST["stop_conn"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                # act on data content
                if data == "connection will be closed":
                    return True
                else:
                    return False
            #------------------------------
            ## "start_cam" requested
            if message == self.REQUEST["start_cam"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                # act on data content
                if data == "cam started":
                    return True
                else:
                    return False
            #------------------------------
            ## "cam_ready" requested
            if message == self.REQUEST["cam_ready"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                # act on data content
                if data == "cam ready":
                    return True
                else:
                    return False
            #------------------------------
            ## "stop_cam" requested
            if message == self.REQUEST["stop_cam"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                # act on data content
                if data == "cam off":
                    return True
                else:
                    return False
            #------------------------------
            ## "stop_server" requested
            if message == self.REQUEST["stop_server"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                # act on data content
                if data == "shutting down the server":
                    return True
                else:
                    return False

            #------------------------------
            ## "top_light_off" requested
            if message == self.REQUEST["top_light_off"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "top light off":
                    return True
                return False

            #------------------------------
            ## "top_light_on" requested
            if message == self.REQUEST["top_light_on"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "top light on":
                    return True
                return False

            #------------------------------
            ## "get_IM" requested
            if message == self.REQUEST["get_IM"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "IM done":
                    return True
                return False
            
            #------------------------------
            ## "test" requested
            if message == self.REQUEST["test"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "connection_Ok":
                    return True
                return False
            
            #------------------------------
            ## "set_autofocus" requested
            if message == self.REQUEST["set_autofocus"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "autofocus set":
                    return True
                return False
            
            #------------------------------
            ## "get_preview" requested
            if message == self.REQUEST["get_preview"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "preview done":
                    print("DEBUG CLIENT: get_preview successful")
                    return True
                print("DEBUG CLIENT: get_preview failed")
                return False

            #------------------------------
            ## "send_preview" requested
            if message == self.REQUEST["send_preview"]:
                # init downloaded pic list and image list
                downloaded_pic = False
                image = None
                for i in range(4):
                    # get the reply
                    data = self.get_message().decode("utf-8")
                    if data == "img_ready":
                        # get picture from RPi
                        image = self.receive_picture()
                        downloaded_pic = True
                        # send signal to confirm picture transfer
                        self.send_message(b"pic_received")
                        # get confirmation that the preview transfer process is complete on RPi
                        data = self.get_message().decode("utf-8")
                        if data == "preview_transfered":
                            return True, image
                        else:
                            return False, None
                    else:
                        logger.error("PC2RPi_client error: get_preview request returned unexpected information")
                        print("get_preview request returned unexpected information")
                        return False, None
            
            #------------------------------
            ## "send_IM" requested
            if message == self.REQUEST["send_IM"]:
                # init downloaded pic list and image list
                downloaded_pic = False
                image = None
                for i in range(4):
                    # get the reply
                    data = self.get_message().decode("utf-8")
                    print(f"Received message: '{data}'")
                    if data == "img_ready":
                        # get picture from RPi
                        image = self.receive_picture()
                        downloaded_pic = True
                        # send signal to confirm picture transfer
                        self.send_message(b"pic_received")
                        # get confirmation that the image acquisition process is complete on RPi
                        data = self.get_message().decode("utf-8")
                        if data == "all_images_transfered":
                            return True, image
                        else:
                            return False, None
                    else:
                        logger.error ("PC2RPi_client error: get_image request returned unexpected information")
                        print ("get_image request returned unexpected information")
                        return False, None
            
            
            #------------------------------
            ## "get_project_data" requested
            if message == self.REQUEST["get_project_data"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "project_data_ready":
                    return True
                return False
            #------------------------------
            ## "send_project_data" requested
            if message == self.REQUEST["send_project_data"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "no_project":
                    return False, None
                else:
                    # Project data as JSON string
                    return True, data

            #------------------------------
            ## "shutdown" requested
            if message == self.REQUEST["shutdown"]:
                # get the reply
                data = self.get_message().decode("utf-8")
                if data == "starting_shutdown":
                    return True
                return False

        except Exception as e:
            logger.error("PC2RPi_client - request error: {0} failed - {1}".format(message, e))
            return False

    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def get_message(self, msize=4096): #msize, max message size, 4096 is 4 Kilobytes
        data = self.do_decrypt(self.sock.recv(msize))
        return data
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def send_message(self, message):
        try :
            self.sock.sendall(self.do_encrypt(message))
            # print("sent {0}".format(message))
        except socket.error :
            logger.error("PC2RPi_client - failed to send message to RPi 1515 port")

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def get_array(self, msize):
        try:
            ultimate_buffer = b""
            while True:
                data = self.do_decrypt(self.sock.recv(4194304))
                ultimate_buffer += data
                if len(data) == '0':
                    break
                if len(ultimate_buffer) >= msize:
                    ultimate_buffer = ultimate_buffer[:msize]
                    break
            final_image = np.load(BytesIO(ultimate_buffer))['frame']
            # print('frame received')
            return final_image
        
        except Exception as e:
            # report error to logger
            logger.error("PC2RPi_client - get_array error: {0}".format(e))

    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def receive_picture(self):
        # send signal to get picture dimensions
        try :
            self.send_message(b"pic_dim")
        except socket.error :
            logger.error("PC2RPi_client - failed to send message to RPi 1515 port")
        # get the reply
        data = self.get_message().decode("utf-8")
        I_dim = ast.literal_eval(data)
        print("Image dim: {0}".format(I_dim))
        # send signal to get message size
        try :
            self.send_message(b"send_msize")
        except socket.error :
            logger.error("PC2RPi_client - failed to send message to RPi 1515 port")
        # get the reply
        data = self.get_message().decode("utf-8")
        msize = int(data)
        print("msize = {0}".format(msize))
        # send signal to start picture transfer
        flag1 = time.time()
        try :
            self.send_message(b"send_pic")
        except socket.error :
            logger.error("PC2RPi_client - failed to send message to RPi 1515 port")
        # receive picture data
        data = self.get_array(msize)              # verify received format (b""?)
        print("{0}".format(time.time()-flag1))
        print("array size : {0}".format(data.shape))
        # reformat data into picture array
        # data_variable = pickle.loads(data)
        I = data  #_variable
        return I
        

    '''=================================================================================================================='''
    '''=================================================================================================================='''
    def request_picture(self):
        """Request and receive picture from satellite Pi"""
        try:
            self.send_request("send_IM")
            return self.get_picture()  # This should use your existing picture transfer protocol
        except Exception as e:
            print(f"Picture request failed: {e}")
            return None
    def send_request(self, message):
        """Wrapper for request method to match backend expectations"""
        return self.request(message)

    def get_response(self):
        """Get response from server"""
        try:
            response = self.get_message()
            return response
        except Exception as e:
            print(f"Error getting response: {e}")
            return None

    def get_picture(self):
        """Get picture using existing receive_picture method"""
        return self.receive_picture()
        
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def close_client(self):
        self.sock.close
        self.sock = None

#===========================================================================================================================
#===========================================================================================================================

