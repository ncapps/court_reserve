""" app.court.reserve.com adapter
"""
from collections import defaultdict
import logging
import logging.config
import re
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import tz

logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class CourtReserveAdapter:
    """Interfaces with app.courtreserve.com"""

    def __init__(
        self,
        org_id: str,
        username: str,
        password: str,
    ) -> None:
        """
        Args:
            org_id (str): Organization id
            username (str): username
            password (str): password

        Returns:
            None

        Raises:
            TBD
        """
        self.org_id = org_id
        self.session_id = None
        self.http_headers = None
        self.session = requests.Session()
        if org_id and username and password:
            self._login(username, password)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Sends HTTP requests

        Args:
            method (str): HTTP method. Example values: GET, POST
            path (str): path of the URL

        Returns:
            Response object

        Raises:
            AssertionError
        """
        request = requests.Request(
            method.upper(), f"https://app.courtreserve.com/Online/{path}", **kwargs
        )
        prepped = self.session.prepare_request(request)
        return self.session.send(prepped)

    def _login(self, username: str, password: str) -> None:
        """Peform user login to app.courtreserve.com

        Args:
            username (str): Username
            password (str): Password

        Returns:
            None

        Raises:
            TBD
        """
        path = f"Account/Login/{self.org_id}"
        payload = {"UserNameOrEmail": username, "Password": password}
        token_name = "__RequestVerificationToken"

        # Add hidden __RequestVerificationToken to login request
        response = self._request("GET", path)
        payload[token_name] = (
            BeautifulSoup(response.text, "html.parser")
            .find(id="loginForm")
            .find(attrs={"name": token_name})
            .get("value")
        )

        response = self._request("POST", path, data=payload)
        # Expect redirect on successful login
        assert response.url.find("Account/Login") == -1, "Login attempt failed."

        # Get session id
        bookings_path = (
            BeautifulSoup(response.text, "html.parser")
            .select_one("li.sub-menu-li a")
            .get("href")
        )
        self.session_id = re.search("sId=([0-9]+)", bookings_path).group(1)
        logger.info("Found session id: %s", self.session_id)

        self.http_headers = {
            "authority": "app.courtreserve.com",
            "sec-ch-ua": (
                '"Google Chrome";v="89", "Chromium";v="89",' '";Not A ' 'Brand";v="99"x'
            ),
            "accept": "*/*",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 "
                "Safari/537.36"
            ),
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://app.courtreserve.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": (
                "https://app.courtreserve.com/Online/Reservations/Bookings/"
                f"{self.org_id}?sId={self.session_id}"
            ),
            "accept-language": "en-US,en;q=0.9",
        }

    def list_reservations(self, date: datetime) -> dict:
        """Returns existing reservations grouped by court

        Arg:
            date (datetime): Reservation date

        Returns:
            (dict) For each court, a list of start and end datetime the
                    court is reserved
        """
        # Get court selection criteria

        response = self._request(
            "GET", f"Reservations/Bookings/{self.org_id}?sId={self.session_id}"
        )
        pattern = re.compile(r"getSelectedCriteriasCourtsView\(\)")
        court_criteria = [
            str(script.string)
            for script in BeautifulSoup(response.text, "html.parser").select(
                "#wrapper div.content div.row div.col-lg-12 script"
            )
            if pattern.search(str(script.string)) is not None
        ][0]
        time_zone = re.search(r"TimeZone: '([A-Za-z_\/]+)'", court_criteria).group(1)
        cost_type_id = re.search("CostTypeId: '([0-9]+)'", court_criteria).group(1)
        court_ids = re.search("SelectedCourtIds: '([0-9,]+)'", court_criteria).group(1)
        member_id = re.search("MemberIds: '([0-9]+)'", court_criteria).group(1)

        payload = {
            "startDate": f"{date.strftime('%Y-%m-%d')}T07:00:00.000Z",
            "end": f"{date.strftime('%Y-%m-%d')}T07:00:00.000Z",
            "orgId": self.org_id,
            "TimeZone": time_zone,
            "Date": (
                f"{date.strftime('%a')},"
                f" {date.day}"
                f" {date.strftime('%b')}"
                f" {date.year}"
                f" 07:00:00 GMT"
            ),
            "KendoDate": {
                "Year": date.year,
                "Month": date.month,
                "Day": date.day,
            },
            "UiCulture": "en-US",
            "CostTypeId": cost_type_id,
            "CustomSchedulerId": self.session_id,
            "ReservationMinInterval": "60",
            "SelectedCourtIds": court_ids,
            "MemberIds": member_id,
            "MemberFamilyId": "",
        }

        response = self._request(
            "POST",
            f"Reservations/ReadExpanded/{self.org_id}",
            data=f"jsonData={payload}",
            headers=self.http_headers,
        )
        json_resp = json.loads(response.text)
        logger.info("Found %s reservations", json_resp["Total"])

        tz_obj = tz.obj = tz.gettz(time_zone)
        court_bookings = {"label_to_id": {}}
        epoch_re = re.compile("[0-9]+")
        # Get datetime objects from POSIX timestamp, grouped by court id
        for booking in json_resp["Data"]:
            court_label = str(booking["CourtLabel"])
            if not court_bookings.get(court_label):
                court_bookings[court_label] = []
            court_bookings[court_label].append(
                (
                    datetime.fromtimestamp(
                        int(epoch_re.search(booking["Start"]).group(0)) / 1000,
                        tz=tz_obj,
                    ),
                    datetime.fromtimestamp(
                        int(epoch_re.search(booking["End"]).group(0)) / 1000, tz=tz_obj
                    ),
                )
            )
            court_bookings["label_to_id"][court_label] = booking["CourtId"]

        # Merge contiguous reservations by court
        re_pattern = re.compile("Court #[0-9]+")
        for court_label, _bookings in court_bookings.items():
            if re_pattern.search(court_label):
                court_bookings[court_label] = self._merge_bookings(_bookings)

        return court_bookings

    @staticmethod
    def _merge_bookings(bookings: list) -> list:
        """Merge contiguous bookings

        Args:
            bookings (list): List of start and end times

        Returns:
            List of merged bookings
        """
        if not bookings:
            return bookings

        # Sort by start time
        bookings.sort(key=lambda x: x[0])
        merged_list = [(bookings[0])]

        for current_start_time, current_end_time in bookings[1:]:
            # check if the current start time is less than the end time of the
            # latest end time in the merged list
            last_merged_start, last_merged_end = merged_list[-1]

            if current_start_time <= last_merged_end:
                merged_list[-1] = (
                    last_merged_start,
                    max(current_end_time, last_merged_end),
                )
            else:
                merged_list.append((current_start_time, current_end_time))

        return merged_list
