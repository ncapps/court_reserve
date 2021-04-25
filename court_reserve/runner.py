#!/usr/bin/env python3
""" CourtReserveSpider runner
"""
import os
import io
import json
import argparse

from scrapy.crawler import CrawlerProcess
from spider import CourtReserveSpider


def get_args():
    """Get command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Reserve a tennis court",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "settings", metavar="settings", type=str, help="Settings string or file"
    )

    args = parser.parse_args()
    if os.path.isfile(args.settings):
        with open(args.settings) as input_file:
            args.settings = json.load(input_file)
    else:
        args.settings = json.load(io.StringIO(args.settings))

    return args


def main():
    """Main function for CLI

    Args:
        None

    Returns:
        None
    """
    args = get_args()
    run_crawler(args.settings)


def run_crawler(settings):
    """Run CourtReserveSpider
    Args:
        settings (dict): CourtReserveSpider settings
    Returns:
        None
    """
    process = CrawlerProcess(settings)
    process.crawl(CourtReserveSpider)
    process.start()


if __name__ == "__main__":
    main()
