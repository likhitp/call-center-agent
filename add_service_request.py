import json
import os
import sys
from datetime import datetime

def add_service_request(customer_name, phone, email, address, service_type, details):
    """
    Add a new service request to the mock data.
    
    Args:
        customer_name (str): Customer name
        phone (str): Customer phone number
        email (str): Customer email
        address (str): Customer address
        service_type (str): Type of service requested
        details (str): Additional details about the request
    """
    # Find the latest mock data file
    mock_data_dir = "mock_data_outputs"
    if not os.path.exists(mock_data_dir):
        print(f"Error: {mock_data_dir} directory not found.")
        return
    
    files = os.listdir(mock_data_dir)
    if not files:
        print(f"Error: No mock data files found in {mock_data_dir}.")
        return
    
    latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(mock_data_dir, x)))
    mock_data_file = os.path.join(mock_data_dir, latest_file)
    
    # Load the mock data
    with open(mock_data_file, 'r') as f:
        mock_data = json.load(f)
    
    # Check if customer already exists
    existing_customer = None
    for customer in mock_data["customers"]:
        if customer["phone"] == phone or customer["email"] == email:
            existing_customer = customer
            break
    
    # Create a new customer if they don't exist
    if not existing_customer:
        # Generate a new customer ID
        new_id = f"CUST{len(mock_data['customers']):04d}"
        
        # Create new customer
        new_customer = {
            "id": new_id,
            "name": customer_name,
            "phone": phone,
            "email": email,
            "address": address,
            "joined_date": datetime.now().isoformat(),
        }
        
        # Add to mock data
        mock_data["customers"].append(new_customer)
        customer_id = new_id
    else:
        customer_id = existing_customer["id"]
    
    # Initialize service_requests if it doesn't exist
    if "service_requests" not in mock_data:
        mock_data["service_requests"] = []
    
    # Create a service request record
    service_request = {
        "id": f"SRQ{len(mock_data['service_requests']):04d}",
        "customer_id": customer_id,
        "service_type": service_type,
        "details": details,
        "status": "Pending",
        "request_date": datetime.now().isoformat(),
    }
    
    # Add to mock data
    mock_data["service_requests"].append(service_request)
    
    # Save updated mock data
    with open(mock_data_file, 'w') as f:
        json.dump(mock_data, f, indent=2)
    
    print(f"Service request #{service_request['id']} added successfully.")
    print(f"Customer: {customer_name} (ID: {customer_id})")
    print(f"Service Type: {service_type}")
    print(f"Details: {details}")
    print(f"Status: {service_request['status']}")
    print(f"Request Date: {service_request['request_date']}")
    print(f"Mock data updated in: {mock_data_file}")

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python add_service_request.py \"Customer Name\" \"Phone\" \"Email\" \"Address\" \"Service Type\" \"Details\"")
        sys.exit(1)
    
    customer_name = sys.argv[1]
    phone = sys.argv[2]
    email = sys.argv[3]
    address = sys.argv[4]
    service_type = sys.argv[5]
    details = sys.argv[6]
    
    add_service_request(customer_name, phone, email, address, service_type, details) 