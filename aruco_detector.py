import cv2
import numpy as np
import cv2.aruco as aruco

class ArUcoDetector:
    # initialize all needed variables 
    def __init__(self, is_remote_mode=False):
        self.boat_dictionary = aruco.Dictionary_get(aruco.DICT_4X4_50)
        self.box_dictionary = aruco.Dictionary_get(aruco.DICT_5X5_50)
        self.position_aruco = aruco.Dictionary_get(aruco.DICT_6X6_50)
        self.parameters = aruco.DetectorParameters_create()
        
        # Store camera mode
        self.is_remote_mode = is_remote_mode
        
        # Fixed positions for both main and satellite cameras
        self.aruco_fixed_positions = {
            # Main camera tags (0-3)
            0: [(10,10), (90,10), (90,90), (10,90)],               # Top-left corner
            1: [(1610,10), (1690,10), (1690,90), (1610,90)],        # Top-right corner  
            2: [(10,410), (90,410), (90,490), (10,490)],            # Bottom-left corner
            3: [(1610,410), (1690,410), (1690,490), (1610,490)],    # Bottom-right corner
            
            # Satellite camera tags (5-8)
            5: [(10,10), (90,10), (90,90), (10,90)],               # Top-left corner
            6: [(1610,10), (1690,10), (1690,90), (1610,90)],        # Top-right corner  
            7: [(10,410), (90,410), (90,490), (10,490)],            # Bottom-left corner
            8: [(1610,410), (1690,410), (1690,490), (1610,490)]     # Bottom-right corner
        }
        
        # Set tag IDs based on camera mode
        if is_remote_mode:
            self.slider_tag = 11
            self.reference_tag = 7
            self.required_corner_tags = [5, 6, 7, 8]
        else:
            self.slider_tag = 4
            self.reference_tag = 2
            self.required_corner_tags = [0, 1, 2, 3]
        
        self.slope, self.intercept = self.load_calibration()
        
    def load_calibration(self):
        import pickle
        import os
        if self.is_remote_mode:
            calibration_file = "/media/jeeves003/EMPTY DRIVE/calibration_satellite.pkl"
        else:
            calibration_file = "/media/jeeves003/EMPTY DRIVE/calibration.pkl"
        
        try:
            if os.path.exists(calibration_file):
                with open(calibration_file, 'rb') as f:
                    data = pickle.load(f)
                
                slope = data['slope']
                intercept = data['intercept']
                r_squared = data.get('r_squared', 'N/A')
                cal_date = data.get('calibration_date', 'Unknown')
                
                print(f"Calibration loaded from file")
                
                return slope, intercept
            else:
                print("Using Default values")
                return 1.97, 0.0
                
        except Exception as e:
            print(f" Error loading calibration: {e}")
            print("  Using defaults: slope=1.97, intercept=0")
            return 1.97, 0.0
    
        
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
                # Use slope for rectification (intercept not needed for fixed positions)
                x_pixels = x_mm * self.slope
                y_pixels = y_mm * self.slope
                pixel_corner_list.append((x_pixels, y_pixels))
            pixel_coords[tag_id] = pixel_corner_list
        
        return pixel_coords

    def rectify_image(self, image):
        detected_positions = self.get_pixel_position(image)
        if detected_positions is None:
            print(f"Cannot rectify: ArUco tags not detected ({'satellite' if self.is_remote_mode else 'main'} mode)")
            return None
        
        expected_positions = self.mm_to_pixels()
        
        # Use correct tag set based on camera mode
        required_tags = self.required_corner_tags
        for tag_id in required_tags:
            if tag_id not in detected_positions:
                print(f"Cannot rectify: Missing ArUco tag {tag_id} ({'satellite' if self.is_remote_mode else 'main'} mode)")
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
    
    def positional_aruco_identification(self, image, slider_tag_id=4):
        corners, ids, rejected = aruco.detectMarkers(image, self.position_aruco, parameters=self.parameters)
        if ids is not None:
            for i, tag_id in enumerate(ids.flatten()):
                if tag_id == slider_tag_id:
                    return tag_id, corners[i]
        return None, None
    
    def get_slider_position(self, raw_image, slider_tag_id=None, return_pixels=False):  
        
        if slider_tag_id is None:
            slider_tag_id = self.slider_tag   
        
        tag_id, corners = self.positional_aruco_identification(raw_image, slider_tag_id)
        if tag_id is None:
            print("ERROR: Slider tag not found")
            return None
        # find the center of slider
        slider_corners = corners[0]
        slider_center_x = np.mean(slider_corners[:, 0])
        slider_center_y = np.mean(slider_corners[:, 1])
        
        # use reference 
        tag2_id, tag2_corners = self.positional_aruco_identification(raw_image, self.reference_tag)
        if tag2_id is None:
            print(f"ERROR: Reference tag {self.reference_tag} not found")
            return None
        
        # find the center of the tag 2 
        tag2_corners_array = tag2_corners[0]
        tag2_center_x = np.mean(tag2_corners_array[:, 0])
        tag2_center_y = np.mean(tag2_corners_array[:, 1])
        
        # Calculate HORIZONTAL distance (X-axis) from Tag 2 to slider
        distance_x_pixels = slider_center_x - tag2_center_x
        
        print(f"  Slider center: ({slider_center_x:.1f}, {slider_center_y:.1f})")
        print(f"  Tag 2 center: ({tag2_center_x:.1f}, {tag2_center_y:.1f})")
        print(f"  Horizontal distance: {distance_x_pixels:.1f} pixels")
        
        # If calibration mode, return raw pixels (NOT converted to mm)
        if return_pixels:
            print(f"  >>> CALIBRATION MODE: Returning RAW PIXELS: {int(distance_x_pixels)}")
            return int(distance_x_pixels)
        
        # Normal measurement mode: convert pixels to mm
        if self.slope == 0:
            print("ERROR: Slope is zero - cannot calculate distance")
            return None
        
        distance_x_mm = (distance_x_pixels - self.intercept) / self.slope
    
        print(f"  Calibration - Slope: {self.slope:.4f}, Intercept: {self.intercept:.4f}")
        print(f"  Distance in mm: {distance_x_mm:.1f}mm")
        
        return int(distance_x_mm)
    
    def debug_all_tags(self, image):
        """Show all detected tags"""
        corners, ids, rejected = aruco.detectMarkers(image, self.position_aruco, parameters=self.parameters)
        
        print("\n" + "="*50)
        print(f"MODE: {'SATELLITE' if self.is_remote_mode else 'MAIN'}")
        print(f"Expected slider: {self.slider_tag}")
        print(f"Expected reference: {self.reference_tag}")
        print(f"Expected corners: {self.required_corner_tags}")
        print("-"*50)
        
        if ids is not None:
            detected = list(ids.flatten())
            print(f"DETECTED: {detected}")
            print(f"  Slider {self.slider_tag}: {'✓ FOUND' if self.slider_tag in detected else '✗ MISSING'}")
            print(f"  Reference {self.reference_tag}: {'✓ FOUND' if self.reference_tag in detected else '✗ MISSING'}")
        else:
            print("DETECTED: NONE")
        
        print(f"Rejected: {len(rejected)}")
        print("="*50 + "\n")
            
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
