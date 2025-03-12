import csv
import os
import sys
from datetime import datetime

def add_complaint(name, address, complaint_details):
    """
    Add a new complaint to the complaints.csv file.
    
    Args:
        name (str): Customer name
        address (str): Customer address
        complaint_details (str): Details of the complaint
    """
    complaints_file = "complaints.csv"
    file_exists = os.path.isfile(complaints_file)
    
    # Get the next serial number
    serial_no = 1
    if file_exists:
        with open(complaints_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) > 1:  # If there's more than just the header
                serial_no = int(rows[-1][0]) + 1
    
    # Current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Write to CSV
    with open(complaints_file, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(["Serial No.", "Name", "Address", "Complaint Details", "Timestamp"])
        
        # Write complaint data
        writer.writerow([serial_no, name, address, complaint_details, timestamp])
    
    print(f"Complaint #{serial_no} added successfully.")
    print(f"Name: {name}")
    print(f"Address: {address}")
    print(f"Details: {complaint_details}")
    print(f"Timestamp: {timestamp}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python add_complaint.py \"Customer Name\" \"Customer Address\" \"Complaint Details\"")
        sys.exit(1)
    
    name = sys.argv[1]
    address = sys.argv[2]
    complaint_details = sys.argv[3]
    
    add_complaint(name, address, complaint_details) 