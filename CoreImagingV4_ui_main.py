from CoreImagingV4_ui import Ui_MainWindow
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from backend_manager import bk
import sys
from PIL import Image
from new_project_creation_ui import Ui_CreateNewProject
from ProjectHistory_ui import Ui_ProjectHistory
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from datetime import datetime
from ProjectDetail_ui import Ui_ProjectDetailDialog
from io import BytesIO
import numpy as np
from client_side import PC2RPi_client


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bk = bk
        self.is_remote_mode = False
        self.satellite_client = None
        self.setup_button_groups()
        self.connect_signals()
        
        self.setup_status_display()
        
        self.update_camera_preview()
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_preview)
        self.camera_timer.start(150)
        self.CamArea.setMinimumSize(QtCore.QSize(539, 400))
        self.cameraPreviewLabel.setMinimumSize(QtCore.QSize(539, 400)) 
        self.cameraPreviewLabel.setMaximumSize(QtCore.QSize(539, 400))
        
    def setup_status_display(self):
        # 'Matrix' Styling
        self.textEdit_2.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
        
        # Initial status message
        self.update_status("Core Imaging System initialized")
        self.update_status("Camera starting...")
        
    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.textEdit_2.append(formatted_message)
        # Auto-scroll to bottom
        scrollbar = self.textEdit_2.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        

    def setup_button_groups(self):
        self.source_group = QButtonGroup(self)
        self.source_group.addButton(self.local)
        self.source_group.addButton(self.Remote)
        self.local.setChecked(True)
        
    def connect_signals(self):
        self.pushButton.clicked.connect(self.new_box_clicked)      
        self.pushButton_13.clicked.connect(self.add_boat_clicked)  
        self.pushButton_4.clicked.connect(self.check_pair_clicked) 
        self.pushButton_3.clicked.connect(self.release_boat_clicked)
        self.pushButton_5.clicked.connect(self.return_box_clicked)
        self.pushButton_6.clicked.connect(self.exit_clicked)
        self.pushButton_15.clicked.connect(self.open_project_history)
        self.Remote.clicked.connect(self.remote_clicked)
        self.local.clicked.connect(self.local_clicked)
        
        
    def new_box_clicked(self):
        self.update_status("NEW BOX workflow initiated")
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            depth_from = dialog.lineEdit.text()
            depth_to = dialog.lineEdit_6.text()
            core_number = dialog.lineEdit_5.text()
            box_number = dialog.lineEdit_3.text()
            bh_id = dialog.lineEdit_4.text()
            
            self.update_status(f"Creating project - BHID: {bh_id}, Core: {core_number}")
            
            result = self.bk.new_box_wrkflw(depth_from, depth_to, core_number, box_number, bh_id)
            
            if isinstance(result, tuple) and result[0] == 'NO_TAGS_DETECTED':
                self.update_status("WARNING: No ArUco tags detected in image")
                reply = QMessageBox.question(self, 'No Tags Detected', 
                                            'No ArUco tags were detected in the image.\n\nContinue anyway?',
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    project_id = result[1]
                    self.bk.current_project_ID = project_id
                    self.update_project_display(depth_from, depth_to, core_number, box_number, bh_id, project_id)
                    self.update_status(f"Project {project_id} created successfully (no tags)")
                else:
                    self.update_status("Project creation cancelled by user")
                    return
            elif result:  
                project_id = result
                self.bk.current_project_ID = result
                self.update_project_display(depth_from, depth_to, core_number, box_number, bh_id, project_id)
                self.update_status(f"Project {project_id} created successfully")
        else:
            self.update_status("New box creation cancelled")

    def update_camera_preview(self):
        if self.bk.local_camera_ready or self.bk.is_remote_mode:
            current_array_frame = self.bk.get_preview_frame()  
            if current_array_frame is not None:
                height, width, channel = current_array_frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(current_array_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                preview_frame = QPixmap.fromImage(q_image)
                self.cameraPreviewLabel.setPixmap(preview_frame)
            else:
                if not hasattr(self, 'camera_error_logged'):
                    self.update_status("ERROR: Camera not initialized")
                    self.camera_error_logged = True
        else:
            if not hasattr(self,'camera_error_logged'):
                self.update_status("Camera Error")
                self.camera_error_logged = True
        
    #refresh product display when needed
    def update_project_display(self, depth_from, depth_to, core_number, box_number, bh_id, project_ID):
        boat_tags = self.bk.db.get_boat_tags(project_ID)
        box_tags = self.bk.db.get_box_tags(project_ID)
        boat_display = ", ".join(map(str, boat_tags)) if boat_tags else "None"
        box_display = ", ".join(map(str, box_tags)) if box_tags else "None"
        
        display_text = f"""<center><b>Current Project: {project_ID}</b></center><br>
    BHID: {bh_id} <br>
    Core ID: {core_number} <br>
    Box #: {box_number}<br>
    Depth from (m): {depth_from}<br>
    Depth to (m): {depth_to}<br>
    Box: {box_display}<br>
    Boat(s): {boat_display}"""
        
        self.textEdit.setHtml(display_text)
        self.check_add_boat_button_state()
        
    def clear_project_display(self):
        clear_proj_text = f"""<center><b>No Project</b></center><br>
    BHID: <br>
    Core ID: <br>
    Box #: <br> 
    Depth from (m): <br> 
    Depth to (m): <br>
    Box: <br>
    Boat(s): """
        
        self.textEdit.setHtml(clear_proj_text)
            
    def add_boat_clicked(self):
        self.update_status("ADD BOAT workflow initiated")
        result = self.bk.add_boat_wrkflw()
        if result:
            self.update_status(f"Boat added successfully: {result}")
            self.refresh_current_project_display()
        else:
            self.update_status("WARNING: No boat tags detected or add failed")

    def check_pair_clicked(self):
        self.update_status("CHECK PAIR workflow initiated")
        result = self.bk.check_pair_wrkflw()
        
        # Check the actual string content
        if "successfully" in result:
            self.update_status("Tag pairing successful")
        else:
            self.update_status(f"Tag pairing failed: {result}")
            
    def release_boat_clicked(self):
        self.update_status("RELEASE BOAT workflow initiated")
        result = self.bk.release_boat_wrkflw()
        if result:
            self.update_status("Boat released successfully")
            self.refresh_current_project_display()
        else:
            self.update_status("WARNING: Boat release failed")

    def return_box_clicked(self):
        self.update_status("RETURN BOX workflow initiated")
        self.update_status("Capturing after image...")
        result = self.bk.return_box_wrkflw()
        if result:
            self.update_status("Box returned and project completed successfully")
        else:
            self.update_status("WARNING: Box return failed")
        self.clear_project_display()
    
    def exit_clicked(self):
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.update_status("System shutdown initiated")
            self.close()
    
    def open_project_history(self):
        self.update_status("Opening project history")
        dialog = ProjectHistoryDialog(self)
        dialog.setWindowTitle("Project History")
        dialog.resize(500, 400)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.update_status("Project switched from history")
        else:
            self.update_status("Project history closed")
    
    def check_add_boat_button_state(self):
        #disable boat button if max reached
        if self.bk.current_project_ID:
            if self.bk.db.boat_limit_reached(self.bk.current_project_ID):
                self.pushButton_13.setEnabled(False)
                self.update_status("Add Boat button disabled - 4 boat limit reached")
            else:
                self.pushButton_13.setEnabled(True)
        else:
            self.pushButton_13.setEnabled(False)
    
    def refresh_current_project_display(self):
        if self.bk.current_project_ID:
            # Get current project details from database
            self.bk.db.c.execute("SELECT BH_ID, core_numb, depth_from, depth_to, box_numb FROM project_table WHERE project_ID = ?", (self.bk.current_project_ID,))
            project_data = self.bk.db.c.fetchone()
            
            if project_data:
                bh_id, core_numb, depth_from, depth_to, box_numb = project_data
                # Update the display with current data
                self.update_project_display(depth_from, depth_to, core_numb, box_numb, bh_id, self.bk.current_project_ID)
                self.update_status("Project display refreshed")
            else:
                self.update_status("ERROR: Could not refresh project display")
        else:
            self.update_status("No active project to refresh")
    
    def remote_clicked(self):
        self.update_status("Switching to remote satellite camera...")
    
        success = self.bk.set_remote_mode(True)
        
        if success:
            self.update_status("SUCCESS: Connected to satellite camera!")
            self.update_status("Remote mode active - all buttons now use satellite camera")
        else:
            self.update_status("ERROR: Failed to connect to satellite camera")
            
    def local_clicked(self):
        self.update_status("Switching to local camera...")
        
        success = self.bk.set_remote_mode(False)
        
        if success:
            self.update_status("SUCCESS: Switched to local camera")
        else:
            self.update_status("ERROR: Failed to switch to local camera")

class NewProjectDialog(QDialog, Ui_CreateNewProject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.submitButton.clicked.connect(self.accept)


class ProjectHistoryDialog(QDialog, Ui_ProjectHistory):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent_app = parent
        self.OpenProject.clicked.connect(self.open_selected_project)
        self.load_projects()
        self.ProjectList.itemDoubleClicked.connect(self.open_project_detail)
    
    def load_projects(self):
        projects = self.parent_app.bk.db.get_recent_projects()
        self.ProjectList.clear()
        
        for project in projects:
            project_id, bh_id, core_numb, status = project
            display_text = f"Project {project_id} - BHID: {bh_id} - Core#: {core_numb} - {status}"
            self.ProjectList.addItem(display_text)
    
    def open_selected_project(self):
        selected_item = self.ProjectList.currentItem()
        if selected_item is None:
            self.parent_app.update_status("ERROR: No project selected")
            return
        
        selected_text = selected_item.text()
        if 'Open' in selected_text:
            parts = selected_text.split()  
            project_id = int(parts[1])
            
            # Get project details from database
            self.parent_app.bk.db.c.execute("SELECT BH_ID, core_numb, depth_from, depth_to, box_numb FROM project_table WHERE project_ID = ?", (project_id,))
            project_data = self.parent_app.bk.db.c.fetchone()
            
            if project_data:
                bh_id, core_numb, depth_from, depth_to, box_numb = project_data
                
                #update parent app
                self.parent_app.bk.current_project_ID = project_id
                self.parent_app.update_project_display(depth_from, depth_to, core_numb, box_numb, bh_id, project_id)
                self.parent_app.check_add_boat_button_state()
                self.parent_app.update_status(f"Switched to project {project_id}")

                self.accept() 
            else:
                self.parent_app.update_status(f"ERROR: Could not load project {project_id} data")
        else:
            self.parent_app.update_status("WARNING: Can only switch to Open projects")
        
    def open_project_detail(self, item):
        selected_text = item.text()
        parts = selected_text.split()  
        project_id = int(parts[1])
        
        detail_dialog = ProjectDetailDialog(self.parent_app, project_id)
        detail_dialog.exec()
        
        
class ProjectDetailDialog(QDialog, Ui_ProjectDetailDialog):
    def __init__(self, parent_app, project_id):
        super().__init__()
        self.setupUi(self)
        self.parent_app = parent_app
        self.project_id = project_id
        self.closeButton.clicked.connect(self.close)
        self.load_project_data()
        
    def load_project_data(self):
        """Load all project data from database and display"""
        try:
            self.parent_app.bk.db.c.execute("""
                SELECT BH_ID, core_numb, depth_from, depth_to, box_numb, 
                       before_image_data, after_image_data,
                       add_boat_1, add_boat_2, add_boat_3, add_boat_4
                FROM project_table WHERE project_ID = ?
            """, (self.project_id,))
            
            project_data = self.parent_app.bk.db.c.fetchone()
            
            if project_data:
                bh_id, core_numb, depth_from, depth_to, box_numb, before_img, after_img, boat1, boat2, boat3, boat4 = project_data
                
                # Update project info
                self.projectTitleLabel.setText(f"Project {self.project_id}")

                boat_tags = self.parent_app.bk.db.get_boat_tags(self.project_id)
                box_tags = self.parent_app.bk.db.get_box_tags(self.project_id)
                
                boat_display = ", ".join(map(str, boat_tags)) if boat_tags else "None"
                box_display = ", ".join(map(str, box_tags)) if box_tags else "None"
                info_text = f"""BHID: {bh_id}
Core ID: {core_numb}
Box #: {box_numb}
Depth from (m): {depth_from}
Depth to (m): {depth_to}
Box tag: {box_display}
Boat tags: {boat_display}"""
                
                self.projectInfoText.setPlainText(info_text)
                self.load_before_after_images(before_img, after_img)
                self.load_boat_images([boat1, boat2, boat3, boat4])
                
            else:
                self.projectTitleLabel.setText("Project Not Found")
                
        except Exception as e:
            self.projectTitleLabel.setText("Error Loading Project")
            print(f"Error loading project data: {e}")

    def load_before_after_images(self, before_blob, after_blob):
        # load before image
        if before_blob:
            before_pixmap = self.blob_to_pixmap(before_blob)
            if before_pixmap:
                self.beforeImageLabel.setPixmap(before_pixmap)
            else:
                self.beforeImageLabel.setText("Error Loading Before Image")
        else:
            self.beforeImageLabel.setText("No Before Image")
        
        #Load after image
        if after_blob:
            after_pixmap = self.blob_to_pixmap(after_blob)
            if after_pixmap:
                self.afterImageLabel.setPixmap(after_pixmap)
            else:
                self.afterImageLabel.setText("Error Loading After Image")
        else:
            self.afterImageLabel.setText("No After Image")

    def load_boat_images(self, boat_blobs):
        """Load and display boat images"""
        boat_labels = [self.addBoat1Image, self.addBoat2Image, self.addBoat3Image, self.addBoat4Image]
        
        for i, blob in enumerate(boat_blobs):
            if blob:
                pixmap = self.blob_to_pixmap(blob)
                if pixmap:
                    boat_labels[i].setPixmap(pixmap)
                else:
                    boat_labels[i].setText("Error Loading Image")
            else:
                boat_labels[i].setText("No Image")

    def blob_to_pixmap(self, blob_data):
        """Convert BLOB data"""
        try:
            f = BytesIO(blob_data)
            loaded_data = np.load(f)
            numpy_array = loaded_data['frame']
            
            # convert Numpy array
            height, width, channel = numpy_array.shape
            bytes_per_line = 3 * width
            q_image = QImage(numpy_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap
            
        except Exception as e:
            print(f"Error converting BLOB to pixmap: {e}")
            return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())