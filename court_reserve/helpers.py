""" Helper functions for Court Reserve spider
"""
from time import tzset, time, localtime, strftime

# Reset time conversion rules using TZ env var
tzset()


def today_offset(offset=0):
    """Returns the date offset

    Args:
        offset: (int) Offset in days.

    Returns:
        Returns A datetime date with offset from today.
    """
    # Get offset in seconds
    offset_seconds = offset * 60 * 60 * 24
    return localtime(time() + offset_seconds)


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
        "startDate": f"{strftime('%Y-%m-%d', reserve_date)}T07:00:00.000Z",
        "end": f"{strftime('%Y-%m-%d', reserve_date)}T07:00:00.000Z",
        "orgId": org_id,
        "TimeZone": "America/Los_Angeles",
        "Date": (
            f"{strftime('%a', reserve_date)},"
            f" {reserve_date.tm_mday}"
            f" {strftime('%b', reserve_date)}"
            f" {reserve_date.tm_year}"
            f" 07:00:00 GMT"
        ),
        "KendoDate": {
            "Year": reserve_date.tm_year,
            "Month": reserve_date.tm_mon,
            "Day": reserve_date.tm_mday,
        },
        "UiCulture": "en-US",
        "CostTypeId": "86377",
        "CustomSchedulerId": f"{session_id}",
        "ReservationMinInterval": "60",
        "SelectedCourtIds": "14609,14610,14611,14612,14613,14614,14615,14616,14617",
        "MemberIds": f"{member_id}",
        "MemberFamilyId": "",
    }


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
