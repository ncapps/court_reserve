""" Helper functions for Court Reserve spider
"""
from datetime import date, timedelta


def today_offset(offset=0):
    """Returns the date offset

    Args:
        date: A datetime date.
        offset: (int) Offset in days.

    Returns:
        Returns A datetime date with offset.
    """
    # Use -8 for UTC to PST offset. This does not consider day light savings.
    return date.today() + timedelta(hours=-8, days=int(offset))


def bookings_request_headers(org_id, session_id):
    """Returns HTTP headers for requesting bookings

    Args:
        org_id (str): Court reserve organization id
        session_id (str): User session id

    Returns:
        List of HTTP headers
    """
    return [
        ("authority", "app.courtreserve.com"),
        ("origin", "https://app.courtreserve.com"),
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
            f"https://app.courtreserve.com/Online/Reservations/Bookings/{org_id}?sId={session_id}",
        ),
        ("content-type", "application/x-www-form-urlencoded; charset=UTF-8"),
        ("sec-fetch-site", "same-origin"),
        ("sec-fetch-mode", "cors"),
        ("sec-fetch-dest", "empty"),
        ("accept-language", "en-US,en;q=0.9"),
    ]


def bookings_request_body(org_id, reserve_date, session_id, member_id):
    """Returns HTTP request body for bookings request

    Args:
        org_id (str): Court reserve organization id
        reserve_date (datetime.date): Reservation date
        session_id (str): User session id
        member_id (str): User member id

    Returns:
        A dictionary containing bookings request body
    """
    return {
        "startDate": f"{reserve_date}T07:00:00.000Z",
        "end": f"{reserve_date}T07:00:00.000Z",
        "orgId": org_id,
        "TimeZone": "America/Los_Angeles",
        "Date": (
            f"{reserve_date.strftime('%a')},"
            f"+{reserve_date.day}"
            f"+{reserve_date.strftime('%b')}"
            f"+{reserve_date.year}"
            f"+07:00:00+GMT"
        ),
        "KendoDate": {
            "Year": reserve_date.year,
            "Month": reserve_date.month,
            "Day": reserve_date.day,
        },
        "UiCulture": "en-US",
        "CostTypeId": "86377",
        "CustomSchedulerId": f"{session_id}",
        "ReservationMinInterval": "60",
        "SelectedCourtIds": "14609,14610,14611,14612,14613,14614,14615,14616,14617",
        "MemberIds": member_id,
        "MemberFamilyId": "",
    }
