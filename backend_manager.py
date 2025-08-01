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
            self.db.update_before_image(project_ID, numpy_array)
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
        if self.is_remote_mode and self.satellite_client:
            try:
                success = self.satellite_client.request("get_IM")
                if success:
                    result = self.satellite_client.request("send_IM")
                    if isinstance(result, tuple) and result[0]:
                        return result[1]  # Return the image
                return None
            except Exception as e:
                print(f"Remote capture error: {e}")
                return None
        else:
            return self.local_camera.capture()

    def get_preview_frame(self):
        if self.is_remote_mode and self.satellite_client:
            try:
                success = self.satellite_client.request("get_IM")
                if success:
                    result = self.satellite_client.request("send_IM")
                    if isinstance(result, tuple) and result[0]:
                        return result[1]  # Return the image
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

    def new_box_wrkflw(self, depth_from, depth_to, core_numb, box_numb, BH_ID):
        image = self.capture_image()
        if image is None:
            return 'Error - Could not capture before image'
        project_ID = self.create_project(depth_from, depth_to, core_numb, box_numb, BH_ID)
        boat_detected_IDs = self.tag_detector(image, '4')
        box_detected_IDs = self.tag_detector(image, '5')
        
        if boat_detected_IDs is None and box_detected_IDs is None:
            return "NO_TAGS_DETECTED", project_ID, image
        
        if boat_detected_IDs is not None:
            for tag_ID in boat_detected_IDs.flatten():
                self.boat_tag_insert(int(tag_ID), project_ID)
        if box_detected_IDs is not None:
            for tag_ID in box_detected_IDs.flatten():
                self.box_tag_insert(int(tag_ID), project_ID)
        
        self.update_before_image(project_ID, image)
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
        
        verification = self.verify_project_tags(self.current_project_ID, boat_detected_IDs, box_detected_IDs)
        if not verification:
            return "Verification failed - Please retake after image and verify tags"
        
        self.update_after_image(self.current_project_ID, image)
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
            slot = self.db.find_next_boat_slot(self.current_project_ID)
            for tag_ID in boat_detected_ID.flatten():
                self.boat_tag_insert(int(tag_ID), self.current_project_ID)
            self.db.update_add_boat_img(self.current_project_ID, slot, boat_detection_frame)
            return "SUCCESS - Boat added"
        else:
            return "No Aruco Boat Tag detected - please reposition boat"
    
    def check_pair_wrkflw(self):
        if not self.current_project_ID:
            return "ERROR - Must be in a project to check tags"
        
        preview_frame = self.get_preview_frame()
        if preview_frame is None:
            return "ERROR - Cannot get camera frame"
        
        # Debug: What tags are detected?
        boat_detected_IDs = self.tag_detector(preview_frame, '4')
        box_detected_IDs = self.tag_detector(preview_frame, '5')
        
        print(f"DEBUG: Current project ID: {self.current_project_ID}")
        print(f"DEBUG: Detected boat tags: {boat_detected_IDs}")
        print(f"DEBUG: Detected box tags: {box_detected_IDs}")
        
        # Debug: What tags should belong to this project?
        expected_boats = self.db.get_boat_tags(self.current_project_ID)
        expected_boxes = self.db.get_box_tags(self.current_project_ID)
        
        print(f"DEBUG: Expected boat tags for project {self.current_project_ID}: {expected_boats}")
        print(f"DEBUG: Expected box tags for project {self.current_project_ID}: {expected_boxes}")
        
        # Debug: Call verification and see what happens
        verification = self.verify_project_tags(self.current_project_ID, boat_detected_IDs, box_detected_IDs)
        
        print(f"DEBUG: Verification returned: {verification}")
        
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
                self.satellite_client = PC2RPi_client(RPi="Pi_1", port=1515)
                self.satellite_client.connect_client()
                    
                # Test connection
                test_result = self.satellite_client.request("test")
                if test_result:
                    return True
                else:
                    self.is_remote_mode = False
                    self.satellite_client = None
                    return False
                        
            except Exception as e:
                print(f"Remote connection failed: {e}")
                self.is_remote_mode = False
                self.satellite_client = None
                return False
        else:
            # Switch back to local
            if self.satellite_client:
                self.satellite_client.close_client()
                self.satellite_client = None
            return True
            
    
        
bk = BackendManager()