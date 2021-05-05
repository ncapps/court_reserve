""" Reserve tennis court time using Scrapy
"""
import re
import json
from urllib.parse import quote

from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider

from helpers import (
    get_http_headers,
    get_booking_date,
    get_bookings_body,
    get_bookings_by_court,
    get_day_preferences,
    find_open_court,
    get_create_booking_body,
)

BASE_URL = "https://app.courtreserve.com/Online"


class CourtReserveSpider(Spider):
    """Reserve a tennis court"""

    name = "courtreserve"

    def start_requests(self):
        """Returns request to login page.

        Args:
            None

        Returns:
            Request to login page.
        """
        cb_kwargs = {"login_attempts": 0}
        yield Request(
            url=f"{BASE_URL}/Account/LogIn/{self.settings['ORG_ID']}",
            cb_kwargs=cb_kwargs,
        )

    def parse(self, response, **kwargs):
        """Default callback for Scrapy responses

        Args:
            response: Scrapy response object

        Returns:
            Scrapy request object or None
        """
        cb_kwargs = response.cb_kwargs.copy()
        re_pattern = r"^https://app.courtreserve.com/Online/([A-Za-z]+[/]?[A-Za-z]+)"
        path = re.search(re_pattern, response.url).group(1).lower()
        self.logger.debug(f"Response path: {path}")

        # 1) Login to app
        if path == "account/login":
            # Retry login once
            if cb_kwargs["login_attempts"] < 2:
                cb_kwargs["login_attempts"] += 1
                return FormRequest.from_response(
                    response,
                    formid="loginForm",
                    formdata={
                        "UserNameOrEmail": self.settings["USERNAME"],
                        "Password": self.settings["PASSWORD"],
                    },
                    clickdata={"type": "button", "onclick": "submitLoginForm()"},
                    cb_kwargs=cb_kwargs,
                )

            self.logger.error("Login failed. Check username and password.")
            raise CloseSpider("Failed to login")

        # 2) Get existing court reservations
        if path == "portal/index":
            self.logger.debug("Login success")
            # Get session id from portal page
            bookings_path = response.css("li.sub-menu-li a").attrib["href"]
            cb_kwargs["session_id"] = re.search("sId=([0-9]+)", bookings_path).group(1)
            self.logger.debug(f"Session id: {cb_kwargs['session_id']}")

            cb_kwargs["headers"] = get_http_headers(
                self.settings["ORG_ID"], cb_kwargs["session_id"]
            )
            self.logger.debug(f"Request headers: {cb_kwargs['headers']}")

            cb_kwargs["booking_date"] = get_booking_date(
                int(self.settings["DAYS_OFFSET"]), self.settings["LOCAL_TIMEZONE"]
            )
            self.logger.debug(f"Booking date: {cb_kwargs['booking_date']}")

            court_ids = ",".join([str(x) for x in self.settings["COURTS"].keys()])
            body = get_bookings_body(
                self.settings["ORG_ID"],
                cb_kwargs["booking_date"],
                cb_kwargs["session_id"],
                self.settings["MEMBER_ID1"],
                self.settings["LOCAL_TIMEZONE"],
                self.settings["COST_TYPE_ID"],
                court_ids,
            )
            self.logger.debug(f"Request body: {body}")

            return Request(
                url=f"{BASE_URL}/Reservations/ReadExpanded/{self.settings['ORG_ID']}",
                method="POST",
                headers=cb_kwargs["headers"],
                body=f"jsonData={body}",
                cb_kwargs=cb_kwargs,
            )

        # 3) Find open court
        if path == "reservations/readexpanded":
            json_response = json.loads(response.text)
            self.logger.debug(f'Found {json_response["Total"]} existing reservations')

            bookings = get_bookings_by_court(
                json_response["Data"], self.settings["LOCAL_TIMEZONE"]
            )
            self.logger.debug(f"Summarized bookings: {bookings}")

            # Get court and time preferences from settings
            try:
                preferences = get_day_preferences(
                    self.settings["PREFERENCES"], cb_kwargs["booking_date"]
                )
                self.logger.debug(f"Day preferences: {preferences}")
            except KeyError as err:
                raise CloseSpider("Day preferences not found. Check settings.") from err

            # Find open court
            open_court = find_open_court(bookings, preferences)
            if not open_court:
                raise CloseSpider("Open court not found.")

            cb_kwargs["open_court"] = open_court
            court_id, start, end = open_court
            court_label = self.settings["COURTS"][court_id]
            self.logger.debug(
                f"{court_label} is open "
                f'from {start.strftime("%I:%M %p")} '
                f'to {end.strftime("%I:%M %p")}'
            )
            return Request(
                url=(
                    f"{BASE_URL}/Reservations/CreateReservationCourtsview/"
                    f"{self.settings['ORG_ID']}?"
                    f"start={start.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)')}&"
                    f"end={end.strftime('%a %b %d %Y %H:%M:%S GMT%z (%Z)')}&"
                    f"courtLabel={quote(court_label)}&"
                    f"customSchedulerId={cb_kwargs['session_id']}"
                ),
                method="GET",
                headers=cb_kwargs["headers"],
                cb_kwargs=cb_kwargs,
            )

        # 4) Reserve a court
        if path == "reservations/createreservationcourtsview":
            try:
                token = response.css("#createReservation-Form input").attrib["value"]
                self.logger.debug(f"Verification Token: {token}")
            except KeyError as err:
                raise CloseSpider("Unable to create reservation") from err

            # Make request body string
            court_id, start, end = cb_kwargs["open_court"]
            body = get_create_booking_body(
                session_id=cb_kwargs["session_id"],
                token=token,
                start_time=start,
                court_id=court_id,
                **self.settings,
            )
            self.logger.debug(f"Request body: {body}")

            if self.settings["DRY_RUN"].lower() == "true":
                raise CloseSpider("Dry run enabled: Skipping reservation creation")
            return Request(
                url=f"{BASE_URL}/Reservations/CreateReservation/{self.settings['ORG_ID']}",
                method="POST",
                headers=cb_kwargs["headers"],
                body=body,
                cb_kwargs=cb_kwargs,
            )

        # 5) Confirm court reservation
        if path == "reservations/createreservation":
            json_response = json.loads(response.text)
            self.logger.debug(f"Create reservation response: {json_response}")
            try:
                assert json_response["isValid"]
            except AssertionError as err:
                raise CloseSpider(
                    f"Failed to create reservation: {json_response.get('message')}"
                ) from err
