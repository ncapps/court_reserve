from os import getenv
from dotenv import load_dotenv
from scrapy import Spider

# Load environment variables from .env
load_dotenv()
ORG_ID = getenv("ORGANIZATION_ID")


class CourtReserveSpider(Spider):
    name = "courtreserve"
    allowed_domains = ["app.courtreserve.com"]
    start_urls = [f"https://app.courtreserve.com/Online/Portal/Index/{ORG_ID}"]

    def parse(self, response):
        print("\n")
        print("HTTP STATUS: " + str(response.status))
        print(response.css("h3::text").get())
        print("\n")
