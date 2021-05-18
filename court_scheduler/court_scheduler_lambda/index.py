#!/usr/bin/env python
""" app.courtreserve.com adapter """
import logging
import logging.config
import os
import json

from botocore.exceptions import ClientError

from court_reserve import CourtReserveAdapter
from helpers import get_secret_value, offset_today, court_preferences, find_open_court

logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)

# Load environment variables
CONFIG = {**os.environ}


def handler(event=None, context=None):
    """Lambda function handler

    Args:
        event (dict): AWS Lambda event object
        context (dict): AWS Lambda context object.

    Returns
        (dict) Response
    """
    dry_run = CONFIG["DRY_RUN"].lower() == "true"
    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {"message": None},
    }
    try:
        # Get court reserve secrets and court preferences from AWS secrets manager
        settings = json.loads(get_secret_value(CONFIG["SECRET_ID"]))
        booking_date = offset_today(CONFIG["DAYS_OFFSET"], CONFIG["LOCAL_TIMEZONE"])
        weekday_name = booking_date.strftime("%A").lower()

        preferences = court_preferences(settings["PREFERENCES_V2"], booking_date)
        if not preferences:
            response["body"]["message"] = f"Preferences not found for {weekday_name}"
            return response

        # Get existing reservations from app.courtreserve.com
        court_reserve = CourtReserveAdapter(
            org_id=settings["ORG_ID"],
            username=settings["USERNAME"],
            password=settings["PASSWORD"],
        )
        bookings = court_reserve.list_reservations(date=booking_date)

        # Find open court
        open_court = find_open_court(bookings, preferences)
        if not open_court:
            response["body"]["message"] = f"No open court found for {weekday_name}"
            return response

        # Create reservation
        players = settings["PREFERENCES_V2"][weekday_name]["players"]
        court, start, end = open_court
        court_reserve.create_reservation(court, start, end, players, dry_run)

    except KeyError as err:
        logger.exception(err)
        response["statusCode"] = 500
        response["body"]["message"] = err
    except ClientError as err:
        logger.exception(err)
        response["statusCode"] = 500
        response["body"]["message"] = err
    except TypeError as err:
        logger.exception(err)
        response["statusCode"] = 500
        response["body"]["message"] = err
    except AssertionError as err:
        logger.exception(err)
        response["statusCode"] = 500
        response["body"]["message"] = err
    else:
        response["body"][
            "message"
        ] = f"{court} reserved at {start.strftime('%I:%M %p %Z')}"

    return response


if __name__ == "__main__":
    handler()
