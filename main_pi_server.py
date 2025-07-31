import socket
import json
import sys
import os

sys.path.append('/home/jeeves003/Desktop/Rasp2')
from ui_DB_manager import DbManager

class MainPiServer:
    
    REQUEST = {
        "test": "test",
        "get_project": "get_project", 
        "send_project": "send_project"
    }
    
    def __init__(self, host="", port=1517):
        self.host = host
        self.port = port
        self.db = DbManager()  #directly access the database 
        self.sock = None
        
    def get_current_project_info(self):
        self.db.c.execute("""
            SELECT project_ID, BH_ID, core_numb, depth_from, depth_to, box_numb 
            FROM project_table 
            WHERE after_image_data IS NULL 
            ORDER BY project_ID DESC LIMIT 1
        """)
        project_data = self.db.c.fetchone()
        
        if project_data:
            project_id, bh_id, core_numb, depth_from, depth_to, box_numb = project_data
            
            boat_tags = self.db.get_boat_tags(project_id)
            box_tags = self.db.get_box_tags(project_id)
            
            project_info = {
                'project_id': project_id,
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
        
    def start_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(1)
            print(f"Main Pi server listening on port {self.port}")
            print("Ready for Scanner PC connections...")
            
            while True:
                conn, addr = self.sock.accept()
                print(f"Scanner PC connected: {addr}")
                
                try:
                    # recieve requests
                    data = conn.recv(1024).decode("utf-8")
                    print(f"Received request: {data}")
                    
                    # Handle requests
                    if data == self.REQUEST["test"]:
                        conn.send(b"connection_ok")
                        print("Sent: connection_ok")
                        
                    elif data == self.REQUEST["get_project"]:
                        project_info = self.get_current_project_info()
                        if project_info:
                            conn.send(b"project_ready")
                            print("Sent: project_ready")
                        else:
                            conn.send(b"no_project")
                            print("Sent: no_project")
                            
                    elif data == self.REQUEST["send_project"]:
                        project_info = self.get_current_project_info()
                        if project_info:
                            json_data = json.dumps(project_info)
                            conn.send(json_data.encode("utf-8"))
                            print(f"Sent project data: {project_info['project_id']}")
                        else:
                            conn.send(b"no_project")
                            print("Sent: no_project")
                    
                    else:
                        conn.send(b"unknown_request")
                        print("Sent: unknown_request")
                        
                except Exception as e:
                    print(f"Error handling request: {e}")
                finally:
                    conn.close()
                    
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.sock:
                self.sock.close()

if __name__ == "__main__":
    server = MainPiServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer stopped")