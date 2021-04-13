import re
from datetime import date, timedelta
from os import getenv
import json

from dotenv import load_dotenv
from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider

# Load environment variables from .env
load_dotenv()
ORG_ID = getenv("ORGANIZATION_ID")
USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")
DATE_OFFSET = getenv("DATE_OFFSET")
MEMBER_ID1 = getenv("MEMBER_ID1")


def get_date_offset(date, offset=0):
    """Returns the date offset

    Args:
        date: A datetime date.
        offset: (int) Offset in days.

    Returns:
        Returns A datetime date with offset.
    """
    # Use -8 for UTC to PST offset. This does not consider day light savings.
    return date + timedelta(hours=-8, days=int(offset))


class CourtReserveSpider(Spider):
    name = "courtreserve"
    allowed_domains = ["app.courtreserve.com"]
    domain = "https://app.courtreserve.com"

    def __init__(
        self,
        category=None,
        org_id="",
        username="",
        password="",
        date_offset=0,
        *args,
        **kwargs,
    ):
        """Initializer for CourtReserveSpider class

        Args:
            org_id: (str) Organization ID. Overrides ORG_ID environment variable.
            username: (str) Username for login. Overrides USERNAME environment variable.
            password: (str) Password for login. Overrides PASSWORD environment variable.
            date_offset: (int) Number of days offset from current date to create reservatiion.
        """
        super(CourtReserveSpider, self).__init__(*args, **kwargs)

        self.org_id = org_id or ORG_ID
        self.username = username or USERNAME
        self.password = password or PASSWORD
        self.date_offset = date_offset or DATE_OFFSET or 0
        self.date = get_date_offset(date.today(), self.date_offset)
        self.session_id = 0

    def start_requests(self):
        """Returns request to login page.
        It is called by Scrapy when the spider is opened for scraping. Scrapy
        calls it only once.

        Args:
            None

        Returns:
            Request to login page.
        """
        yield Request(
            url=f"{self.domain}/Online/Account/LogIn/{self.org_id}", callback=self.login
        )

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
        A successful login request is expected to redirect
        to Online/Portal/Index/.

        Args:
            response: A scrapy Response object for a HTTP POST request
                        to the login form.

        Returns:
            Request for bookings page

        Raises:
            CloseSpider: Stop spider if login is not successful.
        """
        # Login success is redirected to portal home
        if response.url == f"{self.domain}/Online/Portal/Index/{self.org_id}":
            self.logger.debug("Login success.")
            # Get session id
            bookings_path = response.css("li.sub-menu-li a").attrib["href"]
            self.session_id = re.search("sId=([0-9]+)", bookings_path).group(1)
            yield Request(
                url=f"{self.domain}/Online/Reservations/Bookings/{self.org_id}?sId={self.session_id}",
                callback=self.get_bookings,
            )
        else:
            self.logger.error("Login failed. Check username and password.")
            raise CloseSpider("Failed to login")

    def get_bookings(self, response):
        """Returns a request for bookings for a given day

        Args:
            response: A scrapy Response object for the bookings page

        Returns:
            Request for bookings
        """
        headers = self.make_bookings_request_headers()
        body = self.make_bookings_request_body()
        yield Request(
            url=f"{self.domain}/Online/Reservations/ReadExpanded/{self.org_id}",
            method="POST",
            headers=headers,
            body=f"jsonData={body}",
            callback=self.parse_bookings,
        )

    def parse_bookings(self, response):
        json_response = json.loads(response.text)
        print(
            f'{json_response["Total"]} bookings found on {self.date.strftime("%A, %b %d")}'
        )

    def make_bookings_request_headers(self):
        return [
            ("authority", "app.courtreserve.com"),
            ("origin", self.domain),
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
            (
                "referer",
                f"{self.domain}/Online/Reservations/Bookings/{self.org_id}?sId={self.session_id}",
            ),
            ("content-type", "application/x-www-form-urlencoded; charset=UTF-8"),
            ("sec-fetch-site", "same-origin"),
            ("sec-fetch-mode", "cors"),
            ("sec-fetch-dest", "empty"),
            ("accept-language", "en-US,en;q=0.9"),
        ]

    def make_bookings_request_body(self):
        """Returns HTTP request body for bookings request

        Args:
            None
        Returns:
            A dictionary containing bookings request body
        """
        return {
            "startDate": f"{self.date}T07:00:00.000Z",
            "end": f"{self.date}T07:00:00.000Z",
            "orgId": self.org_id,
            "TimeZone": "America/Los_Angeles",
            "Date": (
                f"{self.date.strftime('%a')},"
                f"+{self.date.day}"
                f"+{self.date.strftime('%b')}"
                f"+{self.date.year}"
                f"+07:00:00+GMT"
            ),
            "KendoDate": {
                "Year": self.date.year,
                "Month": self.date.month,
                "Day": self.date.day,
            },
            "UiCulture": "en-US",
            "CostTypeId": "86377",
            "CustomSchedulerId": f"{self.session_id}",
            "ReservationMinInterval": "60",
            "SelectedCourtIds": "14609,14610,14611,14612,14613,14614,14615,14616,14617",
            "MemberIds": MEMBER_ID1,
            "MemberFamilyId": "",
        }
