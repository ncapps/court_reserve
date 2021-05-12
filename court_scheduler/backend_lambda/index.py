#!/usr/bin/env python
""" app.courtreserve.com adapter """
import logging

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CourtReserveClient:
    """Interfaces with app.courtreserve.com"""

    def __init__(
        self, org_id: str = None, username: str = None, password: str = None
    ) -> None:
        self.session = requests.Session()

        if org_id and username and password:
            self.login(org_id, username, password)

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

    def login(self, org_id: str, username: str, password: str) -> None:
        """Peform user login to app.courtreserve.com

        Args:
            org_id (str): Organization id
            username (str): Username
            password (str): Password

        Returns:
            None

        Raises:
            TBD
        """
        path = f"Account/Login/{org_id}"
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

        print(response.status_code)
        print(response.url)


def handler(event=None, context=None):
    """Lambda function handler

    Args:
        event (dict):
        context (dict):

    Returns
        Response (dict):
    """

    # Get schedule and login details from secrets manager

    # Check if a reservation should be made, otherwise exit

    # Create CourtReserveClient
    court_reserve = CourtReserveClient()


if __name__ == "__main__":
    handler()
