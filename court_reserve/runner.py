""" CourtReserveSpider runner
"""
import json

from scrapy.crawler import CrawlerProcess
from spider import CourtReserveSpider


def main():
    """Run CourtReserveSpider

    Args:
        None

    Returns:
        None
    """
    with open("settings.json", "r") as settings_file:
        settings = json.load(settings_file)

    process = CrawlerProcess(settings=settings)
    process.crawl(CourtReserveSpider)
    process.start()


if __name__ == "__main__":
    main()
