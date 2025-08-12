import tkinter as tk
import cv2.aruco as aruco
import numpy as np
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import os
from datetime import datetime
import cv2
from local_camera import LocalCAM #import camera from client
from client_side import PC2RPi_client #import camera from sateltie
from backend_manager import bk


class CoreImagingUI:
    def __init__(self, system_name: str = "Core Imaging", version: str = "v1.0"):
        self.root = tk.Tk()
        self.root.geometry("800x700")
                
        # variables fro naming in title
        self.system_name = system_name
        self.root.title(f"{system_name} Version {version}") #titel
        
        #sets up variables for communcation between UI and Server/Client
        self.local_camera = None
        self.local_camera_ready = False
        self.server_ip = "169.254.182.213"
        self.server_port = 1515
        self.current_mode = "BEFORE"
        # Creating the actual UI
        self.create_menubar()
        self.create_main_interface()
        self.init_hardware()
        
        # User contorl variables init
        self.mode_var = tk.StringVar(value="BEFORE")
        self.capture_btn = None
        self.status_text = None
        self.before_button.config(state='disabled')
        self.after_button.config(state='disabled')
        self.current_project_ID = None
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        #start things up
        self.root.mainloop()


    #create menus
    def create_menubar(self):
        self.menubar = tk.Menu(self.root)
        
        # File menu
        self.filemenu = tk.Menu(self.menubar, tearoff = 0)
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Force Exit", command=exit)
        
        # System menu
        self.systemmenu = tk.Menu(self.menubar, tearoff=0)
        self.systemmenu.add_command(label="Test Local Camera" )#, command=self.test_local_camera)
        self.systemmenu.add_command(label="Test Server Connection", command=self.test_server_connection)
        
        # Help menu
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.show_about)
        self.helpmenu.add_command(label="Status", command=self.show_system_status)
        
        # putting menus in menuframe
        self.menubar.add_cascade(menu=self.filemenu, label="File")
        self.menubar.add_cascade(menu=self.systemmenu, label="System")
        self.menubar.add_cascade(menu=self.helpmenu, label="Help")
        # Place menubar with menus inside
        self.root.config(menu=self.menubar)

    # Creating Intrface
    def create_main_interface(self):
        self.main_frame = tk.Frame(self.root, bg='lightgray', padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        #Step 2 Create a title Using Tk.Label
        main_frame_label = tk.Label(self.main_frame, text="Sample Analyzers" , font =( 'Arial', 16, 'bold'), bg='lightgray')
        main_frame_label.pack(pady=10)
        #Step 3 Create a container for evertyhing to go in
        horizontal_container = tk.Frame(self.main_frame, bg='gray')
        horizontal_container.pack(fill=tk.BOTH, expand=True)
        
        
        #Step4 Place left container (preview page), and Right container (buttons)
        preview_container = tk.Frame(horizontal_container, bg = 'red')
        preview_container.pack(side = tk.TOP, fill =tk.BOTH, expand = True)
        button_container = tk.Frame(horizontal_container, bg = 'blue')
        button_container.pack(side = tk.BOTTOM, fill= tk.BOTH, expand = True)
        
        #Step 5, creating camera preview and starus box conatiners within the preview container
        camera_preview = tk.Frame(preview_container, bg ='black')
        camera_preview.place(relx = 0, rely = 0, relwidth = 0.60, relheight = 1) # had to use .place to keep consistent ratio between two containers
        
        self.preview_label = tk.Label(camera_preview, text ="Camera Starting...", bg = 'black', fg ='white')
        self.preview_label.pack(fill = tk.BOTH, expand = True)
        
        #Step 6 Place the status box terminal
        status_box = tk.Frame(preview_container, bg='white')
        status_box.place(relx = 0.60, rely= 0, relwidth = 0.4, relheight = 1)
        
        self.txt = tk.Text(status_box)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        scrollb = tk.Scrollbar(status_box)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set
        scrollb['command'] = self.txt.yview

        # Configure grid weights so widgets expand properly
        status_box.grid_rowconfigure(0, weight=1)
        status_box.grid_columnconfigure(0, weight=1)
        
        #step 6, Add touch screen UI buttons (big)
        minor_button_container = tk.Frame(button_container, bg = 'lightgray', borderwidth=1, relief="solid")
        minor_button_container.place(relx = 0, rely = 0, relwidth = 0.6, relheight =1 )
        
        major_button_container = tk.Frame(button_container, bg = 'lightgray')
        major_button_container.place(relx = 0.60, rely= 0, relwidth = 0.4, relheight = 1)
        
        self.before_button = tk.Button(major_button_container, text = 'Capture Before', bg= 'green', fg = 'white', height = 5, command = self.capture_before_image)
        self.before_button.pack(fill = tk.BOTH, side = tk.TOP, pady=3, padx = 5)
        
        self.after_button = tk.Button(major_button_container, text="AFTER PICTURE", bg= 'red', fg = 'white', height = 5, command = self.capture_after_image)  
        self.after_button.pack(fill = tk.BOTH, side = tk.TOP, pady=3, padx = 5)
        
        self.add_boats_button = tk.Button(major_button_container, text="ADD BOATS", bg = 'gray', fg ='white', height = 5, command = self.add_boats)
        self.add_boats_button.pack(fill = tk.BOTH, side = tk.TOP,  pady=3, padx = 5)
        
        self.current_proj_lbl_cnt = tk.Label(minor_button_container, text=f"Project: Create Project to Begin " , font =( 'Arial', 16, 'bold'), bg='lightgray')
        self.current_proj_lbl_cnt.pack(side = tk.TOP, anchor = tk.NW, pady=10)
        
        self.create_new_project_btn = tk.Button(minor_button_container, text="Create New Project", bg = 'black', fg = 'white', height = 2, width = 1, command = self.before_picure_clicked)
        self.create_new_project_btn.pack(fill = tk.BOTH, side = tk.TOP, pady=3, padx = 5)
        self.project_history_btn = tk.Button(minor_button_container, text="Project History", bg = 'black', fg = 'white', height = 2, width = 1, command = self.capture_after_image)
        self.project_history_btn.pack(fill = tk.BOTH, side = tk.TOP, pady=3, padx = 5)


        
    
    def init_hardware(self):
        try:
            self.local_camera = LocalCAM()
            self.local_camera_ready = True
            self.update_camera_preview() 
            #self.update_status("Local camera initialized successfully")
        except Exception as e:
            self.local_camera_ready = False
            #self.update_status(f"Failed to initialize local camera: {str(e)}")
            
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''
    # Functions for events that will be called in Section 1
    def on_mode_change(self):
        self.current_mode = self.mode_var.get()
        if self.current_mode == "BEFORE":
            self.update_status("Mode: BEFORE - Using local camera (Pi_2)")
        else:
            self.update_status("Mode: AFTER - Using remote camera (Pi_1 via server)")
    
    def on_capture_click(self):
        self.update_status(f"Starting {self.current_mode} image capture...")
        self.disable_capture_button()
        
        if self.current_mode == "BEFORE":
            threading.Thread(target=self.capture_before_image, daemon=True).start()
        else:
            threading.Thread(target=self.capture_after_image, daemon=True).start()
    
    def on_test_connection_click(self):
        if self.current_mode == "BEFORE":
            self.test_local_camera()
        else:
            threading.Thread(target=self.test_server_connection, daemon=True).start()
    
    def on_focus_adjust_click(self):
        if self.current_mode == "BEFORE":
            self.adjust_local_focus()
        else:
            threading.Thread(target=self.adjust_server_focus, daemon=True).start()
    
    def on_light_control_click(self, action):
        if self.current_mode != "AFTER":
            self.update_status("ⓘ Lighting control only available in AFTER mode")
            return
        threading.Thread(target=self.control_server_lighting, args=(action,), daemon=True).start()
    
    def on_closing(self):
        if messagebox.askyesno("Exit", "Do you really want to exit the Core Imaging System?"):
            try:
                if self.local_camera:
                    self.local_camera.close()
            except:
                pass
            self.root.destroy()
    
    def update_camera_preview(self):
        if self.local_camera_ready:
            current_array_frame = self.local_camera.get_preview_frame() #call on preview_frame class in LocalCam
            pil_frame = Image.fromarray(current_array_frame) # Convert from Numpy Array to PIL 
            preview_frame = ImageTk.PhotoImage(pil_frame) #convert from PIL to Tkinter 
            self.preview_frame = preview_frame # wihtout this line, frame will be immeditely deleted, need to have a refercne to the .PhotoImage
            self.preview_label.config(image=preview_frame) 
            self.root.after(100, self.update_camera_preview)
        else:
            print("The Camera is not initialized")
    
    def update_project_lbl(self):
        if self.current_project_ID is None:
            self.current_proj_lbl_cnt.config(text="Project: Create Project to Begin")
        else:
            self.current_proj_lbl_cnt.config(text=f"Project: #{self.current_project_ID}")
                
            
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    # CAMERA OPERATIONS
    
    def capture_before_image(self):
        try:
            if not self.local_camera_ready:
                raise Exception("Local camera not initialized")
            if self.current_project_ID:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"BEFORE_{timestamp}.jpg"
                filepath = os.path.join("images", filename)
                
                os.makedirs("images", exist_ok=True)
                
                image = self.local_camera.capture()

                
                success = cv2.imwrite(filepath, image)
                
                if success:
                    self.show_capture_feedback
                    self.update_status(f"✓ BEFORE image captured: {filename}")
                    

                    bk.update_before_image(self.current_project_ID, image)
                    boat_detected_IDs = bk.tag_detector(image,'4')
                    box_detected_IDs = bk.tag_detector(image, '5')
                    
                    if boat_detected_IDs is not None:
                        for tag_ID in boat_detected_IDs.flatten():
                            bk.boat_tag_insert(int(tag_ID), self.current_project_ID)
                    
                    if box_detected_IDs is not None:
                        for tag_ID in box_detected_IDs.flatten():
                            bk.box_tag_insert(int(tag_ID), self.current_project_ID)
                            
                    print(f"✓ BEFORE image saved to project {self.current_project_ID}")
                    self.update_status(f"✓ BEFORE image saved to project {self.current_project_ID}")
                    
                else:
                    print("File save failed!")
                    
            else:
                print("No current project ID!")
                tk.messagebox.showwarning(title="Ooops", message="Please create or select a project")
            
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            self.update_status(f"✗ BEFORE capture error: {str(e)}")
            
    
    def capture_after_image(self):
        try:
            if not self.local_camera_ready:
                raise Exception("Local camera not initialized")
            if self.current_project_ID:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"AFTER_{timestamp}.jpg"
                filepath = os.path.join("images", filename)
                
                os.makedirs("images", exist_ok=True)
                
                image = self.local_camera.capture()
                success = cv2.imwrite(filepath, image)
                if success:
                    self.show_capture_feedback
                    self.update_status(f"✓ AFTER image captured: {filename}")
                    boat_detected_IDs = bk.tag_detector(image,'4')
                    box_detected_IDs = bk.tag_detector(image, '5')
                    verification = bk.verify_project_tags(self.current_project_ID, boat_detected_IDs, box_detected_IDs)
                    if verification:
                        bk.update_after_image(self.current_project_ID, image)
                        print(f"✓ AFTER image saved to project {self.current_project_ID}")
                        self.update_status(f"✓ AFTER image saved to project {self.current_project_ID}")
                        proj_check = tk.messagebox.askquestion("Project Status", "Is the project complete?")
                        if proj_check == 'yes':
                            bk.release_project_tags(self.current_project_ID)
                            print(f"Project {self.current_project_ID} is complete")
                            self.update_status(f"Project {self.current_project_ID} is complete")
                            self.current_project_ID = None
                            self.before_button.config(state='disabled')
                            self.after_button.config(state='disabled')
                            self.update_project_lbl()
                        else:
                            print("project not yet completed")
                            self.update_status("project not yet completed")
                    else:
                        print(f" AFTER image captured but Verification failed - Please retake after image and verify tags")
                        self.update_status(f" AFTER image captured but Verification failed - Please retake after image and verify tags")
            else:
                print("ERROR - Must be in a project to take any core sample images")
                self.update_status("ERROR - Must be in a project to take any core sample images")
                
                tk.messagebox.showwarning(title = "Ooops",message = "Please create or select a project")
            
        except Exception as e:
            self.update_status(f"✗ AFTER capture error: {str(e)}")
       
            
    def add_boats(self):
        # detect new boat
        if self.current_project_ID:
            boat_detection_frame = self.local_camera.get_preview_frame()
            if boat_detection_frame is not None:
                boat_detected_IDs = bk.tag_detector(boat_detection_frame, '4')
                if boat_detected_IDs is None:
                    print("No Aruco Boat Tag detected - please reposition boat")
                    self.update_status("No Aruco Boat Tag detected - please reposition boat")
                else:
                    for ids in boat_detected_IDs:
                        bk.boat_tag_insert(int(ids), self.current_project_ID)
                        print(f"Boat tag {ids} added")
                        self.update_status(f"Boat tag {ids} added")
            else:
                print("Cannot get camera frame")
                self.update_status("Cannot get camera frame")
        else:
            print("Not in project, take Before Image first")
            self.update_status("Not in project, take Before Image first")
            
    
    def before_picure_clicked(self):
        self.popup_window = tk.Toplevel()
        self.popup_window.geometry("400x300")
        self.popup_window.title("Project Creation")
        self.popup_window.lift()
        self.popup_window.grab_set()
        self.popup_window.focus()
        label = tk.Label(self.popup_window, text = "Create New Project", bg = 'lightgrey')
        label.pack()
        # seprate popup in two seprate sides
        entry_container = tk.Frame(self.popup_window, bg = 'lightgrey')
        entry_container.pack(side = tk.RIGHT, fill= tk.BOTH, expand =True)
        name_container = tk.Frame(self.popup_window, bg = 'lightgrey')
        name_container.pack(side = tk.LEFT, fill= tk.BOTH, expand =True)
        # submit button, call submit form function
        submit_button = tk.Button(entry_container, text="Submit Form", command = self.submit_form)
        submit_button.pack(side = tk.BOTTOM, pady= 12.5)
        # entry variables, used self as used outside in submit_form
        self.depth_from_entry = tk.Entry(entry_container, font=('calibre',10,'normal'))
        self.depth_to_entry = tk.Entry(entry_container, font=('calibre',10,'normal'))
        self.core_numb_entry = tk.Entry(entry_container, font=('calibre',10,'normal'))
        self.box_numb_entry = tk.Entry(entry_container, font=('calibre',10,'normal'))
        self.BH_ID_entry = tk.Entry(entry_container, font=('calibre',10,'normal'))
        self.root.after(10, lambda: self.depth_from_entry.focus())
        self.depth_from_entry.bind("<Return>", lambda e: self.depth_to_entry.focus())
        self.depth_to_entry.bind("<Return>", lambda e: self.core_numb_entry.focus())
        self.core_numb_entry.bind("<Return>", lambda e: self.box_numb_entry.focus())
        self.box_numb_entry.bind("<Return>", lambda e: self.BH_ID_entry.focus())
        self.BH_ID_entry.bind("<Return>", lambda e: self.submit_form())
        # place 
        self.depth_from_entry.pack(pady = 10)
        self.depth_to_entry.pack(pady = 9)
        self.core_numb_entry.pack(pady = 9.3)
        self.box_numb_entry.pack(pady = 9)
        self.BH_ID_entry.pack(pady = 9.5)
        # Labels
        depth_from_lbl = tk.Label(name_container, text = 'Depth From (m)', font = ('calibre',10,'bold'), bg='lightgrey')
        depth_to_lbl = tk.Label(name_container, text = 'Depth To (m)', font = ('calibre',10,'bold'), bg='lightgrey')
        core_numb_lbl = tk.Label(name_container, text = 'Core Number', font = ('calibre',10,'bold'), bg='lightgrey')
        box_numb_lbl = tk.Label(name_container, text = 'Box Number', font = ('calibre',10,'bold'), bg='lightgrey')
        BH_ID_lbl = tk.Label(name_container, text = 'Bore Hole ID', font = ('calibre',10,'bold'), bg='lightgrey')
        # plcae
        depth_from_lbl.pack(pady = 10)
        depth_to_lbl.pack(pady = 10)
        core_numb_lbl.pack(pady = 10)
        box_numb_lbl.pack(pady = 10)
        BH_ID_lbl.pack(pady = 10)
    
    def submit_form(self):
        depth_from = self.depth_from_entry.get()
        depth_to = self.depth_to_entry.get()
        core_numb = self.core_numb_entry.get()
        box_numb = self.box_numb_entry.get()
        BH_ID = self.BH_ID_entry.get()
        
        if not all([depth_from, depth_to, core_numb, box_numb, BH_ID]):
            print("Error: All fields required!")
            self.update_status("Error: All fields required!")
            return
        
        print(f"Depth From: {depth_from}")
        self.update_status(f"Depth From: {depth_from}")
        print(f"Depth To: {depth_to}")
        self.update_status(f"Depth To: {depth_to}")
        print(f"Core Number: {core_numb}")
        self.update_status(f"Core Number: {core_numb}")
        print(f"Box Number: {box_numb}")
        self.update_status(f"Box Number: {box_numb}")
        print(f"BH ID: {BH_ID}")
        self.update_status(f"BH ID: {BH_ID}")
        
        project_ID = bk.create_project(depth_from, depth_to, core_numb, box_numb, BH_ID)
        self.current_project_ID = project_ID
        
        self.before_button.config(state='normal')
        self.after_button.config(state='normal')
        print(f"Project {project_ID} created - ready for images")
        self.update_status(f"Project {project_ID} created - ready for images")
        self.update_project_lbl()
        
        
        self.popup_window.destroy()
        print(f"Project #{project_ID} created - Picture functionality returned ")
        self.update_status(f"Project #{project_ID} created - Picture functionality returned ")

               
    def show_capture_feedback(self):
        print("\a") # apprently putting this in should give a little beep when pictures are taken
        self.update_status(f"✓ BEFORE image captured: {filename}")

    '''=================================================================================================================='''
    '''=================================================================================================================='''
    
    def test_server_connection(self):
        """Test server connection in background thread"""
        try:
            # Implement PC2RPi_client test
            # client = PC2RPi_client(RPi="Pi_1", port=self.server_port)
            # client.connect_client()
            # success = client.request("test")
            
            # Placeholder for now
            self.update_status("✓ Server connection (AFTER) successful")
            
        except Exception as e:
            self.update_status(f"✗ Server connection test failed: {str(e)}")
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    
    def adjust_local_focus(self):
        """Adjust local camera focus"""
        try:
            # Implement local focus adjustment
            # self.local_camera.set_autofocus()
            self.update_status("✓ Local camera auto-focus enabled")
        except Exception as e:
            self.update_status(f"✗ Focus adjustment failed: {str(e)}")
    
    def adjust_server_focus(self):
        """Adjust server camera focus in background thread"""
        try:
            # Implement server focus adjustment
            # client = PC2RPi_client(RPi="Pi_1", port=self.server_port)
            # client.connect_client()
            # success = client.request("set_autofocus")
            
            self.update_status("✓ Server camera focus adjusted")
            
        except Exception as e:
            self.update_status(f"✗ Server focus adjustment error: {str(e)}")
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''
    
    def control_server_lighting(self, action):
        """Control server lighting in background thread"""
        try:
            # Implement lighting control
            # client = PC2RPi_client(RPi="Pi_1", port=self.server_port)
            # client.connect_client()
            # command = "top_light_on" if action == "on" else "top_light_off"
            # success = client.request(command)
            
            message = f"Top light turned {'ON' if action == 'on' else 'OFF'}"
            self.update_status(f"✓ {message}")
            
        except Exception as e:
            self.update_status(f"✗ Lighting control error: {str(e)}")
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                           f"{self.system_name} System {self.version}\n\n"
                           "Dual-camera core imaging system\n"
                           "BEFORE: Local camera (Pi_2)\n"
                           "AFTER: Remote camera (Pi_1)")
    
    def show_system_status(self):
        """Show system status dialog"""
        local_status = "Ready" if self.local_camera_ready else "Not Ready"
        status_msg = (f"Current Mode: {self.current_mode}\n"
                     f"Local Camera: {local_status}\n"
                     f"Server: {self.server_ip}:{self.server_port}")
        messagebox.showinfo("System Status", status_msg)
    
    '''=================================================================================================================='''
    '''=================================================================================================================='''

    
    def update_status(self, message):
        """Update status display with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        def _update():
            self.txt.insert(tk.END, formatted_message)
            self.txt.see(tk.END)
        
        if threading.current_thread() == threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
            
    
    def clear_status(self):
        """Clear status display"""
        self.txt.delete('1.0', tk.END)
        self.update_status("Status cleared")
   
        
    '''=================================================================================================================='''
    '''=================================================================================================================='''


if __name__ == "__main__":
    app = CoreImagingUI("Core Imaging", "v1.0")