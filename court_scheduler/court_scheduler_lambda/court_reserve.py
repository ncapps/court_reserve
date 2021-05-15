""" app.court.reserve.com adapter
"""
import logging
import logging.config
import requests
import re
from datetime import datetime

from bs4 import BeautifulSoup

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

    def _http_headers(self):
        """Returns HTTP headers for requests to the app.courtreserve.com API

        Args:
            None

        Returns:
            Dictionary of HTTP Headers to send with a Request
        """
        return {
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
                f"{self.org_id}?sId={self.session_id}",
            ),
            "accept-language": "en-US,en;q=0.9",
        }

    def list_reservations(self, reserve_date: datetime):
        """ """
        return ["todo"]
