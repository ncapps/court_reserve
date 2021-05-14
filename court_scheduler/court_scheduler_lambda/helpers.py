""" court scheduler lambda helpers
"""
import logging
import logging.config
from datetime import datetime, timedelta

from dateutil import tz
import boto3
from botocore.exceptions import ClientError

logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def get_secret_value(secret_id: str) -> str:
    """Returns Secrets Manager secret

    Args:
        secret_id (str): AWS secrets manager ecret id

    Returns:
        (str) Secret string

    Throws:
        (ClientError)
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_id)
    except ClientError as err:
        raise err
    else:
        if "SecretString" in get_secret_value_response:
            return get_secret_value_response["SecretString"]


def offset_today(offset=0, tz_name=""):
    """Returns the date offset from today

    Args:
        offset (int): Number of days from current date to booking date
        tz_name (str): IANA time zone name
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    Returns:
        Returns a datetime object
    """
    tz_obj = tz.gettz(tz_name) if tz_name else tz.tzlocal()
    days_offset = timedelta(days=+int(offset))
    return datetime.now(tz=tz_obj) + days_offset


def court_preferences(preferences, booking_date):
    """Returns a list of court and time preferences for the given booking date

    Args:
        schedule (dict): Booking time and court ordered by preference for each day
                            of the week. Example:
                {
                    "monday": {
                        "start_end_times": [["6:30 PM","8:00 PM"],["7:00 PM","8:00 PM"]],
                        "court_ids": ["123","456",]
                    }
                }
        booking_date (datetime): Datetime to reserve a court

    Returns:
        (list) List of court and booking time ordered by preference for the booking date
    """

    def str_to_date(hour_min):
        _dt = datetime.strptime(hour_min, "%I:%M %p")
        return booking_date.replace(
            hour=_dt.hour, minute=_dt.minute, second=0, microsecond=0
        )

    weekday_name = booking_date.strftime("%A").lower()
    if not preferences.get(weekday_name, None):
        logger.info("Preferences not found for %s", weekday_name)
        return []

    prefs = [
        (court_id, (str_to_date(start), str_to_date(end)))
        for start, end in preferences[weekday_name]["start_end_times"]
        for court_id in preferences[weekday_name]["court_ids"]
    ]
    logger.info("Found %s preferences for %s", len(prefs), weekday_name)
    return prefs
