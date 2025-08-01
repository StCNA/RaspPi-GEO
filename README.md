Core Imaging System V4 - User Manual
Overview
This system is designed for geotechnical core imaging with dual Raspberry Pi setup, supporting both local and satellite camera operations, plus integration with Geotek Scanner PC.
System Components

Main Pi: Primary imaging system with database and UI
Satellite Pi: Remote camera for extended reach
Geotek Scanner PC: Displays current project information


Main Interface Controls
Camera Source Selection

Local: Uses camera attached to main Raspberry Pi
Remote: Switches to satellite Raspberry Pi camera
Camera Preview: Live feed from selected camera source

Project Workflow Buttons
NEW BOX

Purpose: Start a new core imaging project
Process:

Opens dialog to enter project details (BHID, Core#, Box#, Depth range)
Captures "before" image automatically
Detects and records ArUco tags in view
Creates new project in database

Result: Project becomes active and displays in project info panel and data is uploaded and storedon database 


ADD BOAT

Purpose: Add boat tags to current project (max 4 boats)
Process:

Captures image when button pressed
Detects boat ArUco tags (ID series 4)
Associates detected boats with current project

Limitation: Button disables after 4 boats added


CHECK PAIR

Purpose: Verify that visible tags belong to current project
Process:

Analyzes current camera view
Checks if detected boat and box tags match project database
Displays success/failure message


Use Case: Quality control before releasing boats


RELEASE BOAT

Purpose: Release individual boats from current project
Process:

Detects boat tags currently in camera view
Removes those specific boats from project
Updates database to show boats as available


Note: Only releases boats visible in camera


RETURN BOX

Purpose: Complete current project
Process:

Captures "after" image
Verifies all project tags are still present
Marks project as completed in database
Clears current project display


Result: Project is finalized and archived

Navigation & History
Project History

Purpose: View and switch between previous projects
Features:

Lists recent projects with status (Open/Completed)
Double-click any project to view detailed information
Switch to open projects to continue work


Project Details: Shows before/after images, boat images, and all project metadata

EXIT

Purpose: Safely close the application
Process: Confirms exit choice and shuts down system


Project Information Panel
Current Project Display
Shows active project details:

Project ID: Unique database identifier
BHID: Borehole identification
Core ID: Core number being processed
Box #: Box number for this core section
Depth Range: From/to measurements in meters
Box Tags: ArUco box tags detected (ID series 5)
Boat Tags: ArUco boat tags assigned (ID series 4)

Status Console

Real-time updates: Shows system status and workflow progress
Error messages: Displays warnings and error conditions
Timestamps: All messages include time stamps
Auto-scroll: Automatically shows latest messages


ArUco Tag System
Tag Types

Boat Tags: ID series 4 (0-49.)
Box Tags: ID series 5 (0-49)

Tag Detection

Automatic: Tags detected during NEW BOX and ADD BOAT workflows
Verification: CHECK PAIR validates tag associations
Release: RELEASE BOAT removes specific boats from project


Dual Pi Operation
Local Mode

Uses camera directly connected to main Raspberry Pi
Faster response time
Standard operation mode

Remote Mode

Connects to satellite Raspberry Pi camera over network
Allows extended camera placement
Slower preview refresh rate (2-second intervals)
All workflows function identically to local mode

Switching Modes

Select Remote radio button to connect to satellite
Status console shows connection success/failure
Camera preview switches to satellite feed
Select Local to return to main Pi camera


Geotek Scanner Integration
Scanner PC Display
The Geotek Scanner PC shows real-time project information:

Connection Status: Live/Offline indicator
Current Project Data: Mirrors main system project info
Auto-refresh: Updates every 5 seconds
Manual Refresh: Button for immediate update


Database & Storage
Automatic Saving

Images: Before/after images stored as compressed arrays
Metadata: All project details saved to SQLite database
Tags: ArUco tag associations tracked with timestamps
History: Complete audit trail of all operations

Data Location

Database: /media/jeeves003/EMPTY DRIVE/raspi.db
Backup: Regular database backups recommended
Export: Project data can be exported for analysis

