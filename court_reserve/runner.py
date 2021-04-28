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
        "config", metavar="config", type=str, help="Configuration string or file"
    )

    args = parser.parse_args()
    if os.path.isfile(args.config):
        with open(args.config) as config_file:
            args.config = json.load(config_file)
    else:
        args.config = json.load(io.StringIO(args.config))

    return args


def main():
    """Get CLI args and start Scrapy crawler

    Args:
        None

    Returns:
        None
    """
    args = get_args()
    run_crawler(args.config)


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
