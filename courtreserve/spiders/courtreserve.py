from os import getenv
from dotenv import load_dotenv
from scrapy import Spider, FormRequest

# Load environment variables from .env
load_dotenv()
ORG_ID = getenv("ORGANIZATION_ID")
USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")


class CourtReserveSpider(Spider):
    name = "courtreserve"
    allowed_domains = ["app.courtreserve.com"]
    start_urls = [f"https://app.courtreserve.com/Online/Account/LogIn/{ORG_ID}"]

    def parse(self, response):
        return FormRequest.from_response(
            response,
            formid="loginForm",
            formdata={"UserNameOrEmail": USERNAME, "Password": PASSWORD},
            clickdata={"type": "button", "onclick": "submitLoginForm()"},
            callback=self.after_login,
        )

    def after_login(self, response):
        print("\n")
        print("HTTP STATUS: " + str(response.status))
        print(response.css("h3::text").get())
        print("\n")
