#!/usr/bin/env python3
""" CourtReserveSpider runner
"""
import json
from pathlib import Path
import os

from dotenv import dotenv_values
from scrapy.crawler import CrawlerProcess
from botocore.exceptions import ClientError

from spider import CourtReserveSpider
from secrets_manager import get_secret


# override loaded values with environment variables
CONFIG = {**dotenv_values(".env"), **os.environ}


def lambda_handler(event, context):
    """Reserve a tennis court

    Args:
        event (dict): Event object
        context (dict): Context object

    Return:
        (dict)
    """
    downloads_path = Path("downloads/")
    downloads_path.mkdir(parents=True, exist_ok=True)
    filepath = downloads_path / CONFIG["SECRET_FILE"]

    try:
        if filepath.exists():
            print("Loading secret from file")
            with filepath.open() as secret_file:
                secret = json.load(secret_file)
        else:
            print("Get secret from secrets manager")
            secret = json.loads(get_secret(CONFIG["SECRET_NAME"]))
            if CONFIG.get("ENVIRONMENT").lower() == "dev":
                # Cache secret in file
                with filepath.open(mode="w") as secret_file:
                    json.dump(secret, secret_file)

    except KeyError as err:
        raise err
    except ClientError as err:
        raise err

    print(f"TYPE: {type(secret)}")
    print(secret)
    process = CrawlerProcess(settings=secret)
    process.crawl(CourtReserveSpider)
    process.start()


def main():
    """Use for local execution"""
    lambda_handler({}, {})


if __name__ == "__main__":
    main()
