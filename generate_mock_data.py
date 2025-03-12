import json
import random
import os
import csv
from datetime import datetime, timedelta

# Create mock data directory if it doesn't exist
os.makedirs("mock_data_outputs", exist_ok=True)

# Top Singapore names (including Justin Lee as requested)
sg_names = ["Justin Lee", "Wei Ling Tan", "Muhammad Bin Abdullah", "Siti Binte Zainudin", "Raj Patel"]

# Generate customers
customers = []
for i in range(5):
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

# Generate contracts
contracts = []
for i in range(10):
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

# Generate billing history
billing_history = []
for contract in contracts:
    for month in range(6):  # Last 6 months of billing
        bill_date = datetime.now() - timedelta(days=30 * month)
        start_date = datetime.fromisoformat(contract["start_date"])
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
                "customer_id": contract["customer_id"],
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

# Generate usage data
usage_data = []
for bill in billing_history:
    if datetime.fromisoformat(bill["bill_date"]) > datetime.now() - timedelta(days=30):  # Only for the most recent month
        for day in range(30):
            usage_date = datetime.fromisoformat(bill["bill_date"]) - timedelta(days=day)
            daily_usage = bill["usage_kwh"] / 30 * random.uniform(0.7, 1.3)  # Daily fluctuation
            
            # Find the contract for this bill
            contract = next((c for c in contracts if c["id"] == bill["contract_id"]), None)
            
            # Add peak and off-peak usage for Peak/Off-Peak plans
            peak_usage = daily_usage * 0.6 if contract and contract["plan_type"] == "Peak/Off-Peak Plan" else None
            off_peak_usage = daily_usage * 0.4 if contract and contract["plan_type"] == "Peak/Off-Peak Plan" else None
            
            usage_entry = {
                "customer_id": bill["customer_id"],
                "contract_id": bill["contract_id"],
                "date": usage_date.isoformat(),
                "total_kwh": round(daily_usage, 2),
                "peak_kwh": round(peak_usage, 2) if peak_usage else None,
                "off_peak_kwh": round(off_peak_usage, 2) if off_peak_usage else None,
                "carbon_offset_kg": round(daily_usage * 0.4 * (contract["green_energy_percentage"] / 100), 2) if contract else 0,
            }
            usage_data.append(usage_entry)

# Create complaints.csv file
with open("complaints.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Serial No.", "Name", "Address", "Complaint Details", "Timestamp"])
    # Add a sample complaint
    writer.writerow([
        1, 
        "Justin Lee", 
        customers[0]["address"], 
        "Experienced a power outage for 2 hours yesterday evening", 
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

# Create mock data object
mock_data = {
    "customers": customers,
    "contracts": contracts,
    "billing_history": billing_history,
    "usage_data": usage_data,
    "service_requests": [],  # Initialize empty service requests
}

# Save mock data to file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"mock_data_outputs/mock_data_{timestamp}.json"
with open(output_file, "w") as f:
    json.dump(mock_data, f, indent=2)

print(f"Mock data generated and saved to {output_file}")
print(f"Sample customers:")
for customer in customers:
    print(f"  - {customer['name']} (ID: {customer['id']}, Email: {customer['email']})")
print(f"Complaints file created: complaints.csv") 