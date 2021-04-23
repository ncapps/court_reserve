""" Handler for court reserve spider
"""
from os import getenv
from copy import deepcopy

from scrapy.crawler import CrawlerProcess
from spider import CourtReserveSpider
from helpers import today_offset
from settings import SETTINGS


def main():
    """CLI entry point"""
    reserve_court()


def reserve_court():
    """Run Court Reserve Spider"""
    settings = deepcopy(SETTINGS)

    # Get reserve date using offset
    settings["RESERVE_DATE"] = today_offset(settings.get("DAY_OFFSET", 0))

    # TODO get secrets from secrets manager
    settings["ORG_ID"] = getenv("ORG_ID")
    settings["USERNAME"] = getenv("USERNAME")
    settings["PASSWORD"] = getenv("PASSWORD")
    settings["MEMBER_IDS"] = getenv("MEMBER_IDS").split(",")

    process = CrawlerProcess(settings=settings)
    process.crawl(CourtReserveSpider)
    process.start()


if __name__ == "__main__":
    main()
