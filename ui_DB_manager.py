import sqlite3
from io import BytesIO
import numpy as np
import os
from datetime import datetime
import cv2
import threading

class DbManager:
    def __init__(self):
        self.conn = sqlite3.connect(r'/media/jeeves003/EMPTY DRIVE/raspi.db')
        self.c = self.conn.cursor()
        self.current_project_id = None
        self.current_project_info = None
        self.boats_linked_amnt = 0
        self.before_image_saved = False
        self.project_complete = False
        self.create_tables()
        
    def create_tables(self):
        self.c.execute("""CREATE TABLE IF NOT EXISTS boat_tag_table (
            tag_ID              INTEGER PRIMARY KEY AUTOINCREMENT,
            aruco_tag_number    INTEGER,
            project_ID          INTEGER,
            FOREIGN KEY (project_ID) REFERENCES project_table (project_ID))""")
        
        self.c.execute("""CREATE TABLE IF NOT EXISTS project_table (
            project_ID                  INTEGER PRIMARY KEY AUTOINCREMENT,
            depth_from                  TEXT,
            depth_to                    TEXT,
            core_numb                   INTEGER,
            box_numb                    INTEGER,
            BH_ID                       INTEGER,
            before_image_data           TEXT,
            after_image_data            TEXT,
            add_boat_1                  TEXT,
            add_boat_2                  TEXT,
            add_boat_3                  TEXT,
            add_boat_4                  TEXT
            )""")
        
        self.c.execute("""CREATE TABLE IF NOT EXISTS box_tag_table (
            tag_ID              INTEGER PRIMARY KEY AUTOINCREMENT,
            aruco_tag_number    INTEGER,
            project_ID          INTEGER,
            FOREIGN KEY (project_ID) REFERENCES project_table (project_ID))""")
        
    def boat_tag_insert(self, aruco_tag_number, project_ID):
        self.c.execute("INSERT INTO boat_tag_table VALUES(NULL,?,?)",(aruco_tag_number, project_ID))
        print("Entry Added")
        tag_ID = self.c.lastrowid
        self.conn.commit()
        return tag_ID
    
    def box_tag_insert(self, aruco_tag_number, project_ID):
        self.c.execute("INSERT INTO box_tag_table VALUES (NULL,?,?)",(aruco_tag_number, project_ID))
        print("Entry Added")
        tag_ID = self.c.lastrowid
        self.conn.commit()
        return tag_ID
    
    def delete_from_proj_tbl(self, project_ID):
        self.c.execute("SELECT * FROM project_table WHERE project_ID=?",(project_ID,))
        result = self.c.fetchone()
        if result != None:
            print("Deleting from DB")
            self.c.execute("DELETE FROM project_table WHERE project_ID=?",(project_ID,))
            print(f"Project {project_ID} deleted from the database")
        else:
            print(f"Project {project_ID} does not exist")
        self.conn.commit()
    
    def get_image_filepath(self, BH_ID, core_numb, box_numb, depth_from, depth_to, image_type):
        print(f"BH_ID: {BH_ID}, core_numb: {core_numb}, box_numb: {box_numb}")
        print(f"depth_from: {depth_from}, depth_to: {depth_to}, image_type: {image_type}")
        # create file name and path
        if "rectified" in image_type:
            base_folder = "/media/jeeves003/EMPTY DRIVE/core_imaging_data_rectified"
        else:
            base_folder = "/media/jeeves003/EMPTY DRIVE/core_imaging_data"
        
        filename = f"{str(BH_ID)}-{str(core_numb)}-{str(box_numb)}-{str(depth_from)}-{str(depth_to)}_{str(image_type)}.jpg"
        filepath = f"{base_folder}/{filename}"
        print(f"Generated filepath: {filepath}")
        return filepath
        
    def save_image_to_file(self, numpy_array, filepath):
        print(f"Saving image to file")
        try:
            # If it's bytes data, convert it first
            if isinstance(numpy_array, bytes):
                print("Converting bytes to numpy array")
                f = BytesIO(numpy_array)
                loaded_data = np.load(f)
                numpy_array = loaded_data['frame']
                print(f"Converted array shape: {numpy_array.shape}")
            
            #validate directory
            directory = os.path.dirname(filepath)
            print(f"Ensuring directory exists: {directory}")
            os.makedirs(directory, exist_ok=True)
            
            print("Converting BGR to RGB...")
            rgb_array = cv2.cvtColor(numpy_array, cv2.COLOR_BGR2RGB)
            
            #save image
            print(f"Saving image to: {filepath}")
            success = cv2.imwrite(filepath, rgb_array)
            if success:
                print(f"Image saved successfully to {filepath}")
                return True
            else:
                print(f"cv2.imwrite failed for {filepath}")
                return False
                
        except Exception as e:
            print(f"Error saving image to {filepath}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_image_type(self, workflow_type, slot_number=None):
        print(f"Getting image type for workflow: {workflow_type}, slot: {slot_number}")
        if workflow_type == "before":
            result = "before_rectified" if is_rectified else "before"
        elif workflow_type == "after": 
            result = "after_rectified" if is_rectified else "after"
        elif workflow_type == "boat" and slot_number:
            result = f"boat_{slot_number}_rectified" if is_rectified else f"boat_{slot_number}"
        else:
            result = "unknown"
        return result
        
    def retrieve_before_image(self, project_ID):
        print(f"Retrieving after image for project {project_ID}")
        self.c.execute("SELECT before_image_data FROM project_table WHERE project_ID = ?", (project_ID,))
        result = self.c.fetchone()

        if result is None:
            print(f"There is no project with the Id: {project_ID}")
            return None
        
        file_path = result[0]
        print(f"File path from database: {file_path}")
        if file_path is None:
            print(f"Project {project_ID} exists but no BEFORE image stored")
            return None
        
        try:
            image = cv2.imread(file_path)
            if image is not None:
                print(f"Image loaded successfully from {file_path}")
            else:
                print(f"Failed to load image from {file_path}")
            return image
        except Exception as e:
            print(f"Error loading image from {file_path}: {e}")
            return None

    def retrieve_after_image(self, project_ID):
        print(f"Retrieving after image for project {project_ID}")
        self.c.execute("SELECT after_image_data FROM project_table WHERE project_ID = ?", (project_ID,))
        result = self.c.fetchone()

        if result is None:
            print(f"There is no project with the Id: {project_ID}")
            return None
        
        file_path = result[0]
        print(f"File path from database: {file_path}")
        if file_path is None:
            print(f"Project {project_ID} exists but no AFTER image stored")
            return None
        
        try:
            image = cv2.imread(file_path)
            if image is not None:
                print(f"Image loaded successfully from {file_path}")
            else:
                print(f"Failed to load image from {file_path}")
            return image
        except Exception as e:
            print(f"Error loading image from {file_path}: {e}")
            return None
        
    def check_project_status(self):
        print("Checking project status")
        if not self.current_project_id:
            print("No active project selected")
            return False
        else:
            print(f"Active Project: {self.current_project_id}")
            return True

    def check_database_projects(self):
        print("Database Contents")
        self.c.execute("SELECT project_ID, depth_from, depth_to, core_numb, box_numb, BH_ID FROM project_table")
        projects = self.c.fetchall()
        
        print(f"Total projects in database: {len(projects)}")
        for project in projects:
            print(f"Project {project[0]}: {project[1]} to {project[2]}, Box {project[3]}")
            
    def create_project(self, depth_from, depth_to, core_numb, box_numb, BH_ID):
        print(f"Creating project: BH_ID={BH_ID}, core={core_numb}, box={box_numb}")
        # Create project with NULL for all images
        self.c.execute("INSERT INTO project_table VALUES (NULL,?,?,?,?,?,NULL,NULL,NULL,NULL,NULL,NULL)",
                    (depth_from, depth_to, core_numb, box_numb, BH_ID))
        project_ID = self.c.lastrowid
        self.conn.commit()
        print(f"Project created with ID: {project_ID}")
        return project_ID
    
    def update_before_image(self, project_ID, rectified_image):
        # Get project data
        self.c.execute("SELECT BH_ID, core_numb, box_numb, depth_from, depth_to FROM project_table WHERE project_ID = ?", (project_ID,))
        project_data = self.c.fetchone()
        
        if project_data is None:
            return False
            
        BH_ID, core_numb, box_numb, depth_from, depth_to = project_data
        image_type = self.get_image_type("before")
        
        # Save original image to file (not in database)
        original_path = self.get_image_filepath(BH_ID, core_numb, box_numb, depth_from, depth_to, image_type, is_rectified=False)
        self.save_image_to_file(original_image, original_path)
        
        # Save rectified image to file AND database
        rectified_path = self.get_image_filepath(BH_ID, core_numb, box_numb, depth_from, depth_to, image_type, is_rectified=True)
        if self.save_image_to_file(rectified_image, rectified_path):
            # Store ONLY rectified path in database
            self.c.execute("UPDATE project_table SET before_image_data=? WHERE project_ID=?", (rectified_path, project_ID))
            self.conn.commit()
            return True
        return False
        
    def update_after_image(self, project_ID, numpy_array):
        print(f"Updating after image for project {project_ID}")
        print(f"Data type received: {type(numpy_array)}")
        
        self.c.execute("SELECT BH_ID, core_numb, box_numb, depth_from, depth_to FROM project_table WHERE project_ID = ?", (project_ID,))
        project_data = self.c.fetchone()
        
        if project_data is None:
            print(f"Project {project_ID} not found")
            return False
            
        BH_ID, core_numb, box_numb, depth_from, depth_to = project_data
        print(f"Project data: {project_data}")
        
        # Generate file path
        image_type = self.get_image_type("after")
        file_path = self.get_image_filepath(BH_ID, core_numb, box_numb, depth_from, depth_to, image_type)
        print(f"Generated file path: {file_path}")
        
        # Save image to file
        print("About to call save_image_to_file...")
        if self.save_image_to_file(numpy_array, file_path):
            # Store file path in database
            print("Updating database with file path...")
            self.c.execute("UPDATE project_table SET after_image_data=? WHERE project_ID=?", (file_path, project_ID))
            self.conn.commit()
            print(f"AFTER image updated for project {project_ID}")
            return True
        else:
            print(f"Failed to save after image for project {project_ID}")
            return False
        
    def release_project_tags(self, project_ID):
        self.c.execute("UPDATE boat_tag_table SET project_ID = NULL WHERE project_ID = ?", (project_ID,))
        self.c.execute("UPDATE box_tag_table SET project_ID = NULL WHERE project_ID = ?", (project_ID,))
        self.conn.commit()
        print(f"All ArUco tags released from project {project_ID}")
        
    def verify_project_tags(self, project_ID, detected_boat_tags, detected_box_tags):
        if detected_boat_tags is None and detected_box_tags is None:
            return False
        
        # Check boat tags 
        if detected_boat_tags is not None:
            for tag_num in detected_boat_tags.flatten():
                self.c.execute("SELECT * FROM boat_tag_table WHERE aruco_tag_number = ? AND project_ID = ?", (str(tag_num), project_ID))
                if not self.c.fetchone():
                    print(f"Boat tag {tag_num} does not belong to project {project_ID}")
                    return False
        
        # Check box tags  
        if detected_box_tags is not None:
            for tag_num in detected_box_tags.flatten():
                self.c.execute("SELECT * FROM box_tag_table WHERE aruco_tag_number = ? AND project_ID = ?", (str(tag_num), project_ID))
                if not self.c.fetchone():
                    print(f"Box tag {tag_num} does not belong to project {project_ID}")
                    return False
        
        # All detected tags belong to this project
        return True
    
    def release_individual_boat_tags(self, aruco_tag_numbers, project_ID):
        for tag_num in aruco_tag_numbers:
            self.c.execute("UPDATE boat_tag_table SET project_ID = NULL WHERE aruco_tag_number = ? AND project_ID = ?", 
                        (str(tag_num), project_ID))
        self.conn.commit()
        print(f"Released {len(aruco_tag_numbers)} boat tags from project {project_ID}")
    
    def get_boat_tags(self, project_ID):
        self.c.execute("SELECT aruco_tag_number FROM boat_tag_table WHERE project_ID = ?", (project_ID,))
        results = self.c.fetchall()
        return [row[0] for row in results] if results else []

    def get_box_tags(self, project_ID):
        self.c.execute("SELECT aruco_tag_number FROM box_tag_table WHERE project_ID = ?", (project_ID,))
        results = self.c.fetchall()
        return [row[0] for row in results] if results else []
    
    def get_recent_projects(self, limit=20):
        self.c.execute("SELECT project_ID, BH_ID, core_numb FROM project_table ORDER BY project_ID DESC LIMIT ?", (limit,))
        projects = self.c.fetchall()   
        project_list = [] #create empty list to add 
        for project in projects:
            project_id, bh_id, core_numb = project # unpack the tuple 
            self.c.execute("SELECT after_image_data FROM project_table WHERE project_ID = ?", (project_id,))
            after_image = self.c.fetchone()
            
            status = "Closed" if after_image[0] is not None else "Open"
            project_list.append((project_id, bh_id, core_numb, status))
        
        return project_list
    
    #test if 4th position is in use 
    def boat_limit_reached(self, project_ID):
        self.c.execute("SELECT add_boat_4 FROM project_table WHERE project_ID = ?", (project_ID,))
        added_boat = self.c.fetchone()
        if added_boat is not None and added_boat[0] is not None:
            return True
        return False
    
    #where to place the next boat slot (whether 1,2,3)
    def find_next_boat_slot(self, project_ID):
        self.c.execute("SELECT add_boat_1, add_boat_2, add_boat_3, add_boat_4 FROM project_table WHERE project_ID = ?", (project_ID,))
        boat_slots = self.c.fetchone()
        #Check slots 1-4, return first NULL slot
        for i, slot in enumerate(boat_slots):
            if slot is None:
                return i + 1 
        return None  
    
    def update_add_boat_img(self, project_ID, slot_number, numpy_array):
        print(f"Project ID: {project_ID}, Slot: {slot_number}")
        print(f"Data type received: {type(numpy_array)}")
        
        self.c.execute("SELECT BH_ID, core_numb, box_numb, depth_from, depth_to FROM project_table WHERE project_ID = ?", (project_ID,))
        project_data = self.c.fetchone()
        
        if project_data is None:
            print(f"Project {project_ID} not found")
            return False
            
        BH_ID, core_numb, box_numb, depth_from, depth_to = project_data
        print(f"Project data: {project_data}")
        
        # Generate file path
        image_type = self.get_image_type("boat", slot_number)
        file_path = self.get_image_filepath(BH_ID, core_numb, box_numb, depth_from, depth_to, image_type)
        print(f"Generated file path: {file_path}")
        
        # Save image to file
        print("About to call save_image_to_file...")
        if self.save_image_to_file(numpy_array, file_path):
            # Store file path in database
            print("Updating database with file path...")
            column_name = f"add_boat_{slot_number}"
            query = f"UPDATE project_table SET {column_name} = ? WHERE project_ID = ?"
            self.c.execute(query, (file_path, project_ID))
            self.conn.commit()
            print(f"BOAT {slot_number} image updated for project {project_ID}")
            return True
        else:
            print(f"Failed to save boat {slot_number} image for project {project_ID}")
            return False
    

    
db = DbManager()