from ui_DB_manager import DbManager #import database
from aruco_detector import ArUcoDetector #import Aruco 
from local_camera import LocalCAM
import os
import cv2
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox


class BackendManager:
    def __init__(self):
        self.ar = ArUcoDetector()
        self.db = DbManager()
        self.local_camera = LocalCAM()
        self.local_camera_ready = True
        self.current_project_ID = None
        self.is_remote_mode = False
        self.satellite_client = None

    
    def insert_to_proj_tbl(self, depth_from, depth_to, core_numb, box_numb, BH_ID, numpy_array):
        return self.db.insert_to_proj_tbl(depth_from, depth_to, core_numb, box_numb, BH_ID, numpy_array)
    
    def boat_tag_insert(self, aruco_tag_number, project_ID):
        return self.db.boat_tag_insert(aruco_tag_number, project_ID)
    
    def box_tag_insert(self, aruco_tag_number, project_ID):
        return self.db.box_tag_insert(aruco_tag_number, project_ID)
    
    def create_project(self, depth_from, depth_to, core_numb, box_numb, BH_ID):
        return self.db.create_project(depth_from, depth_to, core_numb, box_numb, BH_ID)
    
    def update_before_image(self, project_ID, numpy_array):
        try:
            return self.db.update_before_image(project_ID, numpy_array)
        except Exception as e:
            raise e

    def update_after_image(self, project_ID, numpy_array):
        try:
            return self.db.update_after_image(project_ID, numpy_array)
        except Exception as e:
            raise e
    

    def release_project_tags(self, project_ID):
        self.db.release_project_tags(project_ID)
    
    def verify_project_tags(self, project_ID, detected_boat_tags, detected_box_tags):
        return self.db.verify_project_tags(project_ID, detected_boat_tags, detected_box_tags)
    
    def tag_detector(self, image, tag_type):
        return self.ar.tag_detector(image, tag_type)
    
    def capture_image(self):
        if self.is_remote_mode:
            try:
                # Step 1: get_IM with first connection
                from client_side import PC2RPi_client
                client1 = PC2RPi_client(RPi="Pi_1", port=1515)
                client1.connect_client()
                
                success = client1.request("get_IM")
                client1.close_client()  # Close first connection
                
                if success:
                    # Step 2: send_IM with second connection
                    client2 = PC2RPi_client(RPi="Pi_1", port=1515)
                    client2.connect_client()
                    
                    result = client2.request("send_IM")
                    client2.close_client()  # Close second connection
                    
                    if isinstance(result, tuple) and result[0]:
                        image = result[1]
                        import cv2
                        cv2.imwrite("remote_captured_debug.png", image)
                        return image
                
                return None
                
            except Exception as e:
                print(f"Remote capture error: {e}")
                return None
        else:
            return self.local_camera.capture()
    
    def get_preview_frame(self):
        if self.is_remote_mode:
            try:
                # Create fresh client for preview
                from client_side import PC2RPi_client
                client1 = PC2RPi_client(RPi="Pi_1", port=1515)
                client1.connect_client()
                
                # Step 1: Request preview capture
                success = client1.request("get_preview")
                client1.close_client()
                
                if success:
                    # Step 2: Request the preview image data (separate connection)
                    client2 = PC2RPi_client(RPi="Pi_1", port=1515)
                    client2.connect_client()
                    
                    result = client2.request("send_preview")
                    client2.close_client()
                    
                    if isinstance(result, tuple) and result[0]:
                        image = result[1]
                        return image
                
                return None
                
            except Exception as e:
                print(f"Remote preview error: {e}")
                return None
        else:
            return self.local_camera.get_preview_frame()
        
    def is_camera_ready(self):
        if self.is_remote_mode:
            return self.satellite_client is not None
        else:
            return self.local_camera.is_ready()
    
    def rectify_captured_image(self, image):
        try:
            # Attempt rectification
            rectified = self.ar.rectify_image(image)
            
            if rectified is not None:
                print("Image rectification successful")
                return rectified
            else:
                print("Rectification failed - ArUco tags not detected or insufficient")
                print("Saving original image instead")
                return image
                
        except Exception as e:
            print(f"Rectification error: {e}")
            print("Saving original image instead")
            return image

    def new_box_wrkflw(self, depth_from, depth_to, core_numb, box_numb, BH_ID):
        image = self.capture_image()
        if image is None:
            return 'Error - Could not capture before image'

        project_ID = self.create_project(depth_from, depth_to, core_numb, box_numb, BH_ID)
        
        boat_detected_IDs = self.tag_detector(image, '4')
        box_detected_IDs = self.tag_detector(image, '5')
        position_aruco, corners = self.tag_detector(image, '6')
        
        # ALWAYS rectify the image before saving
        rectified_image = self.rectify_captured_image(image)
        
        if boat_detected_IDs is None and box_detected_IDs is None:
            # Save rectified image (not original)
            self.update_before_image(project_ID, rectified_image)
            return "NO_TAGS_DETECTED", project_ID
        
        if boat_detected_IDs is not None:
            for tag_ID in boat_detected_IDs.flatten():
                if self.db.is_aruco_tag_available(int(tag_ID), 'boat'):
                    self.boat_tag_insert(int(tag_ID), project_ID)
                else:
                    print(f"WARNING: Boat tag {tag_ID} is already in use - skipped")

        if box_detected_IDs is not None:
            for tag_ID in box_detected_IDs.flatten():
                if self.db.is_aruco_tag_available(int(tag_ID), 'box'):
                    self.box_tag_insert(int(tag_ID), project_ID)
                else:
                    print(f"WARNING: Box tag {tag_ID} is already in use - skipped")
                    
        # Save rectified image 
        self.update_before_image(project_ID, rectified_image)
        
        self.current_project_ID = project_ID
        return project_ID

    def return_box_wrkflw(self):
        if not self.current_project_ID:
            return "ERROR - Must be in a project to take after image"
        
        image = self.capture_image()
        if image is None:
            return "ERROR - Could not capture after image"
        
        boat_detected_IDs = self.tag_detector(image, '4')
        box_detected_IDs = self.tag_detector(image, '5')
        
        # ALWAYS rectify the image before saving
        rectified_image = self.rectify_captured_image(image)
        
        # Save rectified image (not original)
        self.update_after_image(self.current_project_ID, rectified_image)
        
        self.release_project_tags(self.current_project_ID)
        completed_project_ID = self.current_project_ID
        self.current_project_ID = None
        return f"Project {completed_project_ID} completed successfully"

    def add_boat_wrkflw(self):
        if not self.current_project_ID:
            return "ERROR - Must be in a project to add boats"

        boat_detection_frame = self.capture_image()
        if boat_detection_frame is None:
            return 'Error - Could not Add Boat'

        boat_detected_ID = self.tag_detector(boat_detection_frame, '4')
        if boat_detected_ID is not None:
            # Check for tag conflicts BEFORE adding
            for tag_ID in boat_detected_ID.flatten():
                if not self.db.is_aruco_tag_available(int(tag_ID), 'boat'):
                    return f"TAG_IN_USE_BOAT_{tag_ID}"
            
            # all tags are available - proceed
            slot = self.db.find_next_boat_slot(self.current_project_ID)
            for tag_ID in boat_detected_ID.flatten():
                self.boat_tag_insert(int(tag_ID), self.current_project_ID)
            
            rectified_image = self.rectify_captured_image(boat_detection_frame)
            self.db.update_add_boat_img(self.current_project_ID, slot, rectified_image)
            
            return "SUCCESS - Boat added"
        else:
            return "No Aruco Boat Tag detected - please reposition boat"
            
    def check_pair_wrkflw(self):
        if not self.current_project_ID:
            return "ERROR - Must be in a project to check tags"
        
        preview_frame = self.get_preview_frame()
        if preview_frame is None:
            return "ERROR - Cannot get camera frame"
        
        boat_detected_IDs = self.tag_detector(preview_frame, '4')
        box_detected_IDs = self.tag_detector(preview_frame, '5')
        
        print(f"Current project ID: {self.current_project_ID}")
        print(f"Detected boat tags: {boat_detected_IDs}")
        print(f"Detected box tags: {box_detected_IDs}")
        
         
        expected_boats = self.db.get_boat_tags(self.current_project_ID)
        expected_boxes = self.db.get_box_tags(self.current_project_ID)
        
        
        verification = self.verify_project_tags(self.current_project_ID, boat_detected_IDs, box_detected_IDs)
        
        print(f"Verification returned: {verification}")
        
        if verification:
            return "Tags verified successfully"
        else:
            return "Tag verification failed"
                    
    def release_boat_wrkflw(self):
        if not self.current_project_ID:
            return "ERROR - Must be in a project to release boats"
        
        preview_frame = self.get_preview_frame()
        if preview_frame is None:
            return "ERROR - Cannot get camera frame"
        
        boat_detected_IDs = self.tag_detector(preview_frame, '4')
        if boat_detected_IDs is None:
            return "No boat tags detected to release"
        
        tag_list = [int(tag_ID) for tag_ID in boat_detected_IDs.flatten()]
        self.db.release_individual_boat_tags(tag_list, self.current_project_ID)
        
        return f"{len(boat_detected_IDs)} boat(s) released"
    
    def get_current_project_info(self):
        if self.current_project_ID:
            # Get project details from database
            self.db.c.execute("""
                SELECT BH_ID, core_numb, depth_from, depth_to, box_numb 
                FROM project_table WHERE project_ID = ?
            """, (self.current_project_ID,))
            project_data = self.db.c.fetchone()
            
            if project_data:
                bh_id, core_numb, depth_from, depth_to, box_numb = project_data
                
                # Get boat and box tags
                boat_tags = self.db.get_boat_tags(self.current_project_ID)
                box_tags = self.db.get_box_tags(self.current_project_ID)
                
                project_info = {
                    'project_id': self.current_project_ID,
                    'bh_id': bh_id,
                    'core_number': core_numb,
                    'box_number': box_numb,
                    'depth_from': depth_from,
                    'depth_to': depth_to,
                    'boat_tags': boat_tags,
                    'box_tags': box_tags
                }
                return project_info
            else:
                return None
        else:
            return None

    def update_current_project_file(self):
        try:
            with open('/tmp/current_project.txt', 'w') as f:
                if self.current_project_ID:
                    f.write(str(self.current_project_ID))
                else:
                    f.write('')
        except Exception as e:
            print(f"Error writing current project file: {e}")
            
    
    def set_remote_mode(self, remote_mode):
        self.is_remote_mode = remote_mode
    
        if remote_mode:
            try:
                from client_side import PC2RPi_client
                test_client = PC2RPi_client(RPi="Pi_1", port=1515)
                test_client.connect_client()
                result = test_client.request("test")
                test_client.close_client()
                return result
            except Exception as e:
                print(f"Remote connection test failed: {e}")
                self.is_remote_mode = False
                return False
        
        return True

bk = BackendManager()