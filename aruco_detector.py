import cv2
import numpy as np
import cv2.aruco as aruco

class ArUcoDetector:
    # initialize all needed variables 
    def __init__(self):
        self.boat_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)
        self.box_dictionary = aruco.Dictionary_get(aruco.DICT_5X5_50)
        #self.position_aruco = aruco.Dictionary_get(aruco.DICT_6X6_50)
        self.parameters = aruco.DetectorParameters_create()
        
    def tag_detector(self, image, tag_type):
        if tag_type == '4' :
            corners, ids, rejected = aruco.detectMarkers(image, self.boat_dictionary, parameters=self.parameters)
            return ids
        elif tag_type == '5':
            corners, ids, rejected = aruco.detectMarkers(image, self.box_dictionary, parameters=self.parameters)
            return ids
        else: 
            print("Tag does not exist in this file")
            return None
    
    def photo_measurements(self):
        pass
        
if __name__ == "__main__":
    from local_camera import LocalCAM
    
    detector = ArucoDetector()
    camera = LocalCAM()
    
    print("ArUco Production Test")
    print("1. Position physical ArUco tags in camera view")
    print("2. Press Enter to capture and test detection...")
    input()
    
    # Capture real image
    image = camera.capture()
    
    if image is not None:
        print("Image captured successfully")
        
        # Test boat tag detection
        boat_ids = detector.tag_detector(image, '4')
        print("Boat tags found:", boat_ids)
        
        # Test box tag detection  
        box_ids = detector.tag_detector(image, '5')
        print("Box tags found:", box_ids)
        
        cv2.imwrite("test_capture.jpg", image)
        print("Image saved as test_capture.jpg")
        
    else:
        print("Camera capture failed")
        
    camera.close()
