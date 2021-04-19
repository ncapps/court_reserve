""" Handler for court reserve spider
"""
from os import getenv

from scrapy.crawler import CrawlerProcess
from spider import CourtReserveSpider
from helpers import today_offset
import settings


def main():
    """CLI entry point"""
    reserve_court()


def reserve_court():
    """Run Court Reserve Spider"""
    _settings = settings.SETTINGS.copy()
    _settings["ORG_ID"] = getenv("ORG_ID")
    _settings["USERNAME"] = getenv("USERNAME")
    _settings["PASSWORD"] = getenv("PASSWORD")
    _settings["RESERVE_DATE"] = today_offset(settings.SETTINGS.get("DAY_OFFSET", 0))

    process = CrawlerProcess(settings=_settings)
    process.crawl(CourtReserveSpider)
    process.start()


if __name__ == "__main__":
    main()
