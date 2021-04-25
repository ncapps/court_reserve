""" Helper functions for Court Reserve spider
"""
from datetime import datetime, timedelta

from dateutil import tz


def get_http_headers(org_id, session_id):
    """Returns HTTP headers for requests to the app.courtreserve.com API

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


def get_bookings_body(
    org_id, booking_date, session_id, member_id, time_zone, cost_type_id, court_ids
):
    """Returns HTTP request body used for requesting existing reservartions

    Args:
        org_id (str): Court reserve organization id
        booking_date (datetime.date): Reservation date
        session_id (str): User session id
        member_id (str): User member id
        time_zone (str): IANA time zone name
        cost_type_id (str): Cost type id
        court_ids (str): Comma separated list of court ids

    Returns:
        A dictionary that represents the HTTP request body
    """
    return {
        "startDate": f"{booking_date.strftime('%Y-%m-%d')}T07:00:00.000Z",
        "end": f"{booking_date.strftime('%Y-%m-%d')}T07:00:00.000Z",
        "orgId": org_id,
        "TimeZone": time_zone,
        "Date": (
            f"{booking_date.strftime('%a')},"
            f" {booking_date.day}"
            f" {booking_date.strftime('%b')}"
            f" {booking_date.year}"
            f" 07:00:00 GMT"
        ),
        "KendoDate": {
            "Year": booking_date.year,
            "Month": booking_date.month,
            "Day": booking_date.day,
        },
        "UiCulture": "en-US",
        "CostTypeId": cost_type_id,
        "CustomSchedulerId": session_id,
        "ReservationMinInterval": "60",
        "SelectedCourtIds": court_ids,
        "MemberIds": member_id,
        "MemberFamilyId": "",
    }


def get_create_booking_body(org_id, session_id, member_id, cost_type_id):
    """Returns HTTP request body used for creating a new reservation

    Args:
        org_id (str): Court reserve organization id
        reserve_date (datetime.date): Reservation date
        session_id (str): User session id
        member_id (str): User member id
        cost_type_id (str): Cost type id

    Returns:
        A dictionary that represents the HTTP request body
    """
    return {
        "__RequestVerificationToken": "Knctp8jpOwkAhrLi6Ui9apH6KarxUWWrt7Ghfddn7VKgZhKYc64NIeR6oCaM4j2b-FIZxNskLbPpxiW4QwS-2VVpEFbhRi_xqcYW6CJ3raSc1kGoMNpdv64KL6iR-aW0WEr52ypox8kJ-GyqkP-idA2",
        "Id": org_id,
        "OrgId": org_id,
        "MemberId": member_id,
        "MemberIds": "",
        "IsConsolidatedScheduler": True,
        "Date": "4/22/2021 12:00:00 AM",  # TODO format from date arg
        "HoldTimeForReservation": 15,
        "RequirePaymentWhenBookingCourtsOnline": False,
        "AllowMemberToPickOtherMembersToPlayWith": True,
        "ReservableEntityName": "Court",
        "IsAllowedToPickStartAndEndTime": False,
        "CustomSchedulerId": session_id,
        "IsConsolidated": False,
        "IsToday": False,
        "SelectedCourtType": "Hard",
        "SelectedCourtTypeId": 0,
        "DisclosureText": "",
        "DisclosureName": "",
        "StartTime": "19:00:00",  # TODO add time arg
        "CourtTypeEnum": 2,
        "MembershipId": cost_type_id,
        "UseMinTimeByDefault": False,
        "IsEligibleForPreauthorization": False,
        "ReservationTypeId": 17591,
        "Duration": 60,
        "CourtId": 14614,  # TODO add court id arg
        "OwnersDropdown_input": "",
        "OwnersDropdown": "",
        "SelectedMembers[0].OrgMemberId": "ORG_MEMBER_ID1",  # TODO
        "SelectedMembers[0].MemberId": "MEMBER_ID1",  # TODO
        "SelectedMembers[0].MemberFamilyId": "",
        "SelectedMembers[0].FirstName": "",
        "SelectedMembers[0].LastName": "",
        "SelectedMembers[0].Email": "",
        "SelectedMembers[0].PaidAmt": "",
        "SelectedMembers[0].MembershipNumber": "ORG_MEMBER_ID1",  # TODO
        "SelectedMembers[0].PriceToPay": 0,
        "SelectedMembers[1].OrgMemberId": "ORG_MEMBER_ID2",  # TODO
        "SelectedMembers[1].MemberId": "MEMBER_ID2",  # TODO
        "SelectedMembers[1].MemberFamilyId": "",
        "SelectedMembers[1].FirstName": "",
        "SelectedMembers[1].LastName": "",
        "SelectedMembers[1].Email": "",
        "SelectedMembers[1].PaidAmt": "",
        "SelectedMembers[1].MembershipNumber": "ORG_MEMBER_ID2",
        "SelectedMembers[1].PriceToPay": 0,
    }


def get_booking_date(offset=0, tz_name=""):
    """Returns the booking date

    Args:
        offset (int): Number of days from current date to booking date
        tz (str): IANA name of the time zone
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    Returns:
        Returns a datetime object
    """
    tz_obj = tz.gettz(tz_name) if tz_name else tz.tzlocal()
    days_offset = timedelta(days=+int(offset))
    return datetime.now(tz=tz_obj) + days_offset


def merge_booking_ranges(bookings):
    """Merge consecutive booking time ranges

    Args:
        bookings (list): List of start and end times

    Returns:
        List of consecutive bookings times merged
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


def get_available_court(bookings, requests):
    """Find available court by requested time"""
    for req_start_end, req_court_id in requests:
        req_start, req_end = req_start_end
        court_bookings = bookings.get(req_court_id)
        available = True
        for booked_start, booked_end in court_bookings:
            if req_end > booked_start and req_start < booked_end:
                available = False

        if available:
            return {"start_end": (req_start, req_end), "court_id": req_court_id}

    # Available court not found
    return None
