import socket
import json
import sys
import logging

class ScannerClient:
    
    REQUEST = {
        "test": "test",
        "get_project": "get_project",
        "send_project": "send_project"
    }
    
    def __init__(self, host="169.254.182.214", port=1517):
        self.host = host
        self.port = port
        self.sock = None
        
    def connect_client(self):
        """Connect to main Pi"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            return True
        except socket.error as e:
            print(f"Failed to connect to Main Pi: {e}")
            return False
    
    def close_client(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            self.sock = None
    
    def send_message(self, message):
        """Send message to server"""
        try:
            self.sock.sendall(message)
        except socket.error as e:
            print(f"Failed to send message: {e}")
            return False
        return True
    
    def get_message(self, size=4096):
        """Receive message from server"""
        try:
            data = self.sock.recv(size)
            return data
        except socket.error as e:
            print(f"Failed to receive message: {e}")
            return None
    
    def request(self, message):
        """Send request and handle response"""
        try:
            # Check if request is authorized
            if message not in self.REQUEST:
                print(f"Unknown request: {message}")
                return False
            
            # Connect for this request
            if not self.connect_client():
                return False
            
            # Send request
            self.send_message(message.encode())
            
            # Handle responses based on request type
            if message == self.REQUEST["test"]:
                response = self.get_message().decode("utf-8")
                self.close_client()
                return response == "connection_ok"
            
            elif message == self.REQUEST["get_project"]:
                response = self.get_message().decode("utf-8")
                self.close_client()
                if response == "project_ready":
                    return True
                elif response == "no_project":
                    return False
                else:
                    return False
            
            elif message == self.REQUEST["send_project"]:
                response = self.get_message().decode("utf-8")
                self.close_client()
                if response == "no_project":
                    return False, None
                else:
                    # Parse JSON project data
                    try:
                        project_data = json.loads(response)
                        return True, project_data
                    except json.JSONDecodeError:
                        return False, None
            
        except Exception as e:
            print(f"Request error: {e}")
            self.close_client()
            return False
    
    def get_project_data(self):
        """Complete workflow: check, request, receive project data"""
        # Step 1: Check if project is ready
        if self.request("get_project"):
            # Step 2: Request the actual data
            success, data = self.request("send_project")
            if success:
                # Step 3: Data received successfully
                return data
            else:
                return None
        else:
            return None
    
    def test_connection(self):
        """Test if Main Pi is responding"""
        return self.request("test")