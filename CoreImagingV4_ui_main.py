from CoreImagingV4_ui import Ui_MainWindow
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QMessageBox, QDialog, QVBoxLayout,
    QLabel, QLineEdit, QPushButton,QToolButton, QInputDialog
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
import cv2
import pickle

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bk = bk
        self.is_remote_mode = False
        self.satellite_client = None
        self.calibration_mode = False
        self.calibration_data = []
        self.calibration_point = 1
        self.total_calibration_points = 5
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
        self.update_status("Core Imaging System initialized - Camera starting...")
        self.update_status(f"Pixel Density = {self.bk.ar.slope:.4f} px/mm, Intercept = {self.bk.ar.intercept:.4f} px")

        
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
        self.pushButton_7.clicked.connect(self.core_start_clicked)
        self.pushButton_8.clicked.connect(self.core_end_clicked) 
        self.pushButton_9.clicked.connect(self.meas_point_clicked)
        self.pushButton_10.clicked.connect(self.avoid_start_clicked)
        self.pushButton_11.clicked.connect(self.avoid_end_clicked)
        self.pushButton_12.clicked.connect(self.reset_measurements_clicked)
        self.Remote.clicked.connect(self.remote_clicked)
        self.local.clicked.connect(self.local_clicked)
        self.actionExit.triggered.connect(self.exit_clicked)
        self.actionProject_History.triggered.connect(self.open_project_history)
        self.actionRecalibrate.triggered.connect(self.recalibrate_clicked)
        self.actionDisplay_pixel_density.triggered.connect(self.display_current_pixeldensity)
        
        
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
            
            if result == "TAG_IN_USE":
                self.update_status("ERROR: Tag(s) already in use")
                QMessageBox.warning(self, 'Tag In Use', 
                                'One or more Tags in project already in use.\n\n'
                                'Please use new tags or complete open projects.')
                self.update_status("WARNING: Tag already in use")
                return
            
            elif result == 'TAG_OVERLIMIT':
                self.update_status("WARNING: Multiple boat or box tags detected")
                QMessageBox.warning(self, 'Multiple boat or box tags detected', 
                                    'Multiple Tags detected\n\n'
                                    '1 Box and 1 Boat per project!')
                return
            
            elif result == 'RECTIFICATION_FAILED':
                self.update_status("ERROR: Position tags not visible - cannot rectify image")
                QMessageBox.warning(self, 'Rectification Failed', 
                                'Position tags (0,1,2,3) not detected.\n\n'
                                'Please adjust the core to show all 4 corner tags.')
                return
            
            elif result == "NO_TAGS_DETECTED":
                self.update_status("WARNING: No boat or box tags detected")
                
                reply = QMessageBox.question(
                    self,
                    "No Tags Detected",
                    "No boat or box tags were detected in the image.\n\n"
                    "Continue with project creation?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    # Delete the project that was already created
                    project_id = self.bk.current_project_ID
                    if project_id:
                        self.bk.db.delete_from_proj_tbl(project_id)
                        self.bk.current_project_ID = None
                    self.update_status("Project creation cancelled - no tags")
                    return
                else:
                    # Continue with project even without tags
                    project_id = self.bk.current_project_ID
                    self.update_project_display(depth_from, depth_to, core_number, box_number, bh_id, project_id)
                    self.update_status(f"Project {project_id} created successfully (no tags)")
            
            elif result:  
                project_id = int(result)
                self.bk.current_project_ID = int(result)
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
        if isinstance(project_ID, tuple):
            project_ID = project_ID[0]
        project_ID = int(project_ID)
        
        boat_tags = self.bk.db.get_boat_tags(project_ID)
        box_tags = self.bk.db.get_box_tags(project_ID)
        boat_display = ", ".join(map(str, boat_tags)) if boat_tags else "None"
        box_display = ", ".join(map(str, box_tags)) if box_tags else "None"
        
        # Get measurements
        measurements = self.bk.db.get_project_measurements(project_ID)
        core_start = None
        core_end = None
        meas_points = []
        avoid_starts = []
        avoid_ends = []
        
        for meas_type, position_mm, boat_tag in measurements:
            if meas_type == 'core_start':
                core_start = (position_mm, boat_tag)
            elif meas_type == 'core_end':
                core_end = (position_mm, boat_tag)
            elif meas_type == 'meas_point':
                meas_points.append((position_mm, boat_tag))
            elif meas_type == 'avoid_start':
                avoid_starts.append(position_mm)
            elif meas_type == 'avoid_end':
                avoid_ends.append(position_mm)
        
        # Build display text
        display_text = f"""<center><b>Current Project: {project_ID}</b></center><br>
    BHID: {bh_id}<br>
    Core #: {core_number}<br>
    Box #: {box_number}<br>
    Depth from (m): {depth_from}<br>
    Depth to (m): {depth_to}<br>
    Box: {box_display}<br>
    Boat(s): {boat_display}<br>
    <br>
    <b>═══ MEASUREMENTS ═══</b><br>"""
        
        # Core boundaries
        if core_start:
            display_text += f"Core Start: {core_start[0]}mm (boat {core_start[1]})<br>"
        else:
            display_text += "Core Start: <i>Not set</i><br>"
        
        if core_end:
            display_text += f"Core End: {core_end[0]}mm (boat {core_end[1]})<br>"
        else:
            display_text += "Core End: <i>Not set</i><br>"
        
        # Core length calculation
        if core_start and core_end:
            length = core_end[0] - core_start[0]
            display_text += f"<b>Core Length: {length}mm ({length/1000:.3f}m)</b><br>"
        
        display_text += "<br>"
        
        # Measurement points
        if meas_points:
            display_text += f"<b>Measurement Points ({len(meas_points)}):</b><br>"
            for pos, boat in meas_points:
                display_text += f"  • {pos}mm (boat {boat})<br>"
            display_text += "<br>"
        
        # Avoid zones
        if avoid_starts and avoid_ends:
            zones = list(zip(avoid_starts, avoid_ends))
            display_text += f"<b>Avoid Zones ({len(zones)}):</b><br>"
            for i, (start, end) in enumerate(zones, 1):
                zone_length = end - start
                display_text += f"  • Zone {i}: {start}-{end}mm ({zone_length}mm)<br>"
        elif avoid_starts or avoid_ends:
            display_text += "<b>Avoid Zones:</b> <i>Incomplete (missing start or end)</i><br>"
        
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
        
        if result and "TAG_IN_USE" in result:
            tag_info = result.split("_")
            tag_number = tag_info[3]
            self.update_status(f"WARNING: boat tag {tag_number} already in use by another project")
            return
        if result and "SUCCESS" in result:
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
        
        if success == True:
            # Update ArUco detector for satellite mode
            self.bk.ar.is_remote_mode = True
            self.bk.ar.slider_tag = 11
            self.bk.ar.reference_tag = 7
            self.bk.ar.required_corner_tags = [5, 6, 7, 8]
            self.bk.ar.slope, self.bk.ar.intercept = self.bk.ar.load_calibration()
            
            self.update_status("SUCCESS: Connected to satellite camera!")
            self.update_status("Remote mode active - using tags 5-8, slider tag 9")
        elif success == "REMOTE_CONNECTION_FAILED":
            self.update_status("ERROR: Remote satellite camera not connected")
            self.local.setChecked(True)  
        else:
            self.update_status("ERROR: Failed to connect to satellite camera")
            self.local.setChecked(True)
            
    def local_clicked(self):
        self.update_status("Switching to local camera...")
        
        success = self.bk.set_remote_mode(False)
        
        if success:
            # Update ArUco detector for main mode
            self.bk.ar.is_remote_mode = False
            self.bk.ar.slider_tag = 4
            self.bk.ar.reference_tag = 2
            self.bk.ar.required_corner_tags = [0, 1, 2, 3]
            self.bk.ar.slope, self.bk.ar.intercept = self.bk.ar.load_calibration()
            
            self.update_status("SUCCESS: Switched to local camera")
            self.update_status("Using tags 0-3, slider tag 4")
        else:
            self.update_status("ERROR: Failed to switch to local camera")
            
    def core_start_clicked(self):
        self.update_status("CORE START measurement initiated")
        result = self.bk.capture_measurement("core_start")
        
        if result.startswith("ALREADY_EXISTS"):
            parts = result.split("|")
            existing_pos = parts[2]
            existing_boat = parts[3]
            new_pos = parts[4]
            new_boat = parts[5]
            
            reply = QMessageBox.question(
                self,
                "Core Start Already Exists",
                f"Core Start already captured:\n"
                f"  Existing: {existing_pos}mm (boat {existing_boat})\n"
                f"  New: {new_pos}mm (boat {new_boat})\n\n"
                f"Overwrite existing measurement?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                result = self.bk.overwrite_measurement("core_start", int(new_pos), int(new_boat))
                self.update_status(result)
                self.refresh_current_project_display() 
            else:
                self.update_status("Core Start measurement cancelled")
        else:
            self.update_status(result)
            if "SUCCESS" in result:
                self.refresh_current_project_display() 

    def core_end_clicked(self):
        self.update_status("CORE END measurement initiated")
        result = self.bk.capture_measurement("core_end")
        
        # Check if measurement already exists
        if result.startswith("ALREADY_EXISTS"):
            parts = result.split("|")
            existing_pos = parts[2]
            existing_boat = parts[3]
            new_pos = parts[4]
            new_boat = parts[5]
            
            reply = QMessageBox.question(
                self,
                "Core End Already Exists",
                f"Core End already captured:\n"
                f"  Existing: {existing_pos}mm (boat {existing_boat})\n"
                f"  New: {new_pos}mm (boat {new_boat})\n\n"
                f"Overwrite existing measurement?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                result = self.bk.overwrite_measurement("core_end", int(new_pos), int(new_boat))
                self.update_status(result)
                self.refresh_current_project_display() 
            else:
                self.update_status("Core End measurement cancelled")
        else:
            self.update_status(result)
            if "SUCCESS" in result:
                self.refresh_current_project_display() 
                
            
            
            self.update_status(result)

    def meas_point_clicked(self):
        self.update_status("MEASUREMENT POINT captured")
        result = self.bk.capture_measurement("meas_point")
        self.update_status(result)
        if "SUCCESS" in result:
                self.refresh_current_project_display() 

    def avoid_start_clicked(self):
        self.update_status("AVOID START marked")
        result = self.bk.capture_measurement("avoid_start")
        self.update_status(result)
        if "SUCCESS" in result:
                self.refresh_current_project_display() 

    def avoid_end_clicked(self):
        self.update_status("AVOID END marked")
        result = self.bk.capture_measurement("avoid_end")
        self.update_status(result)
        if "SUCCESS" in result:
                self.refresh_current_project_display() 
    
    def reset_measurements_clicked(self):
        self.update_status("Reset Initiated...")
        if not self.bk.current_project_ID:
            self.update_status("ERROR: No active project")
            QMessageBox.warning(self, "No Project" , "No active project")
            return 
        
        measurements = self.bk.db.get_project_measurements(self.bk.current_project_ID)
        count = len(measurements)
        
        if count == 0:
            self.update_status("Measurments are already empty.. :(")
            QMessageBox.information(self, "No Measurements", "No measurements to clear for this project")
            return
        
        reply = QMessageBox.question(
            self,
            "Reset Measurements",
            f"Delete all {count} measurement(s) for this project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            result = self.bk.reset_measurements()
            self.update_status(result)
            
            if "SUCCESS" in result:
                QMessageBox.information(self, "Measurements Reset", result)
                self.refresh_current_project_display()
            else:
                self.update_status("Reset cancelled")
        

    def recalibrate_clicked(self):
        self.update_status("Recalibration Started")
        self.calibration_mode = True
        self.calibration_data = []
        self.calibration_point = 1
        
        # Prompt for first point
        self.prompt_calibration_point()
        
    def prompt_calibration_point(self):
        self.update_status("Place slider in position")
        # Simple message box to pause workflow
        reply = QMessageBox.question(
            self, 
            f'Calibration Point {self.calibration_point}',
            f'Position slider at mark #{self.calibration_point}\n\n'
            f'Ready to capture?',
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            self.cancel_calibration()
            return
        
        # If OK clicked, move to capture
        self.update_status("OK clicked - ready to capture")
        self.capture_calibration_point()
    
    def capture_calibration_point(self):
        self.update_status("Capturing image...")
        frame = self.bk.capture_image()
        if frame is None:
            self.update_status("ERROR: Could not capture calibration image")
            QMessageBox.critical(self, "Capture Failed", "Could not capture calibration image")
            self.cancel_calibration()
            return
        
        # get raw pixels (not converted to mm)
        detected_pixels = self.bk.ar.get_slider_position(frame, return_pixels=True)
        
        if detected_pixels is None:
            self.update_status("ERROR: Could not detect slider position")
            QMessageBox.warning(self, "Detection Failed", 
                            "Could not detect slider (Tag 4) or reference (Tag 2).\n"
                            "Retrying this point...")
            self.prompt_calibration_point()
            return
        
        self.update_status(f"Detected {detected_pixels} pixels from Tag 2")
        self.get_measured_distance(detected_pixels)
    
    def get_measured_distance(self, detected_pixels):
        # Simple input dialog
        measured_mm, ok = QInputDialog.getDouble(
            self,
            f"Calibration Point {self.calibration_point}",
            f"Detected: {detected_pixels} pixels\n\n"
            f"Enter measured distance from Tag 2 (mm):",
            value=0.0,
            min=0.0,
            max=5000.0,
            decimals=1
        )
        
        if not ok:
            self.update_status("Measurement cancelled - retrying point")
            self.prompt_calibration_point()  
            return
        
        if measured_mm <= 0:
            self.update_status("ERROR: Distance must be greater than 0")
            QMessageBox.warning(self, "Invalid Input", "Distance must be greater than 0")
            self.get_measured_distance(detected_pixels)  # Ask again
            return
        
        # calculate pixel density for the point / Update to store two points and not pixel density
        self.update_status(f"Measured: {measured_mm}mm at {detected_pixels} pixels")
        print(f"Point {self.calibration_point} - {measured_mm}mm = {detected_pixels}px")
        if detected_pixels < 0 or measured_mm <= 0:
            self.update_status("ERROR: Invalid measurement values")
            QMessageBox.warning(self, "Invalid Data", "Invalid pixel or mm values detected")
            self.get_measured_distance(detected_pixels)
            return
        
        # store for later printing
        self.calibration_data.append({
            'point': self.calibration_point,
            'measured_mm': measured_mm,
            'detected_pixels': detected_pixels,
        })        
        self.update_status(f"Point {self.calibration_point} captured succesfully")
        self.calibration_point += 1
        if self.calibration_point <= self.total_calibration_points:
            self.prompt_calibration_point() 
        else:
            self.finish_calibration()
         
         
    def cancel_calibration(self):
        self.calibration_mode = False
        self.update_status("Calibration cancelled")
        QMessageBox.information(self, "Calibration Cancelled", 
                            "Calibration process was cancelled.")
        
    def finish_calibration(self):
        import math
        from datetime import datetime
        
        self.calibration_mode = False
        
        # Extract mm and pixel values from calibration data
        mm_values = [point['measured_mm'] for point in self.calibration_data]
        pixel_values = [point['detected_pixels'] for point in self.calibration_data]
        coefficients = np.polyfit(mm_values, pixel_values, 1)
        slope = coefficients[0]
        intercept = coefficients[1]
        
        correlation_matrix = np.corrcoef(mm_values, pixel_values)
        r_squared = correlation_matrix[0, 1] ** 2
        self.update_status("\nCalibration Points:")
        for point in self.calibration_data:
            self.update_status(f"  {point['measured_mm']}mm → {point['detected_pixels']}px")
                
        # print to external terminal (debugging)
        self.update_status("CALIBRATION RESULTS")
        self.update_status(f"Slope: {slope:.4f} px/mm")
        self.update_status(f"Intercept: {intercept:.4f} px")
        
        # confiirmation
        msg = QMessageBox()
        msg.setWindowTitle("Save Calibration?")
        msg.setText(
            f"Linear Fit Calibration:\n\n"
            f"Slope: {slope:.4f} px/mm\n"
            f"Intercept: {intercept:.4f} px\n"
            f"Save this calibration?"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | 
                            QMessageBox.StandardButton.Discard)
        
        result = msg.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            # Prepare calibration data
            calibration_data = {
                'slope': slope,
                'intercept': intercept,
                'calibration_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'calibration_points': self.calibration_data,
            }
            
            # Save to pickle file
            if self.bk.is_remote_mode:
                calibration_file = "/media/jeeves003/EMPTY DRIVE/calibration_satellite.pkl"
                mode_text = "SATELLITE"
            else:
                calibration_file = "/media/jeeves003/EMPTY DRIVE/calibration.pkl"
                mode_text = "MAIN"

            
            try:
                with open(calibration_file, 'wb') as f:
                    pickle.dump(calibration_data, f)
                
                # Update system
                self.bk.ar.slope = slope
                self.bk.ar.intercept = intercept
                
                QMessageBox.information(self, "Calibration Complete",
                                    f"Calibration saved successfully!\n\n"
                                    f"Slope: {slope:.4f} px/mm\n"
                                    f"Intercept: {intercept:.4f} px")
            except Exception as e:
                self.update_status(f"ERROR: Could not save calibration: {e}")
                QMessageBox.critical(self, "Save Failed", f"Could not save calibration:\n{e}")
        else:
            self.update_status("Calibration discarded")
            QMessageBox.information(self, "Calibration Discarded", 
                                "Calibration was not saved.")
            
    
    
    def display_current_pixeldensity(self):
        self.update_status(f"The Current Pixel Density slope is {self.bk.ar.slope:.4f} px/mm") 
            

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
        try:
            self.parent_app.bk.db.c.execute("""
                SELECT BH_ID, core_numb, depth_from, depth_to, box_numb, 
                    before_image_data, after_image_data,
                    add_boat_1, add_boat_2, add_boat_3, add_boat_4
                FROM project_table WHERE project_ID = ?
            """, (self.project_id,))
            
            project_data = self.parent_app.bk.db.c.fetchone()
            
            if project_data:
                bh_id, core_numb, depth_from, depth_to, box_numb, before_path, after_path, boat1_path, boat2_path, boat3_path, boat4_path = project_data
                
                # Update project info
                self.projectTitleLabel.setText(f"Project {self.project_id}")

                boat_tags = self.parent_app.bk.db.get_boat_tags(self.project_id)
                box_tags = self.parent_app.bk.db.get_box_tags(self.project_id)
                
                boat_display = ", ".join(map(str, boat_tags)) if boat_tags else "None"
                box_display = ", ".join(map(str, box_tags)) if box_tags else "None"
                
                # Get measurements
                measurements = self.parent_app.bk.db.get_project_measurements(self.project_id)
                
                # Find core start and core end
                core_start = None
                core_end = None
                
                for meas_type, position_mm, boat_tag in measurements:
                    if meas_type == 'core_start':
                        core_start = (position_mm, boat_tag)
                    elif meas_type == 'core_end':
                        core_end = (position_mm, boat_tag)
                
                # Build info text
                info_text = f"""BHID: {bh_id}
    Core #: {core_numb}
    Box #: {box_numb}
    Depth from (m): {depth_from}
    Depth to (m): {depth_to}
    Box tag: {box_display}
    Boat tags: {boat_display}"""
                
                # Add measurements if they exist
                if core_start or core_end:
                    info_text += "\n\n--- MEASUREMENTS ---"
                    
                    if core_start:
                        info_text += f"\nCore Start: {core_start[0]}mm (boat {core_start[1]})"
                    
                    if core_end:
                        info_text += f"\nCore End: {core_end[0]}mm (boat {core_end[1]})"
                    
                    # Calculate and display core length
                    if core_start and core_end:
                        length_mm = core_end[0] - core_start[0]
                        length_m = length_mm / 1000
                        info_text += f"\nCore Length: {length_mm}mm ({length_m:.3f}m)"
                
                self.projectInfoText.setPlainText(info_text)
                self.load_before_after_images(before_path, after_path)
                self.load_boat_images([boat1_path, boat2_path, boat3_path, boat4_path])
                
            else:
                self.projectTitleLabel.setText("Project Not Found")
                
        except Exception as e:
            self.projectTitleLabel.setText("Error Loading Project")
            print(f"Error loading project data: {e}")

    def load_before_after_images(self, before_path, after_path):
        # Load before image
        if before_path:
            before_pixmap = self.filepath_to_pixmap(before_path)
            if before_pixmap:
                self.beforeImageLabel.setPixmap(before_pixmap)
            else:
                self.beforeImageLabel.setText("Error Loading Before Image")
        else:
            self.beforeImageLabel.setText("No Before Image")
        
        # Load after image
        if after_path:
            after_pixmap = self.filepath_to_pixmap(after_path)
            if after_pixmap:
                self.afterImageLabel.setPixmap(after_pixmap)
            else:
                self.afterImageLabel.setText("Error Loading After Image")
        else:
            self.afterImageLabel.setText("No After Image")

    def load_boat_images(self, boat_paths):
        boat_labels = [self.addBoat1Image, self.addBoat2Image, self.addBoat3Image, self.addBoat4Image]
        
        for i, path in enumerate(boat_paths):
            if path:
                pixmap = self.filepath_to_pixmap(path)
                if pixmap:
                    boat_labels[i].setPixmap(pixmap)
                else:
                    boat_labels[i].setText("Error Loading Image")
            else:
                boat_labels[i].setText("No Image")

    def filepath_to_pixmap(self, file_path):
        try:
            # Load image directly with cv2
            image = cv2.imread(file_path)
            if image is None:
                print(f"Could not load image from {file_path}")
                return None
                
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Convert to QPixmap
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap
            
        except Exception as e:
            print(f"Error loading image from {file_path}: {e}")
            return None
        
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())