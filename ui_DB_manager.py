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
            project_ID             INTEGER PRIMARY KEY AUTOINCREMENT,
            depth_from             TEXT,
            depth_to               TEXT,
            core_numb              INTEGER,
            box_numb               INTEGER,
            BH_ID                  INTEGER,
            before_image_data      BLOB,
            after_image_data       BLOB,
            add_boat_1             BLOB,
            add_boat_2             BLOB,
            add_boat_3             BLOB,
            add_boat_4             BLOB
            )""")
        
        self.c.execute("""CREATE TABLE IF NOT EXISTS box_tag_table (
            tag_ID              INTEGER PRIMARY KEY AUTOINCREMENT,
            aruco_tag_number    INTEGER,
            project_ID          INTEGER,
            FOREIGN KEY (project_ID) REFERENCES project_table (project_ID))""")
        
        
    
    def insert_to_proj_tbl(self, depth_from, depth_to, core_numb, box_numb, BH_ID, numpy_array):
            f = BytesIO()
            np.savez_compressed(f, frame=numpy_array)
            f.seek(0)
            binary_data = f.read()
            self.c.execute("INSERT INTO project_table VALUES (NULL,?,?,?,?,?)",(depth_from, depth_to, core_numb, box_numb, BH_ID, binary_data))
            project_ID = 1000 + self.c.lastrowid
            self.conn.commit()
            return project_ID
        
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
            print(f"Project {project_ID} does not exisit")
        self.conn.commit()
        
    def image_to_binary(self, image_path):
        try:
            with open(image_path,'rb') as file:
                binary_data = file.read()
                print(f"Image converted  to binary: {len(binary_data)}bytes")
                return binary_data
        except FileNotFoundError:
            print(f"file {image_path} not found")
        except Exception as e:
            print(f"Image transfer failed{e}")
            
    def numpy_to_binary(self, numpy_array):
        try: 
            import numpy as np 
            # Use the same technique as server side
            f = BytesIO() #create temp contianer
            np.savez_compressed(f, frame=numpy_array) #compress array onto the temp container file
            f.seek(0) #reset to the start of the file
            binary_data = f.read() #f.read meaning write to the 'f' (temp file), 
            
            print(f"Numpy array converted to binary: {len(binary_data)} bytes")
            print(f"Original size: {numpy_array.nbytes} bytes")
            print(f"Compression ratio: {numpy_array.nbytes / len(binary_data):.2f}x smaller")
            return binary_data
        except Exception as e:
            print(f"Numpy conversion failed: {e}")
            return None
        
        
    def retrieve_before_image(self, project_ID):
        self.c.execute("SELECT before_image_data FROM project_table WHERE project_ID = ?", (project_ID,))
        result = self.c.fetchone()

        if result is None:
            print(f"There is no project with the Id: {project_ID}")
            return None
        
        binary_data = result[0]
        if binary_data is None:
            print(f"Project {project_ID} exists but no BEFORE image stored")
            return None
        
        f = BytesIO(binary_data)
        loaded_data = np.load(f)
        array = loaded_data['frame']
        return array

    def retrieve_after_image(self, project_ID):
        self.c.execute("SELECT after_image_data FROM project_table WHERE project_ID = ?", (project_ID,))
        result = self.c.fetchone()

        if result is None:
            print(f"There is no project with the Id: {project_ID}")
            return None
        
        binary_data = result[0]
        if binary_data is None:
            print(f"Project {project_ID} exists but no AFTER image stored")
            return None
        
        f = BytesIO(binary_data)
        loaded_data = np.load(f)
        array = loaded_data['frame']
        return array
   
    def check_project_status(self):
        print("====Checking Project Status====")
        if not self.current_project_id:
            print("No active project selected")
            return False
        else:
            print(f"Active Project: {self.current_project_id}")
            return True

    
    def check_database_projects(self):
        print("=== Database Contents ===")
        self.c.execute("SELECT project_ID, depth_from, depth_to, core_numb, box_numb, BH_ID FROM project_table")
        projects = self.c.fetchall()
        
        print(f"Total projects in database: {len(projects)}")
        for project in projects:
            print(f"Project {project[0]}: {project[1]} to {project[2]}, Box {project[3]}")
            
    def create_project(self, depth_from, depth_to, core_numb, box_numb, BH_ID):
        # Create project with NULL for both images
        self.c.execute("INSERT INTO project_table VALUES (NULL,?,?,?,?,?,NULL,NULL,NULL,NULL,NULL,NULL)",
                    (depth_from, depth_to, core_numb, box_numb, BH_ID))
        project_ID = self.c.lastrowid
        self.conn.commit()
        return project_ID
    
    def update_before_image(self, project_ID, numpy_array):        
        f = BytesIO()
        np.savez_compressed(f, frame=numpy_array)
        f.seek(0)
        binary_data = f.read()
        self.c.execute("UPDATE project_table SET before_image_data=? WHERE project_ID=?",
                    (binary_data, project_ID))
        self.conn.commit()
        print(f"BEFORE image updated for project {project_ID}")
        
    def update_after_image(self, project_ID, numpy_array):
        f = BytesIO()
        np.savez_compressed(f, frame=numpy_array)
        f.seek(0)
        binary_data = f.read()
        self.c.execute("UPDATE project_table SET after_image_data=? WHERE project_ID=?",
                    (binary_data, project_ID))
        self.conn.commit()
        print(f"AFTER image updated for project {project_ID}")
        
    def release_project_tags(self, project_ID):
        self.c.execute("UPDATE boat_tag_table SET project_ID = NULL WHERE project_ID = ?", (project_ID,))
        self.c.execute("UPDATE box_tag_table SET project_ID = NULL WHERE project_ID = ?", (project_ID,))
        self.conn.commit()
        print(f"All ArUco tags released from project {project_ID}")
        
    def verify_project_tags(self, project_ID, detected_boat_tags, detected_box_tags):
        if detected_boat_tags is None and detected_box_tags is None:
            return False
        
        # Check boat tags if any were detected
        if detected_boat_tags is not None:
            for tag_num in detected_boat_tags.flatten():
                self.c.execute("SELECT * FROM boat_tag_table WHERE aruco_tag_number = ? AND project_ID = ?", (str(tag_num), project_ID))
                if not self.c.fetchone():
                    print(f"Boat tag {tag_num} does not belong to project {project_ID}")
                    return False
        
        # Check box tags if any were detected  
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
        project_list = [] #create empty list to add 'pseudo variable'
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
    #where to place the next boat slot (wether 1,2,3)
    def find_next_boat_slot(self, project_ID):
        self.c.execute("SELECT add_boat_1, add_boat_2, add_boat_3, add_boat_4 FROM project_table WHERE project_ID = ?", (project_ID,))
        boat_slots = self.c.fetchone()
        #Check slots 1-4, return first NULL slot
        for i, slot in enumerate(boat_slots):
            if slot is None:
                return i + 1 
        return None  
    
    def update_add_boat_img(self, project_ID, slot_number, numpy_array):
        f = BytesIO()
        np.savez_compressed(f, frame=numpy_array)
        f.seek(0)
        binary_data = f.read()
        
        column_name = f"add_boat_{slot_number}"
        query = f"UPDATE project_table SET {column_name} = ? WHERE project_ID = ?"
        self.c.execute(query, (binary_data, project_ID))
        self.conn.commit()
                       
db = DbManager()
