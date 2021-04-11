from os import getenv
import pprint

from dotenv import load_dotenv
from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider

# Load environment variables from .env
load_dotenv()
ORG_ID = getenv("ORGANIZATION_ID")
USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")

REQUEST_KWARGS = {
    "method": "POST",
    "url": f"https://app.courtreserve.com/Online/Reservations/ReadExpanded/{ORG_ID}",
    "headers": [
        ("authority", "app.courtreserve.com"),
        (
            "sec-ch-ua",
            '"Google Chrome";v="89", "Chromium";v="89", ";Not A ' 'Brand";v="99"x',
        ),
        ("accept", "*/*"),
        ("x-requested-with", "XMLHttpRequest"),
        ("sec-ch-ua-mobile", "?0"),
        (
            "user-agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 "
            "Safari/537.36",
        ),
        ("content-type", "application/x-www-form-urlencoded; charset=UTF-8"),
        ("origin", "https://app.courtreserve.com"),
        ("sec-fetch-site", "same-origin"),
        ("sec-fetch-mode", "cors"),
        ("sec-fetch-dest", "empty"),
        (
            "referer",
            "https://app.courtreserve.com/Online/Reservations/Bookings/6801?sId=797",
        ),
        ("accept-language", "en-US,en;q=0.9"),
    ],
    "body": "sort=&group=&filter=&jsonData=%7B%22startDate%22%3A%222021-04-11T07%3A00%3A00.000Z%22%2C%22end%22%3A%222021-04-11T07%3A00%3A00.000Z%22%2C%22orgId%22%3A%226801%22%2C%22TimeZone%22%3A%22America%2FLos_Angeles%22%2C%22Date%22%3A%22Sun%2C+11+Apr+2021+07%3A00%3A00+GMT%22%2C%22KendoDate%22%3A%7B%22Year%22%3A2021%2C%22Month%22%3A4%2C%22Day%22%3A11%7D%2C%22UiCulture%22%3A%22en-US%22%2C%22CostTypeId%22%3A%2286377%22%2C%22CustomSchedulerId%22%3A%22797%22%2C%22ReservationMinInterval%22%3A%2260%22%2C%22SelectedCourtIds%22%3A%2214609%2C14610%2C14611%2C14612%2C14613%2C14614%2C14615%2C14616%2C14617%22%2C%22MemberIds%22%3A%22404752%22%2C%22MemberFamilyId%22%3A%22%22%7D",
}


class CourtReserveSpider(Spider):
    name = "courtreserve"
    allowed_domains = ["app.courtreserve.com"]
    domain = "https://app.courtreserve.com"

    def __init__(
        self, category=None, org_id="", username="", password="", *args, **kwargs
    ):
        """Initializer for CourtReserveSpider class

        Args:
            org_id: (str) Organization ID. Overrides ORG_ID environment variable.
            username: (str) Username for login. Overrides USERNAME environment variable.
            password: (str) Password for login. Overrides PASSWORD environment variable.
        """
        super(CourtReserveSpider, self).__init__(*args, **kwargs)

        self.org_id = org_id or ORG_ID
        self.username = username or USERNAME
        self.password = password or PASSWORD

    def start_requests(self):
        """Returns request to login page.
        It is called by Scrapy when the spider is opened for scraping. Scrapy
        calls it only once.

        Args:
            None

        Returns:
            Request to login page.
        """
        yield Request(f"{self.domain}/Online/Account/LogIn/{self.org_id}", self.login)

    def login(self, response):
        """Simulate a user login

        Args:
            response: A scrapy Response object for the login page.

        Returns:
            Request to login form
        """
        return FormRequest.from_response(
            response,
            formid="loginForm",
            formdata={"UserNameOrEmail": self.username, "Password": self.password},
            clickdata={"type": "button", "onclick": "submitLoginForm()"},
            callback=self.verify_login,
        )

    def verify_login(self, response):
        """Checks login result.
        A successful login request is expected to redirect to the
        Online/Portal/Index/ path.

        Args:
            response: A scrapy Response object for a HTTP POST request
                        to the login form.

        Returns:
            Request to bookings page

        Raises:
            CloseSpider: Stop spider if login is not successful.
        """
        # Login success is redirected to portal home
        if response.url == f"{self.domain}/Online/Portal/Index/{self.org_id}":
            yield Request(
                f"{self.domain}/Online/Reservations/Bookings/{self.org_id}",
                self.get_reservations,
            )
        else:
            self.logger.error("Login failed. Check username and password.")
            raise CloseSpider("Failed to login")

    def get_reservations(self, response):
        yield Request(**REQUEST_KWARGS, callback=self.parse_reservations)

    def parse_reservations(self, response):
        print(f"STATUS: {response.status}")
        pprint.pp(response.text)
