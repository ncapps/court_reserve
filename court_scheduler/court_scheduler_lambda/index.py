#!/usr/bin/env python
""" app.courtreserve.com adapter """
import logging
import logging.config
import os
import json

from botocore.exceptions import ClientError

from court_reserve import CourtReserveAdapter
from helpers import get_secret_value, offset_today, court_preferences

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

        preferences = court_preferences(settings["PREFERENCES"], booking_date)
        if not preferences:
            # TODO Lambda return value
            return
        # Create CourtReserve

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
