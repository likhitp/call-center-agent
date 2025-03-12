ARTIFICIAL_DELAY = {
    "database": 0.0,
    "external_api": 0.0, # Not in use in this reference implementation but left as an example for simulating different delays
    "heavy_computation": 0.0 # Not in use in this reference implementation but left as an example for simulating different delays
}


# Mock data settings
MOCK_DATA_SIZE = {
    "customers": 5,  # 5 customers as requested
    "appointments": 5,  # Minimal appointments
    "orders": 10,     # Enough contracts for billing history
    "billing_months": 6  # Number of months of billing history to generate
}

# Database settings (if using SQLite)
# Not in use in this reference implementation but left as an example for how to potentially integrate with a DB
DATABASE_CONFIG = {
    "path": "business_data.db",
    "enable": False  # Set to True to use actual SQLite instead of mock data
} 