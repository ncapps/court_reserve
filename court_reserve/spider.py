""" Reserve tennis court time using Scrapy
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
    get_http_headers,
    get_booking_date,
    get_bookings_body,
    get_bookings_by_court,
    get_day_preferences,
    find_open_court,
)

# override loaded values with environment variables
CONFIG = {**dotenv_values(".env"), **os.environ}
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
            url=f"{BASE_URL}/Account/LogIn/{CONFIG['ORG_ID']}",
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

        if path == "account/login":
            # Retry login once
            if cb_kwargs["login_attempts"] < 2:
                cb_kwargs["login_attempts"] += 1
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

        if path == "portal/index":
            self.logger.debug("Login success")
            # Get session id from portal page
            bookings_path = response.css("li.sub-menu-li a").attrib["href"]
            cb_kwargs["session_id"] = re.search("sId=([0-9]+)", bookings_path).group(1)
            self.logger.debug(f"Session id: {cb_kwargs['session_id']}")

            headers = get_http_headers(CONFIG["ORG_ID"], cb_kwargs["session_id"])
            self.logger.debug(f"Request headers: {headers}")

            cb_kwargs["booking_date"] = get_booking_date(
                int(self.settings["DAYS_OFFSET"]), self.settings["TIMEZONE"]
            )
            self.logger.debug(f"Booking date: {cb_kwargs['booking_date']}")

            court_ids = ",".join([str(x) for x in self.settings["COURTS"].keys()])
            body = get_bookings_body(
                CONFIG["ORG_ID"],
                cb_kwargs["booking_date"],
                cb_kwargs["session_id"],
                CONFIG["MEMBER_ID1"],
                self.settings["TIMEZONE"],
                CONFIG["COST_TYPE_ID"],
                court_ids,
            )
            self.logger.debug(f"Request body: {body}")

            return Request(
                url=f"{BASE_URL}/Reservations/ReadExpanded/{CONFIG['ORG_ID']}",
                method="POST",
                headers=headers,
                body=f"jsonData={body}",
                cb_kwargs=cb_kwargs,
            )

        if path == "reservations/readexpanded":
            json_response = json.loads(response.text)
            self.logger.debug(f'Found {json_response["Total"]} existing reservations')

            bookings = get_bookings_by_court(
                json_response["Data"], self.settings["TIMEZONE"]
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
            self.logger.debug(
                f"{open_court[0]} is open "
                f'from {open_court[1].strftime("%I:%M %p")} '
                f'to {open_court[2].strftime("%I:%M %p")}'
            )
            if not open_court:
                raise CloseSpider("Open court not found.")

        return None

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
