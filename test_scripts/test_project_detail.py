import sys
from PyQt6.QtWidgets import QApplication, QDialog
from ProjectDetail_ui import Ui_ProjectDetailDialog

class TestProjectDetailDialog(QDialog, Ui_ProjectDetailDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.closeButton.clicked.connect(self.close)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = TestProjectDetailDialog()
    dialog.show()
    sys.exit(app.exec())
[10:29:38] Core Imaging System initialized
[10:29:38] Camera starting...
[10:29:40] Switching to Remote satellite
[10:29:40] Attempting to connect to satellite...
[10:29:40] Satellite connection successful - Remote mode active
[10:30:00] NEW BOX workflow initiated
[10:30:04] Creating project - BHID: , Core: 
[10:30:04] Project Error - Could not capture before image created successfully
