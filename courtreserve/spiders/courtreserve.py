from os import getenv

from dotenv import load_dotenv
from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider

# Load environment variables from .env
load_dotenv()
ORG_ID = getenv("ORGANIZATION_ID")
USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")
LOGIN_URL = f"https://app.courtreserve.com/Online/Account/LogIn/{ORG_ID}"


class CourtReserveSpider(Spider):
    name = "courtreserve"
    allowed_domains = ["app.courtreserve.com"]

    def start_requests(self):
        yield Request(LOGIN_URL, self.login)

    def login(self, response):
        return FormRequest.from_response(
            response,
            formid="loginForm",
            formdata={"UserNameOrEmail": USERNAME, "Password": PASSWORD},
            clickdata={"type": "button", "onclick": "submitLoginForm()"},
            callback=self.check_login_result,
        )

    def check_login_result(self, response):
        # Redirection to portal home is expected on successful login
        if response.url == LOGIN_URL:
            self.logger.error("Login failed. Check username and password.")
            raise CloseSpider("Failed to login")
        else:
            print("\n")
            print("HTTP STATUS: " + str(response.status))
            print(f"Response from: {response.url}")
            print(response.css("h3::text").get())
            print("\n")
