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
        event (dict):
        context (dict):

    Returns
        Response (dict):
    """

    try:
        # Get court reserve secrets and court preferences from AWS secrets manager
        settings = json.loads(get_secret_value(CONFIG["SECRET_ID"]))
        booking_date = offset_today(CONFIG["DAYS_OFFSET"], CONFIG["LOCAL_TIMEZONE"])

        preferences = court_preferences(settings["PREFERENCES_V2"], booking_date)
        if not preferences:
            # TODO Lambda return value
            return

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
            # TODO Lambda return value
            return

        # Create reservation
        weekday_name = booking_date.strftime("%A").lower()
        players = settings["PREFERENCES_V2"][weekday_name]["players"]
        court, start, end = open_court
        court_reserve.create_reservation(court, start, end, players)

    except KeyError as err:
        # TODO Lambda return value
        logger.exception(err)
    except ClientError as err:
        # TODO Lambda return value
        # Secret error
        logger.exception(err)
    except AssertionError as err:
        # TODO Lambda return value
        # Login failure
        logger.exception(err)

    # Get existing reservations


if __name__ == "__main__":
    handler()
