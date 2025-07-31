# ProjectDetail_ui.py
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_ProjectDetailDialog(object):
    def setupUi(self, ProjectDetailDialog):
        ProjectDetailDialog.setObjectName("ProjectDetailDialog")
        ProjectDetailDialog.resize(831, 661)
        ProjectDetailDialog.setMinimumSize(QtCore.QSize(831, 661))
        ProjectDetailDialog.setMaximumSize(QtCore.QSize(831, 661))
        
        self.horizontalLayout = QtWidgets.QHBoxLayout(ProjectDetailDialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.leftWidget = QtWidgets.QWidget(ProjectDetailDialog)
        self.leftWidget.setMaximumSize(QtCore.QSize(400, 16777215))
        self.leftWidget.setObjectName("leftWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.leftWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.projectInfoFrame = QtWidgets.QFrame(self.leftWidget)
        self.projectInfoFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.projectInfoFrame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.projectInfoFrame.setObjectName("projectInfoFrame")
        self.projectInfoLayout = QtWidgets.QVBoxLayout(self.projectInfoFrame)
        self.projectInfoLayout.setObjectName("projectInfoLayout")
        
        self.projectTitleLabel = QtWidgets.QLabel(self.projectInfoFrame)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.projectTitleLabel.setFont(font)
        self.projectTitleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projectTitleLabel.setObjectName("projectTitleLabel")
        self.projectInfoLayout.addWidget(self.projectTitleLabel)
        
        self.projectInfoText = QtWidgets.QTextEdit(self.projectInfoFrame)
        self.projectInfoText.setMaximumSize(QtCore.QSize(16777215, 250))
        self.projectInfoText.setReadOnly(True)
        self.projectInfoText.setObjectName("projectInfoText")
        self.projectInfoLayout.addWidget(self.projectInfoText)
        
        self.verticalLayout.addWidget(self.projectInfoFrame)

        self.addedBoatsFrame = QtWidgets.QFrame(self.leftWidget)
        self.addedBoatsFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.addedBoatsFrame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.addedBoatsFrame.setObjectName("addedBoatsFrame")
        self.addedBoatsLayout = QtWidgets.QVBoxLayout(self.addedBoatsFrame)
        self.addedBoatsLayout.setObjectName("addedBoatsLayout")
        
        self.addedBoatsTitle = QtWidgets.QLabel(self.addedBoatsFrame)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.addedBoatsTitle.setFont(font)
        self.addedBoatsTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addedBoatsTitle.setObjectName("addedBoatsTitle")
        self.addedBoatsLayout.addWidget(self.addedBoatsTitle)
        
        self.boatImagesWidget = QtWidgets.QWidget(self.addedBoatsFrame)
        self.boatImagesWidget.setObjectName("boatImagesWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.boatImagesWidget)
        self.gridLayout.setObjectName("gridLayout")
        
        self.addBoat1Frame = QtWidgets.QFrame(self.boatImagesWidget)
        self.addBoat1Frame.setMinimumSize(QtCore.QSize(150, 100))
        self.addBoat1Frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.addBoat1Frame.setObjectName("addBoat1Frame")
        self.addBoat1Layout = QtWidgets.QVBoxLayout(self.addBoat1Frame)
        self.addBoat1Layout.setObjectName("addBoat1Layout")
        
        self.addBoat1Image = QtWidgets.QLabel(self.addBoat1Frame)
        self.addBoat1Image.setMinimumSize(QtCore.QSize(130, 80))
        self.addBoat1Image.setScaledContents(True)
        self.addBoat1Image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat1Image.setObjectName("addBoat1Image")
        self.addBoat1Layout.addWidget(self.addBoat1Image)
        
        self.addBoat1Label = QtWidgets.QLabel(self.addBoat1Frame)
        self.addBoat1Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat1Label.setObjectName("addBoat1Label")
        self.addBoat1Layout.addWidget(self.addBoat1Label)
        
        self.gridLayout.addWidget(self.addBoat1Frame, 0, 0, 1, 1)
        
        self.addBoat2Frame = QtWidgets.QFrame(self.boatImagesWidget)
        self.addBoat2Frame.setMinimumSize(QtCore.QSize(150, 100))
        self.addBoat2Frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.addBoat2Frame.setObjectName("addBoat2Frame")
        self.addBoat2Layout = QtWidgets.QVBoxLayout(self.addBoat2Frame)
        self.addBoat2Layout.setObjectName("addBoat2Layout")
        
        self.addBoat2Image = QtWidgets.QLabel(self.addBoat2Frame)
        self.addBoat2Image.setMinimumSize(QtCore.QSize(130, 80))
        self.addBoat2Image.setScaledContents(True)
        self.addBoat2Image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat2Image.setObjectName("addBoat2Image")
        self.addBoat2Layout.addWidget(self.addBoat2Image)
        
        self.addBoat2Label = QtWidgets.QLabel(self.addBoat2Frame)
        self.addBoat2Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat2Label.setObjectName("addBoat2Label")
        self.addBoat2Layout.addWidget(self.addBoat2Label)
        
        self.gridLayout.addWidget(self.addBoat2Frame, 0, 1, 1, 1)
        
        # Add Boat 3 Image
        self.addBoat3Frame = QtWidgets.QFrame(self.boatImagesWidget)
        self.addBoat3Frame.setMinimumSize(QtCore.QSize(150, 100))
        self.addBoat3Frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.addBoat3Frame.setObjectName("addBoat3Frame")
        self.addBoat3Layout = QtWidgets.QVBoxLayout(self.addBoat3Frame)
        self.addBoat3Layout.setObjectName("addBoat3Layout")
        
        self.addBoat3Image = QtWidgets.QLabel(self.addBoat3Frame)
        self.addBoat3Image.setMinimumSize(QtCore.QSize(130, 80))
        self.addBoat3Image.setScaledContents(True)
        self.addBoat3Image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat3Image.setObjectName("addBoat3Image")
        self.addBoat3Layout.addWidget(self.addBoat3Image)
        
        self.addBoat3Label = QtWidgets.QLabel(self.addBoat3Frame)
        self.addBoat3Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat3Label.setObjectName("addBoat3Label")
        self.addBoat3Layout.addWidget(self.addBoat3Label)
        
        self.gridLayout.addWidget(self.addBoat3Frame, 1, 0, 1, 1)
        
        # Add Boat 4 Image
        self.addBoat4Frame = QtWidgets.QFrame(self.boatImagesWidget)
        self.addBoat4Frame.setMinimumSize(QtCore.QSize(150, 100))
        self.addBoat4Frame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.addBoat4Frame.setObjectName("addBoat4Frame")
        self.addBoat4Layout = QtWidgets.QVBoxLayout(self.addBoat4Frame)
        self.addBoat4Layout.setObjectName("addBoat4Layout")
        
        self.addBoat4Image = QtWidgets.QLabel(self.addBoat4Frame)
        self.addBoat4Image.setMinimumSize(QtCore.QSize(130, 80))
        self.addBoat4Image.setScaledContents(True)
        self.addBoat4Image.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat4Image.setObjectName("addBoat4Image")
        self.addBoat4Layout.addWidget(self.addBoat4Image)
        
        self.addBoat4Label = QtWidgets.QLabel(self.addBoat4Frame)
        self.addBoat4Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.addBoat4Label.setObjectName("addBoat4Label")
        self.addBoat4Layout.addWidget(self.addBoat4Label)
        
        self.gridLayout.addWidget(self.addBoat4Frame, 1, 1, 1, 1)
        
        self.addedBoatsLayout.addWidget(self.boatImagesWidget)
        self.verticalLayout.addWidget(self.addedBoatsFrame)
        
        self.horizontalLayout.addWidget(self.leftWidget)
        
        # Right side widget for Before/After images
        self.rightWidget = QtWidgets.QWidget(ProjectDetailDialog)
        self.rightWidget.setObjectName("rightWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.rightWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        
        # Before Image Section
        self.beforeImageFrame = QtWidgets.QFrame(self.rightWidget)
        self.beforeImageFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.beforeImageFrame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.beforeImageFrame.setObjectName("beforeImageFrame")
        self.beforeImageLayout = QtWidgets.QVBoxLayout(self.beforeImageFrame)
        self.beforeImageLayout.setObjectName("beforeImageLayout")
        
        # Before Image Title
        self.beforeImageTitle = QtWidgets.QLabel(self.beforeImageFrame)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.beforeImageTitle.setFont(font)
        self.beforeImageTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.beforeImageTitle.setObjectName("beforeImageTitle")
        self.beforeImageLayout.addWidget(self.beforeImageTitle)
        
        # Before Image Display
        self.beforeImageLabel = QtWidgets.QLabel(self.beforeImageFrame)
        self.beforeImageLabel.setMinimumSize(QtCore.QSize(350, 250))
        self.beforeImageLabel.setScaledContents(True)
        self.beforeImageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.beforeImageLabel.setObjectName("beforeImageLabel")
        self.beforeImageLayout.addWidget(self.beforeImageLabel)
        
        self.verticalLayout_2.addWidget(self.beforeImageFrame)
        
        # After Image Section
        self.afterImageFrame = QtWidgets.QFrame(self.rightWidget)
        self.afterImageFrame.setMinimumSize(QtCore.QSize(0, 300))
        self.afterImageFrame.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.afterImageFrame.setObjectName("afterImageFrame")
        self.afterImageLayout = QtWidgets.QVBoxLayout(self.afterImageFrame)
        self.afterImageLayout.setObjectName("afterImageLayout")
        
        # After Image Title
        self.afterImageTitle = QtWidgets.QLabel(self.afterImageFrame)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.afterImageTitle.setFont(font)
        self.afterImageTitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.afterImageTitle.setObjectName("afterImageTitle")
        self.afterImageLayout.addWidget(self.afterImageTitle)
        
        # After Image Display
        self.afterImageLabel = QtWidgets.QLabel(self.afterImageFrame)
        self.afterImageLabel.setMinimumSize(QtCore.QSize(350, 250))
        self.afterImageLabel.setScaledContents(True)
        self.afterImageLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.afterImageLabel.setObjectName("afterImageLabel")
        self.afterImageLayout.addWidget(self.afterImageLabel)
        
        self.verticalLayout_2.addWidget(self.afterImageFrame)
        
        self.horizontalLayout.addWidget(self.rightWidget)
        
        # Close button
        self.closeButton = QtWidgets.QPushButton(ProjectDetailDialog)
        self.closeButton.setMinimumSize(QtCore.QSize(100, 30))
        self.closeButton.setObjectName("closeButton")
        
        # Add close button to bottom
        self.bottomLayout = QtWidgets.QHBoxLayout()
        self.bottomLayout.addStretch()
        self.bottomLayout.addWidget(self.closeButton)
        self.bottomLayout.addStretch()
        
        # Main layout with close button at bottom
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addLayout(self.horizontalLayout)
        self.mainLayout.addLayout(self.bottomLayout)
        
        ProjectDetailDialog.setLayout(self.mainLayout)

        self.retranslateUi(ProjectDetailDialog)
        QtCore.QMetaObject.connectSlotsByName(ProjectDetailDialog)

    def retranslateUi(self, ProjectDetailDialog):
        _translate = QtCore.QCoreApplication.translate
        ProjectDetailDialog.setWindowTitle(_translate("ProjectDetailDialog", "Project Details"))
        self.projectTitleLabel.setText(_translate("ProjectDetailDialog", "Project #"))
        self.projectInfoText.setHtml(_translate("ProjectDetailDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">BHID:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Core ID:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Box #:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Depth from (m):</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Depth to (m):</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Box tag:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt;\">Boat tags:</span></p></body></html>"))
        self.addedBoatsTitle.setText(_translate("ProjectDetailDialog", "Added Boats"))
        self.addBoat1Image.setText(_translate("ProjectDetailDialog", "No Image"))
        self.addBoat1Label.setText(_translate("ProjectDetailDialog", "Add_boat_1"))
        self.addBoat2Image.setText(_translate("ProjectDetailDialog", "No Image"))
        self.addBoat2Label.setText(_translate("ProjectDetailDialog", "Add_boat_2"))
        self.addBoat3Image.setText(_translate("ProjectDetailDialog", "No Image"))
        self.addBoat3Label.setText(_translate("ProjectDetailDialog", "Add_boat_3"))
        self.addBoat4Image.setText(_translate("ProjectDetailDialog", "No Image"))
        self.addBoat4Label.setText(_translate("ProjectDetailDialog", "Add_boat_4"))
        self.beforeImageTitle.setText(_translate("ProjectDetailDialog", "Before Image"))
        self.beforeImageLabel.setText(_translate("ProjectDetailDialog", "No Image Available"))
        self.afterImageTitle.setText(_translate("ProjectDetailDialog", "After Image"))
        self.afterImageLabel.setText(_translate("ProjectDetailDialog", "No Image Available"))
        self.closeButton.setText(_translate("ProjectDetailDialog", "Close"))
