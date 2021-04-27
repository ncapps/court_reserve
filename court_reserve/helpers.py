""" Helper functions for Court Reserve spider
"""
import re
from datetime import datetime, timedelta
from collections import defaultdict

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
        ("content-type", "application/x-www-form-urlencoded; charset=UTF-8"),
        ("origin", "https://app.courtreserve.com"),
        ("sec-fetch-site", "same-origin"),
        ("sec-fetch-mode", "cors"),
        ("sec-fetch-dest", "empty"),
        (
            "referer",
            f"https://app.courtreserve.com/Online/Reservations/Bookings/{org_id}?sId={session_id}",
        ),
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


def get_create_booking_body(session_id, token, start_time, court_id, **kwargs):
    """Returns HTTP request body used for creating a new reservation

    Args:
        session_id (str): User session id
        token (str): Verification token
        start_time (datetime): Reservation start time
        court_id (str): Court id to reserve
        kwargs (dict): Environment variables including organization id, member ids, etc.

    Returns:
        A string that represents the HTTP request body
    """
    return (
        f"__RequestVerificationToken={token}&"
        f"Id={kwargs['ORG_ID']}&"
        f"OrgId={kwargs['ORG_ID']}&"
        f"MemberId={kwargs['MEMBER_ID1']}&"
        "MemberIds=&"
        "IsConsolidatedScheduler=True&"
        f"Date={start_time.strftime('%m/%d/%Y 12:00:00 AM')}&"
        "HoldTimeForReservation=15&"
        "RequirePaymentWhenBookingCourtsOnline=False&"
        "AllowMemberToPickOtherMembersToPlayWith=True&"
        "ReservableEntityName=Court&"
        "IsAllowedToPickStartAndEndTime=False&"
        f"CustomSchedulerId={session_id}&"
        "IsConsolidated=False&"
        "IsToday=False&"
        f"Id={kwargs['ORG_ID']}&"
        f"OrgId={kwargs['ORG_ID']}&"
        f"Date={start_time.strftime('%m/%d/%Y 12:00:00 AM')}&"
        "SelectedCourtType=Hard&"
        "SelectedCourtTypeId=0&"
        "DisclosureText=&"
        "DisclosureName=&"
        f"StartTime={start_time.strftime('%H:%M:%S')}&"
        "CourtTypeEnum=2&"
        f"MembershipId={kwargs['COST_TYPE_ID']}&"
        f"CustomSchedulerId={session_id}&"
        "IsAllowedToPickStartAndEndTime=False&"
        "UseMinTimeByDefault=False&"
        "IsEligibleForPreauthorization=False&"
        "ReservationTypeId=17591&"
        "Duration=60&"
        f"CourtId={court_id}&"
        "OwnersDropdown_input=&"
        "OwnersDropdown=&"
        f"SelectedMembers[0].OrgMemberId={kwargs['ORG_MEMBER_ID1']}&"
        f"SelectedMembers[0].MemberId={kwargs['MEMBER_ID1']}&"
        "SelectedMembers[0].MemberFamilyId=&"
        f"SelectedMembers[0].FirstName={kwargs['FIRST_NAME1']}&"
        f"SelectedMembers[0].LastName={kwargs['LAST_NAME1']}&"
        f"SelectedMembers[0].Email={kwargs['EMAIL1']}&"
        "SelectedMembers[0].PaidAmt=&"
        f"SelectedMembers[0].MembershipNumber={kwargs['ORG_MEMBER_ID1']}&"
        "SelectedMembers[0].PriceToPay=0&"
        f"SelectedMembers[1].OrgMemberId={kwargs['ORG_MEMBER_ID2']}&"
        f"SelectedMembers[1].MemberId={kwargs['MEMBER_ID2']}&"
        "SelectedMembers[1].MemberFamilyId=&"
        f"SelectedMembers[1].FirstName={kwargs['FIRST_NAME2']}&"
        f"SelectedMembers[1].LastName={kwargs['LAST_NAME2']}&"
        "SelectedMembers[1].Email=&"
        "SelectedMembers[1].PaidAmt=&"
        f"SelectedMembers[1].MembershipNumber={kwargs['ORG_MEMBER_ID2']}&"
        "SelectedMembers[1].PriceToPay=0&"
        "SelectedNumberOfGuests=&"
        "X-Requested-With=XMLHttpRequest"
    )


def get_bookings_by_court(bookings, tz_name):
    """Groups bookings by court

    Args:
        bookings (list): List of booking data received from courtreserve
        tz_name (str): IANA time zone name

    Returns:
        (dict) Grouped by court id, a list of start and end datetimes a
                court is reserved
    """
    tz_obj = tz.gettz(tz_name) if tz_name else tz.tzlocal()
    bookings_by_court = defaultdict(list)
    epoch_re = re.compile("[0-9]+")
    # Get datetime objects from POSIX timestamp, grouped by court id
    for booking in bookings:
        bookings_by_court[str(booking["CourtId"])].append(
            (
                datetime.fromtimestamp(
                    int(epoch_re.search(booking["Start"]).group(0)) / 1000, tz=tz_obj
                ),
                datetime.fromtimestamp(
                    int(epoch_re.search(booking["End"]).group(0)) / 1000, tz=tz_obj
                ),
            )
        )

    # Merge contiguous reservations by court
    for court_id, _bookings in bookings_by_court.items():
        bookings_by_court[court_id] = merge_bookings(_bookings)

    return bookings_by_court


def get_day_preferences(preferences, booking_date):
    """Get time and court preferences for the booking date day
        of the week

    Args:
        schedule (dict): Booking time and court ordered by preferences for each day
                            of the week
        booking_date (datetime): Datetime to reserve a court

    Returns:
        (list) List of court and booking time ordered by preference for the booking date

    Throws:
        (KeyError)
    """

    def str_to_date(hour_min):
        _dt = datetime.strptime(hour_min, "%I:%M %p")
        return booking_date.replace(
            hour=_dt.hour, minute=_dt.minute, second=0, microsecond=0
        )

    weekday_name = booking_date.strftime("%A").lower()
    return [
        (court_id, (str_to_date(start), str_to_date(end)))
        for start, end in preferences[weekday_name]["start_end_times"]
        for court_id in preferences[weekday_name]["court_ids"]
    ]


def get_booking_date(offset=0, tz_name=""):
    """Returns the booking date

    Args:
        offset (int): Number of days from current date to booking date
        tz_name (str): IANA time zone name
            https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    Returns:
        Returns a datetime object
    """
    tz_obj = tz.gettz(tz_name) if tz_name else tz.tzlocal()
    days_offset = timedelta(days=+int(offset))
    return datetime.now(tz=tz_obj) + days_offset


def merge_bookings(bookings):
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


def find_open_court(bookings, preferences):
    """Compares existing bookings with user preferences
        and returns the first open court found

    Args:
        bookings (dict): Court bookings grouped by court id
        preferences (list): List of court and time preferences

    Returns:
        (tuple) Court id, start datetime, end datetime

    """
    for court_id, pref_start_end in preferences:
        pref_start, pref_end = pref_start_end
        conflict = False
        for booked_start, booked_end in bookings.get(court_id):
            if pref_end > booked_start and pref_start < booked_end:
                conflict = True
        if not conflict:
            return (court_id, pref_start, pref_end)

    # Court and time match not found
    return None
