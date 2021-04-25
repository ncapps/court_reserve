""" Reserve court time using a Scrapy spider
"""
import re
import json
import os
from collections import defaultdict
from time import strptime, strftime, localtime
from pprint import pp

from scrapy import Spider, Request, FormRequest
from scrapy.exceptions import CloseSpider
from dotenv import dotenv_values
from helpers import (
    request_headers,
    get_reservations_body,
    merge_booking_ranges,
    get_available_court,
)

# override loaded values with environment variables
CONFIG = {**dotenv_values(".env"), **os.environ}


class CourtReserveSpider(Spider):
    """Reserve a tennis court"""

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
        cb_kwargs = {"login_count": 0}
        yield Request(
            url=f"https://app.courtreserve.com/Online/Account/LogIn/{CONFIG['ORG_ID']}",
            cb_kwargs=cb_kwargs,
        )

    def parse(self, response, **kwargs):
        """Default callback for Scrapy response

        Args:
            response: Scrapy response object

        Returns:
            Scrapy request object
        """
        cb_kwargs = response.cb_kwargs.copy()
        re_pattern = r"^https://app.courtreserve.com/Online/([A-Za-z]*)"
        path = re.search(re_pattern, response.url).group(1).lower()
        self.logger.debug(f"Response path: {path}")

        if path == "account":
            # Retry login once
            if cb_kwargs["login_count"] < 2:
                cb_kwargs["login_count"] += 1
                return FormRequest.from_response(
                    response,
                    formid="loginForm",
                    formdata={
                        "UserNameOrEmail": CONFIG["USERNAME"],
                        "Password": CONFIG["PASSWORD"],
                    },
                    clickdata={"type": "button", "onclick": "submitLoginForm()"},
                    cb_kwargs=cb_kwargs,
                )

            self.logger.error("Login failed. Check username and password.")
            raise CloseSpider("Failed to login")

        if path == "portal":
            self.logger.debug("Login success")

        return None

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
        reserve_date = self.settings.get("BOOKING_DATE")
        member_id = self.settings.get("MEMBER_IDS")[0]

        headers = request_headers(org_id, self.session_id)
        body = get_reservations_body(org_id, reserve_date, self.session_id, member_id)

        yield Request(
            url=f"https://app.courtreserve.com/Online/Reservations/ReadExpanded/{org_id}",
            method="POST",
            headers=headers,
            body=f"jsonData={body}",
            callback=self.parse_bookings,
        )

    def parse_bookings(self, response):
        reserve_date = self.settings.get("BOOKING_DATE")

        json_response = json.loads(response.text)
        self.logger.info(
            f'Found {json_response["Total"]} bookings on {strftime("%A, %b %d", reserve_date)}'
        )

        time_re = re.compile("[0-9]+")
        # Create dict of end time keys with list of court ids value
        bookings_by_court = defaultdict(list)
        for booking in json_response["Data"]:
            court_id = str(booking["CourtId"])
            start_time = localtime(
                int(time_re.search(booking["Start"]).group(0)) / 1000
            )
            end_time = localtime(int(time_re.search(booking["End"]).group(0)) / 1000)
            bookings_by_court[court_id].append((start_time, end_time))

        for cid, bookings in bookings_by_court.items():
            bookings_by_court[cid] = merge_booking_ranges(bookings)
        self.logger.debug(bookings_by_court)

        # Get settings for a given day
        day_name = strftime("%A", reserve_date).lower()
        reserve_day_schedule = self.settings.get("SCHEDULE").get(day_name)

        # Get list of requesting times and court
        if reserve_day_schedule:
            reserve_requests = [
                (
                    (
                        strptime(start_end[0], "%I:%M %p"),
                        strptime(start_end[1], "%I:%M %p"),
                    ),
                    cid,
                )
                for start_end in reserve_day_schedule["request_times"]
                for cid in reserve_day_schedule["court_ids"]
            ]

        else:

            self.logger.error(f'Schedule not found for "{day_name}". Check settings.')
            raise CloseSpider(f"No schedule for {day_name}")

        # Find court availability
        open_court = get_available_court(bookings_by_court, reserve_requests)
        if open_court:
            court_label = self.settings.get("COURT_LABEL").get(open_court["court_id"])
            self.logger.info(
                f"{court_label} is open "
                f'from {strftime("%I:%M %p", open_court["start_end"][0])} '
                f'to {strftime("%I:%M %p", open_court["start_end"][1])}'
            )
            # "start=Thu%20Apr%2022%202021%2019:00:00%20GMT-0700%20(Pacific%20Daylight%20Time)&"
            # "end=Thu%20Apr%2022%202021%2019:30:00%20GMT-0700%20(Pacific%20Daylight%20Time)&"
            request_url = (
                "https://app.courtreserve.com/Online/Reservations/CreateReservationCourtsview/"
                f'{self.settings.get("ORG_ID")}?'
                f'start={strftime("%a %b %Y %H:%M:%S %z (%Z)", open_court["start_end"][0])}&'
                f'end={strftime("%a %b %Y %H:%M:%S %z (%Z)", open_court["start_end"][1])}&'
                f"courtLabel={court_label}&"
                f"customSchedulerId={self.session_id}"
            )
            pp(request_url)
            # return Request(url=request_url)

        else:
            self.logger.info("Open court not found")
            raise CloseSpider("Open court not found")
