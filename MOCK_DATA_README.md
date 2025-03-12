# Realistic Mock Data for Energy Company Voice Agent

This document describes the realistic mock data created for the energy company voice agent demo.

## Customer Profiles

We've created 5 customer profiles with realistic Singapore names:

1. Justin Lee (ID: CUST0000, Email: justin@example.com)
2. Wei Ling Tan (ID: CUST0001, Email: wei@example.com)
3. Muhammad Bin Abdullah (ID: CUST0002, Email: muhammad@example.com)
4. Siti Binte Zainudin (ID: CUST0003, Email: siti@example.com)
5. Raj Patel (ID: CUST0004, Email: raj@example.com)

Each customer has:
- A unique customer ID
- A Singapore-style address
- A Singapore phone number
- An email address in the format `firstname@example.com`
- A joined date

## Use Cases

### Use Case 1: Understanding the Bill

The AI can handle common billing-related queries such as:

- "What is my current month's energy bill?"
- "What was my last month's energy bill?"
- "What is my energy usage this month?"
- "Can you explain the rate breakdown on my bill?"
- "Tell me about green energy plans"
- "Why is my bill higher this month?"
- "How does my usage compare to last month?"
- "What discounts am I eligible for?"
- "When is my bill due?"
- "How can I reduce my energy costs?"

The mock data includes:
- 6 months of billing history for each contract
- Detailed energy usage data for the most recent month
- Different plan types (Fixed Price, Discount Off Tariff, Peak/Off-Peak, Green Energy)
- Various discounts and promotions

### Use Case 2: Handling Complaints

The AI can accept and record customer complaints, such as power outages or energy disruptions.

Process:
1. The AI confirms the complaint with the user, including their address
2. The complaint is stored in a structured CSV file (`complaints.csv`)
3. The CSV includes Serial No., Name, Address, Complaint Details, and Timestamp

A sample complaint has been pre-populated in the CSV file.

### Use Case 3: New Connections or Service Requests

The AI can handle requests for new service connections, upgrades, or modifications.

The system will:
1. Ask for the customer's name and other relevant details
2. Check if the customer already exists in the system
3. Create a new customer record if needed
4. Record the service request with details

## Data Files

- **Mock Data**: Located in `mock_data_outputs/mock_data_[timestamp].json`
- **Complaints**: Stored in `complaints.csv`

## Utility Scripts

### Generate Mock Data

To regenerate the mock data, run:

```
python generate_mock_data.py
```

This will create a new mock data file with a current timestamp and reset the complaints.csv file with a sample complaint.

### Add a Complaint

To manually add a new complaint to the complaints.csv file, run:

```
python add_complaint.py "Customer Name" "Customer Address" "Complaint Details"
```

Example:
```
python add_complaint.py "Wei Ling Tan" "Block 123, #10-20, Singapore 123456" "Frequent power fluctuations in the evening"
```

### Add a Service Request

To manually add a new service request to the mock data, run:

```
python add_service_request.py "Customer Name" "Phone" "Email" "Address" "Service Type" "Details"
```

Example:
```
python add_service_request.py "New Customer" "+6591234567" "new@example.com" "Block 456, #05-10, Singapore 654321" "New Connection" "Need electricity connection for new apartment"
```

## Testing the Use Cases

### Use Case 1: Understanding the Bill

Test queries:
- "What is my current month's energy bill for Justin Lee?"
- "Show me Wei Ling Tan's energy usage for last month"
- "Explain the rate breakdown on Muhammad's latest bill"
- "What green energy options are available for Raj Patel?"

### Use Case 2: Handling Complaints

Test scenarios:
- "I want to report a power outage at my address"
- "There was a power surge that damaged my appliances"
- "My electricity has been fluctuating all day"

### Use Case 3: New Connections or Service Requests

Test scenarios:
- "I need a new electricity connection for my new apartment"
- "I want to upgrade my current plan to a green energy plan"
- "How do I request a smart meter installation?" 