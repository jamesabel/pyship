from datetime import datetime
from dateutil import tz

# todo: this code is from sundry - break this out of sundry into its own package


def _time_string_format(dt, time_zone=None):
    """
    format a datetime based on time zone
    :param dt: datetime object
    :param time_zone: a timezone object, or None for local time zone
    :return:
    """
    return dt.astimezone(time_zone).isoformat()


def local_time_string(timestamp=None):
    """
    time string in local time
    e.g. 2018-07-21T11:12:42.248091-07:00
    :param timestamp: time since epoch (as a float) or None for current time
    :return: an ISO time string
    """
    if timestamp is None:
        time_string = _time_string_format(datetime.now())
    else:
        time_string = _time_string_format(datetime.fromtimestamp(timestamp))
    return time_string


def utc_time_string(timestamp=None):
    """
    time string in UTC time
    e.g. 2018-07-22T01:12:42.248091+00:00
    :param timestamp: time since epoch (as a float) or None for current time
    :return: an ISO time string
    """
    utc_tz = tz.gettz("utc")
    if timestamp is None:
        time_string = _time_string_format(datetime.utcnow(), utc_tz)
    else:
        time_string = _time_string_format(datetime.fromtimestamp(timestamp), utc_tz)
    return time_string
