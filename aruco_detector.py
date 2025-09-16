import cv2
import numpy as np
import cv2.aruco as aruco

class ArUcoDetector:
    # initialize all needed variables 
    def __init__(self):
        self.boat_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)
        self.box_dictionary = aruco.Dictionary_get(aruco.DICT_5X5_50)
        self.position_aruco = aruco.Dictionary_get(aruco.DICT_6X6_50)
        self.parameters = aruco.DetectorParameters_create()
        self.aruco_fixed_positions = {
            0: [(10,10), (90,10), (90,90), (10,90)],               # Top-left corner
            1: [(1610,10), (1690,10), (1690,90), (1610,90)],        # Top-right corner  
            2: [(10,410), (90,410), (90,490), (10,490)],            # Bottom-left corner
            3: [(1610,410), (1690,410), (1690,490), (1610,490)]    # Bottom-right corner
        }
        self.pixel_density = 5
        
    def tag_detector(self, image, tag_type):
        if tag_type == '4':
            corners, ids, rejected = aruco.detectMarkers(image, self.boat_dictionary, parameters=self.parameters)
            print(f"Boat tags - Detected: {len(ids) if ids is not None else 0}, Rejected: {len(rejected)}")
            if len(rejected) > 0:
                print(f"Found {len(rejected)} rejected boat tag candidates")
            return ids
        elif tag_type == '5':
            corners, ids, rejected = aruco.detectMarkers(image, self.box_dictionary, parameters=self.parameters)
            print(f"Box tags - Detected: {len(ids) if ids is not None else 0}, Rejected: {len(rejected)}")
            if len(rejected) > 0:
                print(f"Found {len(rejected)} rejected box tag candidates")
            return ids
        elif tag_type == '6':
            corners, ids, rejected = aruco.detectMarkers(image, self.position_aruco, parameters=self.parameters)
            print(f"Position tags - Detected: {len(ids) if ids is not None else 0}, Rejected: {len(rejected)}")
            return ids, corners
        else: 
            print("Tag does not exist in this file")
            return None
    
    def get_pixel_position(self, image):
        ids, corners = self.tag_detector(image, '6') 
        
        if ids is None or corners is None:
            print("Positional aruco tags no detected")
            return None 
        
        pixel_positions = {}
        
        #loop through 
        for i, tag_id in enumerate(ids.flatten()):
            tag_corners = corners[i][0] # extract 4 corner points
            
            corner_list = []
            for corner in tag_corners:
                x = int(corner[0])
                y = int(corner[1])
                corner_list.append((x, y))
            
            pixel_positions[tag_id] = corner_list
            
            
        return pixel_positions
            
    def mm_to_pixels(self):
        pixel_coords = {}
        
        for tag_id, corner_list in self.aruco_fixed_positions.items():
            pixel_corner_list = []
            for (x_mm, y_mm) in corner_list:
                x_pixels = x_mm * self.pixel_density
                y_pixels = y_mm * self.pixel_density
                pixel_corner_list.append((x_pixels, y_pixels))
            pixel_coords[tag_id] = pixel_corner_list
        
        return pixel_coords
    
    def rectify_image(self, image):
        #get detected ArUco positions
        detected_positions = self.get_pixel_position(image)
        if detected_positions is None:
            print("Cannot rectify: ArUco tags not detected")
            return None
    
        expected_positions = self.mm_to_pixels()
        
        #check all tags 
        required_tags = [0, 1, 2, 3]
        for tag_id in required_tags:
            if tag_id not in detected_positions:
                print(f"Cannot rectify: Missing ArUco tag {tag_id}")
                return None
            
        src_pts = []
        dst_pts = []
        
        for tag_id in required_tags:
            corners = detected_positions[tag_id]
            src_pts.append(corners)
            dst_pts.append(expected_positions[tag_id])
        
        src_pts = self._reshape_pts(src_pts)
        dst_pts = self._reshape_pts(dst_pts)
        
        #image size calcualtion
        all_expected_corners = []
        for tag_id in required_tags:
            all_expected_corners.extend(expected_positions[tag_id])

        max_x = max(corner[0] for corner in all_expected_corners)
        max_y = max(corner[1] for corner in all_expected_corners)
        size = (int(max_x), int(max_y))
        
        # Michel Code
        homography_mtx, status = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        rectified_image = cv2.warpPerspective(image, homography_mtx, size)
        
        return rectified_image
    
    def _reshape_pts(self, pts):
        _pts=[]
        for tag_corners in pts:
            for corner in tag_corners:
                _pts.append([corner[0], corner[1]])  # Always treat as (x, y)
        return np.array(_pts).astype(float)

        
if __name__ == "__main__":
    from local_camera import LocalCAM
    
    detector = ArucoDetector()
    camera = LocalCAM()
    
    print("ArUco Production Test")
    print("1. Position physical ArUco tags in camera view")
    print("2. Press Enter to capture and test detection...")
    input()
    
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
        
        # Test position tag detection and pixel extraction
        print("Testing position tag pixel extraction...")
        pixel_positions = detector.get_pixel_position(image)
        if pixel_positions:
            print("Position tags found with corners:")
            for tag_id, corners in pixel_positions.items():
                print(f"  Tag {tag_id}: {corners}")
        else:
            print("No position tags detected")
                
    else:
        print("Camera capture failed")
        
    camera.close()
