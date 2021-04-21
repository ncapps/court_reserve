"""
Court Reserve spider settings
"""

# Configure log level
# 1. logging.CRITICAL - for critical errors (highest severity)
# 2. logging.ERROR - for regular errors
# 3. logging.WARNING - for warning messages
# 4. logging.INFO - for informational messages
# 5. logging.DEBUG - for debugging messages (lowest severity)

SETTINGS = {
    "DOMAIN": "https://app.courtreserve.com",
    "LOG_LEVEL": "WARNING",
    "DAY_OFFSET": 1,
    "SCHEDULE": {
        "thursday": {
            "request_times": [("6:30 PM", "8:00 PM"), ("7:00 PM", "8:00 PM")],
            "court_ids": ["14610", "14614", "14611", "14613", "14612"],
        },
        "friday": {
            "request_times": [("6:30 PM", "8:00 PM"), ("7:00 PM", "8:00 PM")],
            "court_ids": ["14610", "14614", "14611", "14613", "14612"],
        },
    },
}
