import asyncio
import json
from datetime import datetime, timedelta
import random
from common.config import ARTIFICIAL_DELAY, MOCK_DATA_SIZE
import pathlib
import csv
import os


def save_mock_data(data):
    """Save mock data to a timestamped file in mock_data_outputs directory."""
    # Create mock_data_outputs directory if it doesn't exist
    output_dir = pathlib.Path("mock_data_outputs")
    output_dir.mkdir(exist_ok=True)

    # Clean up old mock data files
    cleanup_mock_data_files(output_dir)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"mock_data_{timestamp}.json"

    # Save the data with pretty printing
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nMock data saved to: {output_file}")


def cleanup_mock_data_files(output_dir):
    """Remove all existing mock data files in the output directory."""
    for file in output_dir.glob("mock_data_*.json"):
        try:
            file.unlink()
        except Exception as e:
            print(f"Warning: Could not delete {file}: {e}")


# Mock data generation
def generate_mock_data():
    customers = []
    appointments = []
    contracts = []
    billing_history = []
    usage_data = []
    payment_methods = []

    # Top Singapore names (including Justin Lee as requested)
    sg_names = ["Justin Lee", "Wei Ling Tan", "Muhammad Bin Abdullah", "Siti Binte Zainudin", "Raj Patel"]
    
    # Generate customers with realistic Singapore names
    for i in range(MOCK_DATA_SIZE["customers"]):
        name = sg_names[i]
        first_name = name.split()[0].lower()
        customer = {
            "id": f"CUST{i:04d}",
            "name": name,
            "phone": f"+65{random.randint(80000000, 99999999)}",  # Singapore mobile number format
            "email": f"{first_name}@example.com",
            "address": f"Block {random.randint(1, 999)}, #{random.randint(1, 20)}-{random.randint(1, 99)}, Singapore {random.randint(100000, 999999)}",
            "joined_date": (
                datetime.now() - timedelta(days=random.randint(0, 730))
            ).isoformat(),
        }
        customers.append(customer)

    # Generate appointments
    for i in range(MOCK_DATA_SIZE["appointments"]):
        customer = random.choice(customers)
        appointment = {
            "id": f"APT{i:04d}",
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "date": (datetime.now() + timedelta(days=random.randint(0, 14))).isoformat(),
            "service": random.choice(
                ["Contract Consultation", "Bill Review", "Energy Audit", "Plan Advisory", "Complaint Resolution"]
            ),
            "status": random.choice(["Scheduled", "Completed", "Cancelled"]),
            "location": "JTC Summit (near Jurong East MRT Station)",
            "notes": random.choice([
                "Customer wants to discuss bill discrepancies",
                "Energy efficiency consultation",
                "Contract renewal discussion",
                "Smart meter installation follow-up",
                "Solar panel installation inquiry",
                "",
            ]),
        }
        appointments.append(appointment)

    # Generate energy contracts
    for i in range(MOCK_DATA_SIZE["orders"]):  # Using orders size for contracts
        customer = random.choice(customers)
        plan_types = ["Fixed Price Plan", "Discount Off Tariff", "Peak/Off-Peak Plan", "Green Energy Plan"]
        contract_terms = [6, 12, 24, 36]  # Months
        selected_plan = random.choice(plan_types)
        start_date = datetime.now() - timedelta(days=random.randint(0, 365))
        term_months = random.choice(contract_terms)
        end_date = start_date + timedelta(days=term_months * 30)
        
        contract = {
            "id": f"CONT{i:04d}",
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "term_months": term_months,
            "plan_type": selected_plan,
            "monthly_usage": round(random.uniform(200.0, 1200.0), 2),  # kWh
            "rate": round(random.uniform(0.18, 0.30), 4),  # $ per kWh
            "status": random.choice(["Active", "Pending", "Renewed", "Expired"]),
            "auto_renewal": random.choice([True, False]),
            "green_energy_percentage": 100 if selected_plan == "Green Energy Plan" else random.choice([0, 10, 20, 50]),
            "promotion_code": random.choice(["WELCOME20", "LOYAL10", "GREEN15", ""]),
            "early_termination_fee": round(random.uniform(50, 200), 2),
        }
        contracts.append(contract)
        
        # Generate billing history for each contract
        for month in range(6):  # Last 6 months of billing
            bill_date = datetime.now() - timedelta(days=30 * month)
            if bill_date > start_date:  # Only generate bills after contract start date
                # Calculate usage with some randomness but trending with seasons
                base_usage = contract["monthly_usage"]
                seasonal_factor = 1.0 + (0.2 * (month % 3 - 1))  # Simulate seasonal changes
                random_factor = random.uniform(0.8, 1.2)  # Random fluctuation
                monthly_usage = base_usage * seasonal_factor * random_factor
                
                # Calculate charges
                energy_charge = monthly_usage * contract["rate"]
                transmission_fee = monthly_usage * 0.05  # 5 cents per kWh for transmission
                gst = (energy_charge + transmission_fee) * 0.08  # 8% GST
                total_amount = energy_charge + transmission_fee + gst
                
                # Apply discounts if any
                discount = 0
                if contract["promotion_code"]:
                    if contract["promotion_code"] == "WELCOME20":
                        discount = total_amount * 0.20
                    elif contract["promotion_code"] == "LOYAL10":
                        discount = total_amount * 0.10
                    elif contract["promotion_code"] == "GREEN15":
                        discount = total_amount * 0.15
                
                total_after_discount = total_amount - discount
                
                bill = {
                    "id": f"BILL{len(billing_history):04d}",
                    "contract_id": contract["id"],
                    "customer_id": customer["id"],
                    "bill_date": bill_date.isoformat(),
                    "due_date": (bill_date + timedelta(days=21)).isoformat(),
                    "billing_period_start": (bill_date - timedelta(days=30)).isoformat(),
                    "billing_period_end": bill_date.isoformat(),
                    "usage_kwh": round(monthly_usage, 2),
                    "energy_charge": round(energy_charge, 2),
                    "transmission_fee": round(transmission_fee, 2),
                    "gst": round(gst, 2),
                    "discount": round(discount, 2),
                    "total_amount": round(total_after_discount, 2),
                    "status": random.choice(["Paid", "Unpaid", "Overdue"]),
                    "payment_date": (bill_date + timedelta(days=random.randint(1, 20))).isoformat() if random.random() > 0.2 else None,
                }
                billing_history.append(bill)
                
                # Generate daily usage data for the most recent month
                if month == 0:  # Only for the most recent month
                    for day in range(30):
                        usage_date = bill_date - timedelta(days=day)
                        daily_usage = monthly_usage / 30 * random.uniform(0.7, 1.3)  # Daily fluctuation
                        
                        # Add peak and off-peak usage for Peak/Off-Peak plans
                        peak_usage = daily_usage * 0.6 if contract["plan_type"] == "Peak/Off-Peak Plan" else None
                        off_peak_usage = daily_usage * 0.4 if contract["plan_type"] == "Peak/Off-Peak Plan" else None
                        
                        usage_entry = {
                            "customer_id": customer["id"],
                            "contract_id": contract["id"],
                            "date": usage_date.isoformat(),
                            "total_kwh": round(daily_usage, 2),
                            "peak_kwh": round(peak_usage, 2) if peak_usage else None,
                            "off_peak_kwh": round(off_peak_usage, 2) if off_peak_usage else None,
                            "carbon_offset_kg": round(daily_usage * 0.4 * (contract["green_energy_percentage"] / 100), 2),
                        }
                        usage_data.append(usage_entry)
    
    # Generate payment methods for customers
    for customer in customers:
        # Most customers have 1-2 payment methods
        num_payment_methods = random.randint(1, 2)
        for _ in range(num_payment_methods):
            payment_type = random.choice(["Credit Card", "GIRO", "PayNow"])
            
            if payment_type == "Credit Card":
                payment_method = {
                    "id": f"PAY{len(payment_methods):04d}",
                    "customer_id": customer["id"],
                    "type": payment_type,
                    "card_type": random.choice(["Visa", "MasterCard", "American Express"]),
                    "last_four": f"{random.randint(1000, 9999)}",
                    "expiry_date": f"{random.randint(1, 12)}/{random.randint(23, 28)}",
                    "is_default": random.choice([True, False]),
                }
            elif payment_type == "GIRO":
                payment_method = {
                    "id": f"PAY{len(payment_methods):04d}",
                    "customer_id": customer["id"],
                    "type": payment_type,
                    "bank_name": random.choice(["DBS", "OCBC", "UOB", "Standard Chartered"]),
                    "account_last_four": f"{random.randint(1000, 9999)}",
                    "is_default": random.choice([True, False]),
                }
            else:  # PayNow
                payment_method = {
                    "id": f"PAY{len(payment_methods):04d}",
                    "customer_id": customer["id"],
                    "type": payment_type,
                    "linked_to": random.choice(["NRIC", "Mobile Number"]),
                    "is_default": random.choice([True, False]),
                }
            
            payment_methods.append(payment_method)

    # Format sample data for display
    sample_data = []
    sample_customers = random.sample(customers, 3)
    for customer in sample_customers:
        customer_data = {
            "Customer": customer["name"],
            "ID": customer["id"],
            "Phone": customer["phone"],
            "Email": customer["email"],
            "Address": customer["address"],
            "Appointments": [],
            "Contracts": [],
            "Billing": [],
            "Usage": [],
            "Payment Methods": [],
        }

        # Add appointments
        customer_appointments = [
            a for a in appointments if a["customer_id"] == customer["id"]
        ]
        for apt in customer_appointments[:2]:
            customer_data["Appointments"].append(
                {
                    "Service": apt["service"],
                    "Date": apt["date"][:10],
                    "Status": apt["status"],
                    "Location": apt["location"],
                }
            )

        # Add contracts
        customer_contracts = [c for c in contracts if c["customer_id"] == customer["id"]]
        for contract in customer_contracts[:2]:
            customer_data["Contracts"].append(
                {
                    "ID": contract["id"],
                    "Plan": contract["plan_type"],
                    "Term": f"{contract['term_months']} months",
                    "Rate": f"${contract['rate']}/kWh",
                    "Status": contract["status"],
                    "Start Date": contract["start_date"][:10],
                    "End Date": contract["end_date"][:10],
                    "Auto Renewal": "Yes" if contract["auto_renewal"] else "No",
                    "Green Energy": f"{contract['green_energy_percentage']}%",
                }
            )
            
            # Add billing history
            contract_bills = [b for b in billing_history if b["contract_id"] == contract["id"]]
            for bill in contract_bills[:3]:  # Show last 3 bills
                customer_data["Billing"].append(
                    {
                        "Bill ID": bill["id"],
                        "Date": bill["bill_date"][:10],
                        "Amount": f"${bill['total_amount']}",
                        "Usage": f"{bill['usage_kwh']} kWh",
                        "Status": bill["status"],
                    }
                )
            
            # Add usage data
            contract_usage = [u for u in usage_data if u["contract_id"] == contract["id"]]
            for usage in contract_usage[:7]:  # Show last 7 days
                customer_data["Usage"].append(
                    {
                        "Date": usage["date"][:10],
                        "Usage": f"{usage['total_kwh']} kWh",
                        "Carbon Offset": f"{usage['carbon_offset_kg']} kg",
                    }
                )
        
        # Add payment methods
        customer_payments = [p for p in payment_methods if p["customer_id"] == customer["id"]]
        for payment in customer_payments:
            if payment["type"] == "Credit Card":
                payment_info = {
                    "Type": payment["type"],
                    "Card": f"{payment['card_type']} ending in {payment['last_four']}",
                    "Expiry": payment["expiry_date"],
                    "Default": "Yes" if payment["is_default"] else "No",
                }
            elif payment["type"] == "GIRO":
                payment_info = {
                    "Type": payment["type"],
                    "Bank": payment["bank_name"],
                    "Account": f"ending in {payment['account_last_four']}",
                    "Default": "Yes" if payment["is_default"] else "No",
                }
            else:  # PayNow
                payment_info = {
                    "Type": payment["type"],
                    "Linked to": payment["linked_to"],
                    "Default": "Yes" if payment["is_default"] else "No",
                }
            customer_data["Payment Methods"].append(payment_info)

        sample_data.append(customer_data)

    # Create data object
    mock_data = {
        "customers": customers,
        "appointments": appointments,
        "contracts": contracts,
        "billing_history": billing_history,
        "usage_data": usage_data,
        "payment_methods": payment_methods,
        "sample_data": sample_data,
    }

    # Save the mock data
    save_mock_data(mock_data)

    return mock_data


# Initialize mock data
MOCK_DATA = generate_mock_data()


# Complaint handling functionality
def save_complaint(name, address, complaint_details):
    """
    Save a customer complaint to a CSV file.
    
    Args:
        name (str): Customer name
        address (str): Customer address
        complaint_details (str): Details of the complaint
        
    Returns:
        dict: Information about the saved complaint
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
    
    return {
        "serial_no": serial_no,
        "name": name,
        "address": address,
        "complaint_details": complaint_details,
        "timestamp": timestamp
    }


async def handle_complaint(customer_id, complaint_details):
    """
    Handle a customer complaint.
    
    Args:
        customer_id (str): Customer ID
        complaint_details (str): Details of the complaint
        
    Returns:
        dict: Information about the processed complaint
    """
    await simulate_delay("database")
    
    # Find the customer
    customer = await get_customer(customer_id=customer_id)
    
    if not customer:
        return {"error": "Customer not found"}
    
    # Save the complaint
    complaint = save_complaint(
        name=customer["name"],
        address=customer["address"],
        complaint_details=complaint_details
    )
    
    return {
        "status": "success",
        "message": f"Complaint #{complaint['serial_no']} has been recorded",
        "complaint": complaint
    }


async def simulate_delay(delay_type):
    """Simulate processing delay based on operation type."""
    await asyncio.sleep(ARTIFICIAL_DELAY[delay_type])


async def get_customer(phone=None, email=None, customer_id=None):
    """Look up a customer by phone, email, or ID."""
    await simulate_delay("database")

    if phone:
        customer = next(
            (c for c in MOCK_DATA["customers"] if c["phone"] == phone), None
        )
    elif email:
        customer = next(
            (c for c in MOCK_DATA["customers"] if c["email"] == email), None
        )
    elif customer_id:
        customer = next(
            (c for c in MOCK_DATA["customers"] if c["id"] == customer_id), None
        )
    else:
        return {"error": "No search criteria provided"}

    return customer if customer else {"error": "Customer not found"}


async def get_customer_appointments(customer_id):
    """Get all appointments for a customer."""
    await simulate_delay("database")

    appointments = [
        a for a in MOCK_DATA["appointments"] if a["customer_id"] == customer_id
    ]
    return {"customer_id": customer_id, "appointments": appointments}


async def get_customer_contracts(customer_id):
    """Get all energy contracts for a customer."""
    await simulate_delay("database")

    contracts = [c for c in MOCK_DATA["contracts"] if c["customer_id"] == customer_id]
    return {"customer_id": customer_id, "contracts": contracts}


async def get_customer_billing(customer_id):
    """Get billing history for a customer."""
    await simulate_delay("database")

    bills = [b for b in MOCK_DATA["billing_history"] if b["customer_id"] == customer_id]
    return {"customer_id": customer_id, "billing_history": bills}


async def get_customer_usage(customer_id, days=30):
    """Get usage data for a customer."""
    await simulate_delay("database")

    usage = [u for u in MOCK_DATA["usage_data"] if u["customer_id"] == customer_id]
    # Sort by date and limit to requested days
    usage.sort(key=lambda x: x["date"], reverse=True)
    usage = usage[:days]
    
    return {"customer_id": customer_id, "usage_data": usage}


async def get_customer_payment_methods(customer_id):
    """Get payment methods for a customer."""
    await simulate_delay("database")

    payment_methods = [p for p in MOCK_DATA["payment_methods"] if p["customer_id"] == customer_id]
    return {"customer_id": customer_id, "payment_methods": payment_methods}


async def schedule_appointment(customer_id, date, service):
    """Schedule a new appointment."""
    await simulate_delay("database")

    # Verify customer exists
    customer = await get_customer(customer_id=customer_id)
    if "error" in customer:
        return customer

    # Create new appointment
    appointment_id = f"APT{len(MOCK_DATA['appointments']):04d}"
    appointment = {
        "id": appointment_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "date": date,
        "service": service,
        "status": "Scheduled",
        "location": "JTC Summit (near Jurong East MRT Station)",
        "notes": "",
    }

    MOCK_DATA["appointments"].append(appointment)
    return appointment


async def get_available_appointment_slots(start_date, end_date):
    """Get available appointment slots."""
    await simulate_delay("database")

    # Convert dates to datetime objects
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    # Generate available slots (9 AM to 5 PM, 1-hour slots)
    slots = []
    current = start
    while current <= end:
        if current.hour >= 9 and current.hour < 17:
            slot_time = current.isoformat()
            # Check if slot is already taken
            taken = any(a["date"] == slot_time for a in MOCK_DATA["appointments"])
            if not taken:
                slots.append(slot_time)
        current += timedelta(hours=1)

    return {"available_slots": slots}


async def prepare_agent_filler_message(websocket, message_type):
    """
    Handle agent filler messages while maintaining proper function call protocol.
    Returns a simple confirmation first, then sends the actual message to the client.
    """
    # First prepare the result that will be the function call response
    result = {"status": "queued", "message_type": message_type}

    # Prepare the inject message but don't send it yet
    if message_type == "lookup":
        inject_message = {
            "type": "InjectAgentMessage",
            "message": "Let me look that up for you...",
        }
    else:
        inject_message = {
            "type": "InjectAgentMessage",
            "message": "One moment please...",
        }

    # Return the result first - this becomes the function call response
    # The caller can then send the inject message after handling the function response
    return {"function_response": result, "inject_message": inject_message}


async def prepare_farewell_message(websocket, farewell_type):
    """End the conversation with an appropriate farewell message and close the connection."""
    # Prepare farewell message based on type
    if farewell_type == "thanks":
        message = "Thank you for calling! Have a great day!"
    elif farewell_type == "help":
        message = "I'm glad I could help! Have a wonderful day!"
    else:  # general
        message = "Goodbye! Have a nice day!"

    # Prepare messages but don't send them
    inject_message = {"type": "InjectAgentMessage", "message": message}

    close_message = {"type": "close"}

    # Return both messages to be sent in correct order by the caller
    return {
        "function_response": {"status": "closing", "message": message},
        "inject_message": inject_message,
        "close_message": close_message,
    }


async def request_new_service(customer_name, phone, email, address, service_type, details):
    """
    Handle a request for a new service connection or modification.
    
    Args:
        customer_name (str): Customer name
        phone (str): Customer phone number
        email (str): Customer email
        address (str): Customer address
        service_type (str): Type of service requested (new connection, upgrade, modification)
        details (str): Additional details about the request
        
    Returns:
        dict: Information about the processed request
    """
    await simulate_delay("database")
    
    # Check if customer already exists
    existing_customer = None
    if phone:
        existing_customer = await get_customer(phone=phone)
    if not existing_customer and email:
        existing_customer = await get_customer(email=email)
    
    # Create a new customer if they don't exist
    if not existing_customer:
        # Generate a new customer ID
        new_id = f"CUST{len(MOCK_DATA['customers']):04d}"
        
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
        MOCK_DATA["customers"].append(new_customer)
        
        # Save updated mock data
        save_mock_data(MOCK_DATA)
        
        customer_id = new_id
    else:
        customer_id = existing_customer["id"]
    
    # Create a service request record
    service_request = {
        "id": f"SRQ{len(MOCK_DATA.get('service_requests', [])):04d}",
        "customer_id": customer_id,
        "service_type": service_type,
        "details": details,
        "status": "Pending",
        "request_date": datetime.now().isoformat(),
    }
    
    # Initialize service_requests if it doesn't exist
    if "service_requests" not in MOCK_DATA:
        MOCK_DATA["service_requests"] = []
    
    # Add to mock data
    MOCK_DATA["service_requests"].append(service_request)
    
    # Save updated mock data
    save_mock_data(MOCK_DATA)
    
    return {
        "status": "success",
        "message": f"Service request #{service_request['id']} has been created",
        "service_request": service_request,
        "customer_id": customer_id
    }
