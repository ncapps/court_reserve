""" Reserve court time using a Scrapy spider
"""
import re
import json

from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider
from helpers import bookings_request_headers, bookings_request_body


class CourtReserveSpider(Spider):
    """Reserve a tennis court based on availability and user time and court
    preferences.
    """

    name = "courtreserve"

    def start_requests(self):
        """Returns request to login page.
        It is called by Scrapy when the spider is opened for scraping. Scrapy
        calls it only once.

        Args:
            None

        Returns:
            Request to login page.
        """
        org_id = self.settings.get("ORG_ID")

        return [
            Request(
                url=f"https://app.courtreserve.com/Online/Account/LogIn/{org_id}",
                callback=self.login,
            )
        ]

    def login(self, response):
        """Simulate a user login

        Args:
            response: A scrapy Response object for the login page.

        Returns:
            Request to login form
        """
        user = self.settings.get("USERNAME")
        pwd = self.settings.get("PASSWORD")

        return FormRequest.from_response(
            response,
            formid="loginForm",
            formdata={"UserNameOrEmail": user, "Password": pwd},
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
        org_id = self.settings.get("ORG_ID")

        # Login success is redirected to portal home
        if response.url == f"https://app.courtreserve.com/Online/Portal/Index/{org_id}":
            self.logger.debug("Login success.")
            # Get session id
            bookings_path = response.css("li.sub-menu-li a").attrib["href"]
            self.session_id = re.search("sId=([0-9]+)", bookings_path).group(1)

            return Request(
                url=f"https://app.courtreserve.com/Online/Reservations/Bookings/{org_id}?sId={self.session_id}",
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
        org_id = self.settings.get("ORG_ID")
        reserve_date = self.settings.get("RESERVE_DATE")
        member_id = self.settings.get("MEMBER_IDS")[0]

        headers = bookings_request_headers(org_id, self.session_id)
        body = bookings_request_body(org_id, reserve_date, self.session_id, member_id)

        yield Request(
            url=f"https://app.courtreserve.com/Online/Reservations/ReadExpanded/{org_id}",
            method="POST",
            headers=headers,
            body=f"jsonData={body}",
            callback=self.parse_bookings,
        )

    def parse_bookings(self, response):
        reserve_date = self.settings.get("RESERVE_DATE")

        json_response = json.loads(response.text)
        print(
            f'{json_response["Total"]} bookings found on {reserve_date.strftime("%A, %b %d")}'
        )
