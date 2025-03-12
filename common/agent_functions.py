import json
from datetime import datetime, timedelta
import asyncio
from common.business_logic import (
    get_customer,
    get_customer_appointments,
    get_customer_contracts,
    get_customer_billing,
    get_customer_usage,
    get_customer_payment_methods,
    schedule_appointment,
    get_available_appointment_slots,
    prepare_agent_filler_message,
    prepare_farewell_message,
    handle_complaint,
    request_new_service,
)


async def find_customer(params):
    """Look up a customer by phone, email, or ID."""
    phone = params.get("phone")
    email = params.get("email")
    customer_id = params.get("customer_id")

    result = await get_customer(phone=phone, email=email, customer_id=customer_id)
    return result


async def get_appointments(params):
    """Get appointments for a customer."""
    customer_id = params.get("customer_id")
    if not customer_id:
        return {"error": "customer_id is required"}

    result = await get_customer_appointments(customer_id)
    return result


async def get_contracts(params):
    """Get energy contracts for a customer."""
    customer_id = params.get("customer_id")
    if not customer_id:
        return {"error": "customer_id is required"}

    result = await get_customer_contracts(customer_id)
    return result


async def get_billing_history(params):
    """Get billing history for a customer."""
    customer_id = params.get("customer_id")
    if not customer_id:
        return {"error": "customer_id is required"}

    result = await get_customer_billing(customer_id)
    return result


async def get_usage_data(params):
    """Get energy usage data for a customer."""
    customer_id = params.get("customer_id")
    days = params.get("days", 30)
    
    if not customer_id:
        return {"error": "customer_id is required"}

    result = await get_customer_usage(customer_id, days)
    return result


async def get_payment_methods(params):
    """Get payment methods for a customer."""
    customer_id = params.get("customer_id")
    if not customer_id:
        return {"error": "customer_id is required"}

    result = await get_customer_payment_methods(customer_id)
    return result


async def create_appointment(params):
    """Schedule a new appointment."""
    customer_id = params.get("customer_id")
    date = params.get("date")
    service = params.get("service")

    if not all([customer_id, date, service]):
        return {"error": "customer_id, date, and service are required"}

    result = await schedule_appointment(customer_id, date, service)
    return result


async def check_availability(params):
    """Check available appointment slots."""
    start_date = params.get("start_date")
    end_date = params.get(
        "end_date", (datetime.fromisoformat(start_date) + timedelta(days=7)).isoformat()
    )

    if not start_date:
        return {"error": "start_date is required"}

    result = await get_available_appointment_slots(start_date, end_date)
    return result


async def agent_filler(websocket, params):
    """
    Handle agent filler messages while maintaining proper function call protocol.
    """
    result = await prepare_agent_filler_message(websocket, **params)
    return result


async def end_call(websocket, params):
    """
    End the conversation and close the connection.
    """
    farewell_type = params.get("farewell_type", "general")
    result = await prepare_farewell_message(websocket, farewell_type)
    return result


async def handle_customer_complaint(params):
    """Handle a customer complaint and record it in the system."""
    customer_id = params.get("customer_id")
    complaint_details = params.get("complaint_details")
    
    result = await handle_complaint(customer_id, complaint_details)
    
    return result


async def request_service_connection(params):
    """Handle a request for a new service connection or modification."""
    customer_name = params.get("customer_name")
    phone = params.get("phone")
    email = params.get("email")
    address = params.get("address")
    service_type = params.get("service_type")
    details = params.get("details")
    
    result = await request_new_service(
        customer_name, phone, email, address, service_type, details
    )
    
    return result


# Function definitions that will be sent to the Voice Agent API
FUNCTION_DEFINITIONS = [
    {
        "name": "agent_filler",
        "description": """Use this function to provide natural conversational filler before looking up information.
        ALWAYS call this function first with message_type='lookup' when you're about to look up customer information.
        After calling this function, you MUST immediately follow up with the appropriate lookup function (e.g., find_customer).""",
        "parameters": {
            "type": "object",
            "properties": {
                "message_type": {
                    "type": "string",
                    "description": "Type of filler message to use. Use 'lookup' when about to search for information.",
                    "enum": ["lookup", "general"],
                }
            },
            "required": ["message_type"],
        },
    },
    {
        "name": "find_customer",
        "description": """Look up a customer's account information. Use context clues to determine what type of identifier the user is providing:

        Customer ID formats:
        - Numbers only (e.g., '169', '42') → Format as 'CUST0169', 'CUST0042'
        - With prefix (e.g., 'CUST169', 'customer 42') → Format as 'CUST0169', 'CUST0042'
        
        Phone number recognition:
        - Singapore format: '6591234567' or '9123 4567' → Format as '+6591234567'
        - With country code: '+65 9123 4567' → Format as '+6591234567'
        - Spoken naturally: 'nine one two three, four five six seven' → Format as '+6591234567'
        - Always add +65 country code if not provided (for Singapore)
        
        Email address recognition:
        - Spoken naturally: 'my email is john dot smith at example dot com' → Format as 'john.smith@example.com'
        - With domain: 'john@example.com' → Use as is
        - Spelled out: 'j o h n at example dot com' → Format as 'john@example.com'""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID. Format as CUSTXXXX where XXXX is the number padded to 4 digits with leading zeros. Example: if user says '42', pass 'CUST0042'",
                },
                "phone": {
                    "type": "string",
                    "description": """Phone number with country code. Format as +65XXXXXXXX for Singapore:
                    - Add +65 if not provided
                    - Remove any spaces, dashes, or parentheses
                    - Convert spoken numbers to digits
                    Example: 'nine one two three four five six seven' → '+6591234567'""",
                },
                "email": {
                    "type": "string",
                    "description": """Email address in standard format:
                    - Convert 'dot' to '.'
                    - Convert 'at' to '@'
                    - Remove spaces between spelled out letters
                    Example: 'j dot smith at example dot com' → 'j.smith@example.com'""",
                },
            },
        },
    },
    {
        "name": "get_appointments",
        "description": """Retrieve all appointments for a customer. Use this function when:
        - A customer asks about their upcoming appointments
        - A customer wants to know their appointment schedule
        - A customer asks 'When is my next appointment?'
        
        Always verify you have the customer's account first using find_customer before checking appointments.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_contracts",
        "description": """Retrieve energy contract details for a customer. Use this function when:
        - A customer asks about their electricity plan
        - A customer wants to check contract status or details
        - A customer asks questions like 'What plan am I on?' or 'When does my contract expire?'
        
        Always verify you have the customer's account first using find_customer before checking contracts.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_billing_history",
        "description": """Retrieve billing history for a customer. Use this function when:
        - A customer asks about their bills or invoices
        - A customer wants to check payment status
        - A customer asks questions like 'What was my last bill?' or 'How much do I owe?'
        
        Always verify you have the customer's account first using find_customer before checking billing history.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_usage_data",
        "description": """Retrieve energy usage data for a customer. Use this function when:
        - A customer asks about their electricity consumption
        - A customer wants to track their usage patterns
        - A customer asks questions like 'How much electricity am I using?' or 'What's my daily usage?'
        
        Always verify you have the customer's account first using find_customer before checking usage data.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days of usage data to retrieve. Default is 30 days.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "get_payment_methods",
        "description": """Retrieve payment methods for a customer. Use this function when:
        - A customer asks about their payment options
        - A customer wants to check their registered payment methods
        - A customer asks questions like 'What card do I have on file?' or 'How am I paying my bills?'
        
        Always verify you have the customer's account first using find_customer before checking payment methods.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                }
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "create_appointment",
        "description": """Schedule a new appointment for a customer. Use this function when:
        - A customer wants to book a new appointment
        - A customer asks to schedule a consultation or energy audit
        
        Before scheduling:
        1. Verify customer account exists using find_customer
        2. Check availability using check_availability
        3. Confirm date/time and service type with customer before booking""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                },
                "date": {
                    "type": "string",
                    "description": "Appointment date and time in ISO format (YYYY-MM-DDTHH:MM:SS). Must be a time slot confirmed as available.",
                },
                "service": {
                    "type": "string",
                    "description": "Type of service requested. Must be one of the following: Contract Consultation, Bill Review, Energy Audit, Plan Advisory, or Complaint Resolution",
                    "enum": ["Contract Consultation", "Bill Review", "Energy Audit", "Plan Advisory", "Complaint Resolution"],
                },
            },
            "required": ["customer_id", "date", "service"],
        },
    },
    {
        "name": "check_availability",
        "description": """Check available appointment slots within a date range. Use this function when:
        - A customer wants to know available appointment times
        - Before scheduling a new appointment
        - A customer asks 'When can I come in?' or 'What times are available?'
        
        After checking availability, present options to the customer in a natural way, like:
        'I have openings on [date] at [time] or [date] at [time]. Which works better for you?'""",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SS). Usually today's date for immediate availability checks.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format. Optional - defaults to 7 days after start_date. Use for specific date range requests.",
                },
            },
            "required": ["start_date"],
        },
    },
    {
        "name": "end_call",
        "description": """End the conversation and close the connection. Call this function when:
        - User says goodbye, thank you, etc.
        - User indicates they're done ("that's all I need", "I'm all set", etc.)
        - User wants to end the conversation
        
        Examples of triggers:
        - "Thank you, bye!"
        - "That's all I needed, thanks"
        - "Have a good day"
        - "Goodbye"
        - "I'm done"
        
        Do not call this function if the user is just saying thanks but continuing the conversation.""",
        "parameters": {
            "type": "object",
            "properties": {
                "farewell_type": {
                    "type": "string",
                    "description": "Type of farewell to use in response",
                    "enum": ["thanks", "general", "help"],
                }
            },
            "required": ["farewell_type"],
        },
    },
    {
        "name": "handle_customer_complaint",
        "description": """Handle a customer complaint and record it in the system. Use this function when:
        - A customer reports a problem or issue
        - A customer wants to report a complaint or concern
        - A customer asks for help with a complaint
        
        Always verify you have the customer's account first using find_customer before handling a complaint.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer's ID in CUSTXXXX format. Must be obtained from find_customer first.",
                },
                "complaint_details": {
                    "type": "string",
                    "description": "Details of the complaint or concern",
                }
            },
            "required": ["customer_id", "complaint_details"],
        },
    },
    {
        "name": "request_service_connection",
        "description": """Handle a request for a new service connection or modification. Use this function when:
        - A customer wants to connect a new service
        - A customer wants to modify an existing service
        - A customer asks for help with a service request
        
        Always verify you have the customer's account first using find_customer before handling a service request.""",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's name",
                },
                "phone": {
                    "type": "string",
                    "description": "Customer's phone number with country code",
                },
                "email": {
                    "type": "string",
                    "description": "Customer's email address",
                },
                "address": {
                    "type": "string",
                    "description": "Customer's address",
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service requested",
                },
                "details": {
                    "type": "string",
                    "description": "Details of the service request",
                }
            },
            "required": ["customer_name", "phone", "email", "address", "service_type", "details"],
        },
    },
]

# Map function names to their implementations
FUNCTION_MAP = {
    "find_customer": find_customer,
    "get_appointments": get_appointments,
    "get_contracts": get_contracts,
    "get_billing_history": get_billing_history,
    "get_usage_data": get_usage_data,
    "get_payment_methods": get_payment_methods,
    "create_appointment": create_appointment,
    "check_availability": check_availability,
    "agent_filler": agent_filler,
    "end_call": end_call,
    "handle_customer_complaint": handle_customer_complaint,
    "request_service_connection": request_service_connection,
}
