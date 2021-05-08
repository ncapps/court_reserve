#!/usr/bin/env python3
""" CourtReserveSpider runner
"""
import json
import os
from copy import deepcopy

from scrapy.crawler import CrawlerProcess
from botocore.exceptions import ClientError

from spider import CourtReserveSpider
from secrets_manager import get_secret


# Load environment variables
CONFIG = {**os.environ}


def handler(event, context):
    """Reserve a tennis court

    Args:
        event (dict): Event object
        context (dict): Context object

    Return:
        (dict)
    """

    # Get secret from secrets manager
    try:
        secret = json.loads(get_secret(CONFIG["SECRET_ID"]))
    except ClientError as err:
        raise err

    # Add environment variables to spider settings
    settings = deepcopy(secret)
    for key in ["DRY_RUN", "DAYS_OFFSET", "LOG_LEVEL", "LOCAL_TIMEZONE"]:
        settings[key] = CONFIG[key]

    process = CrawlerProcess(settings=settings)
    process.crawl(CourtReserveSpider)
    process.start()


def main():
    """Use for local execution"""
    handler({}, {})


if __name__ == "__main__":
    main()
