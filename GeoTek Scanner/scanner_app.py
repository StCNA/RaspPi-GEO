import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QLabel, QPushButton, QGroupBox, 
                             QFormLayout, QCheckBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from scanner_client import ScannerClient
from datetime import datetime

class ScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geotek Scanner - Project Monitor")
        self.setGeometry(100, 100, 500, 400)
        
        self.client = ScannerClient()
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Geotek Scanner - Project Monitor")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2E86AB; margin: 10px; padding: 10px;")
        layout.addWidget(title_label)
        
        # Connection Status
        self.status_label = QLabel("Connection: Checking...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet("padding: 5px; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Project Info Group
        project_group = QGroupBox("Current Project Information")
        project_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        project_layout = QFormLayout(project_group)
        
        # Project data labels
        self.project_id_label = QLabel("--")
        self.bhid_label = QLabel("--") 
        self.core_label = QLabel("--")
        self.box_label = QLabel("--")
        self.depth_label = QLabel("--")
        self.boat_tags_label = QLabel("--")
        self.box_tags_label = QLabel("--")
        self.updated_label = QLabel("--")
        
        # Set font for data labels
        data_font = QFont("Courier", 10)
        for label in [self.project_id_label, self.bhid_label, self.core_label, 
                     self.box_label, self.depth_label, self.boat_tags_label, 
                     self.box_tags_label, self.updated_label]:
            label.setFont(data_font)
            label.setStyleSheet("color: #white; padding: 2px;")
            
        
        # Add to form layout
        project_layout.addRow("Project ID:", self.project_id_label)
        project_layout.addRow("BHID:", self.bhid_label)
        project_layout.addRow("Core Number:", self.core_label)
        project_layout.addRow("Box Number:", self.box_label)
        project_layout.addRow("Depth Range:", self.depth_label)
        project_layout.addRow("Boat Tags:", self.boat_tags_label)
        project_layout.addRow("Box Tags:", self.box_tags_label)
        project_layout.addRow("Last Updated:", self.updated_label)
        
        layout.addWidget(project_group)
        
        # Controls
        controls_layout = QVBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Data Now")
        self.refresh_btn.setFont(QFont("Arial", 11))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1F5F7A;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        controls_layout.addWidget(self.refresh_btn)
        
        # Auto-refresh checkbox
        self.auto_refresh_cb = QCheckBox("Auto-refresh every 5 seconds")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.setFont(QFont("Arial", 10))
        self.auto_refresh_cb.stateChanged.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_cb)
        
        layout.addLayout(controls_layout)
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)  # Every 5 seconds
        
    def toggle_auto_refresh(self, state):
        if state == 2:  # Checked
            self.timer.start(5000)
        else:
            self.timer.stop()
            
    def refresh_data(self):
        # Step 1: Test connection
        if self.client.test_connection():
            self.status_label.setText("Connection: ● LIVE")
            self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
            
            # Step 2 & 3: Get project data
            project_data = self.client.get_project_data()
            if project_data:
                self.project_id_label.setText(str(project_data.get('project_id', '--')))
                self.bhid_label.setText(str(project_data.get('bh_id', '--')))
                self.core_label.setText(str(project_data.get('core_number', '--')))
                self.box_label.setText(str(project_data.get('box_number', '--')))
                self.depth_label.setText(f"{project_data.get('depth_from', '--')}m - {project_data.get('depth_to', '--')}m")
                
                # Format tags
                boat_tags = project_data.get('boat_tags', [])
                box_tags = project_data.get('box_tags', [])
                self.boat_tags_label.setText(', '.join(map(str, boat_tags)) if boat_tags else 'None')
                self.box_tags_label.setText(', '.join(map(str, box_tags)) if box_tags else 'None')
                
                self.updated_label.setText(datetime.now().strftime("%H:%M:%S"))
                
            else:
                # No active project
                for label in [self.project_id_label, self.bhid_label, self.core_label, 
                             self.box_label, self.depth_label, self.boat_tags_label, 
                             self.box_tags_label]:
                    label.setText("No active project")
                self.updated_label.setText(datetime.now().strftime("%H:%M:%S"))
                
        else:
            self.status_label.setText("Connection: ● OFFLINE")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            
            for label in [self.project_id_label, self.bhid_label, self.core_label, 
                         self.box_label, self.depth_label, self.boat_tags_label, 
                         self.box_tags_label]:
                label.setText("Connection Error")
            self.updated_label.setText("--")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScannerApp()
    window.show()
    sys.exit(app.exec())