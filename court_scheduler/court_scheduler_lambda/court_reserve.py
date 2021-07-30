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
            AssertionError when login attempt fails
        """
        path = f"Account/Login/{self.org_id}"
        payload = {"UserNameOrEmail": username, "Password": password}
        token_name = "__RequestVerificationToken"

        # Add hidden __RequestVerificationToken to login request
        response = self._request("GET", path)
        soup = BeautifulSoup(response.text, "html.parser")
        payload[token_name] = soup.find(id="loginForm").find(
            attrs={"name": token_name}
        )["value"]

        response = self._request("POST", path, data=payload)
        # Expect redirect on successful login
        assert response.url.find("Account/Login") == -1, "Login attempt failed."

        # Get session id
        soup = BeautifulSoup(response.text, "html.parser")
        bookings_path = soup.select_one("#respMenu li:nth-child(2) li a")["href"]
        self.session_id = re.search("sId=([0-9]+)", bookings_path).group(1)
        logger.debug("Found session id: %s", self.session_id)

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
        soup = BeautifulSoup(response.text, "html.parser")
        court_criteria = [
            str(script.string)
            for script in soup.select(
                "#expanded-page div.content div.row div.col-lg-12 script"
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
        logger.debug("Found %s reservations", json_resp["Total"])

        tz_obj = tz.obj = tz.gettz(time_zone)
        court_bookings = {}
        epoch_re = re.compile("[0-9]+")
        # Get datetime objects from POSIX timestamp, grouped by court id
        for booking in json_resp["Data"]:
            court_label = str(booking["CourtLabel"])
            if not court_bookings.get(court_label):
                court_bookings[court_label] = {
                    "court_id": booking["CourtId"],
                    "start_end_times": [],
                }
            court_bookings[court_label]["start_end_times"].append(
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

        # Merge contiguous reservations by court
        for court_label in court_bookings:
            court_bookings[court_label]["start_end_times"] = self._merge_bookings(
                court_bookings[court_label]["start_end_times"]
            )

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
        _bookings = bookings.copy()
        _bookings.sort(key=lambda x: x[0])
        merged_list = [(_bookings[0])]

        for current_start_time, current_end_time in _bookings[1:]:
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

    def create_reservation(
        self,
        court: str,
        start: datetime,
        end: datetime,
        players: list,
        dry_run: bool = False,
    ) -> None:
        """Creates a court reservation

        Args:
            start (datetime): Reservation start date and time
            end (datetime): Reservation end date and time
            court (str): Court label (i.e. "Court #1")
            players (list): List of player names (i.e. ["Naomi Osaka"])
            dry_run (bool): Defaults to False. When dry run mode is enabled a reservation is
                            not created.

        Returns:
            None

        Raises:
            AssertionError when reservation creation fails
        """
        path = f"Reservations/CreateReservationCourtsview/{self.org_id}"
        params = {
            "start": start.strftime("%a %b %d %Y %H:%M:%S GMT%z (%Z)"),
            "end": end.strftime("%a %b %d %Y %H:%M:%S GMT%z (%Z)"),
            "courtLabel": court,
            "customSchedulerId": self.session_id,
        }
        response = self._request("GET", path, params=params, headers=self.http_headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check if a reservation has already been made
        has_max_courts = (
            str(soup.find("p", class_="confirm-message")).find(
                "reached max number of courts allowed"
            )
            != -1
        )
        assert not has_max_courts, "Max number of courts allowed already reserved."

        token = soup.select_one("#createReservation-Form input")["value"]
        court_id = soup.find("input", id="CourtId")["value"]
        member_id = soup.find("input", id="MemberId")["value"]
        membership_id = soup.find("input", id="MembershipId")["value"]

        # Get organizing player details
        path = f"AjaxController/CalculateReservationCostMemberPortal/{self.org_id}"
        payload = {
            "Start": start.strftime("%H:%M:%S"),
            "End": "",
            "CourtType": "2",
            "MiscFees": "",
            "ReservationTypeId": "",
            "RegisteringOrganizationMemberId": "",
            "Date": start.strftime("%m/%d/%Y 12:00:00 AM"),
            "NumberOfGuests": "",
            "MembersString": [],
        }
        response = self._request("POST", path, data=payload, headers=self.http_headers)
        soup = BeautifulSoup(json.loads(response.text)["memberTable"], "html.parser")
        org_member_id = soup.find("input", id="SelectedMembers_0__OrgMemberId")["value"]
        member0_firstname = soup.find("input", id=f"hidden-firstname_{org_member_id}")[
            "value"
        ]
        member0_lastname = soup.find("input", id=f"hidden-lastname_{org_member_id}")[
            "value"
        ]
        member0_email = soup.find("input", id=f"hidden-email_{org_member_id}")["value"]

        # Get additional player details
        # TODO Add support for doubles
        path = f"AjaxController/GetMembersToPlayWith/{self.org_id}"
        params = {
            "costTypeId": membership_id,
            "filterValue": players[0],
            "organizationMemberIdsString": "",
            "filter[filters][0][value]": players[0],
            "filter[filters][0][field]": "DisplayName",
            "filter[filters][0][operator]": "contains",
            "filter[filters][0][ignoreCase]": "true",
            "filter[logic]": "and",
        }
        response = self._request("GET", path, params=params, headers=self.http_headers)
        player2 = json.loads(response.text)[0]

        payload = (
            f"__RequestVerificationToken={token}&"
            f"Id={self.org_id}&"
            f"OrgId={self.org_id}&"
            f"MemberId={member_id}&"
            "MemberIds=&"
            "IsConsolidatedScheduler=True&"
            f"Date={start.strftime('%m/%d/%Y 12:00:00 AM')}&"
            "HoldTimeForReservation=15&"
            "RequirePaymentWhenBookingCourtsOnline=False&"
            "AllowMemberToPickOtherMembersToPlayWith=True&"
            "ReservableEntityName=Court&"
            "IsAllowedToPickStartAndEndTime=False&"
            f"CustomSchedulerId={self.session_id}&"
            "IsConsolidated=False&"
            "IsToday=False&"
            f"Id={self.org_id}&"
            f"OrgId={self.org_id}&"
            f"Date={start.strftime('%m/%d/%Y 12:00:00 AM')}&"
            "SelectedCourtType=Hard&"
            "SelectedCourtTypeId=0&"
            "DisclosureText=&"
            "DisclosureName=&"
            f"StartTime={start.strftime('%H:%M:%S')}&"
            "CourtTypeEnum=2&"
            f"MembershipId={membership_id}&"
            f"CustomSchedulerId={self.session_id}&"
            "IsAllowedToPickStartAndEndTime=False&"
            "UseMinTimeByDefault=False&"
            "IsEligibleForPreauthorization=False&"
            "ReservationTypeId=17591&"
            "Duration=60&"
            f"CourtId={court_id}&"
            "OwnersDropdown_input=&"
            "OwnersDropdown=&"
            f"SelectedMembers[0].OrgMemberId={org_member_id}&"
            f"SelectedMembers[0].MemberId={member_id}&"
            "SelectedMembers[0].MemberFamilyId=&"
            f"SelectedMembers[0].FirstName={member0_firstname}&"
            f"SelectedMembers[0].LastName={member0_lastname}&"
            f"SelectedMembers[0].Email={member0_email}&"
            "SelectedMembers[0].PaidAmt=&"
            f"SelectedMembers[0].MembershipNumber={org_member_id}&"
            "SelectedMembers[0].PriceToPay=0&"
            f"SelectedMembers[1].OrgMemberId={player2['MemberOrgId']}&"
            f"SelectedMembers[1].MemberId={player2['MemberId']}&"
            "SelectedMembers[1].MemberFamilyId=&"
            f"SelectedMembers[1].FirstName={player2['FirstName']}&"
            f"SelectedMembers[1].LastName={player2['LastName']}&"
            "SelectedMembers[1].Email=&"
            "SelectedMembers[1].PaidAmt=&"
            f"SelectedMembers[1].MembershipNumber={player2['MemberOrgId']}&"
            "SelectedMembers[1].PriceToPay=0&"
            "SelectedNumberOfGuests=&"
            "X-Requested-With=XMLHttpRequest"
        )

        if dry_run:
            logger.info("Dry run mode enabled. Court will not be reserved.")
            logger.debug("Reservation payload: %s", payload)
            return

        path = f"Reservations/CreateReservation/{self.org_id}"
        response = self._request("POST", path, data=payload, headers=self.http_headers)
        json_resp = json.loads(response.text)

        assert json_resp["isValid"]

        logger.info("%s reserved at %s", court, start.strftime("%I:%M %p %Z"))
