import re


def time_to_s(time):
    """
    Args:
        time (float or str): timestamp

    Returns:
        s (float): seconds
    """
    if isinstance(time, str):
        return timestamp_to_s(time)
    elif isinstance(time, float) or isinstance(time, int):
        return time
    raise TypeError("Invalid timestamp (%s)" % str(time))


def time_to_timestamp(time):
    """
    Args:
        time (float or str): timestamp

    Returns:
        s (str): timestamp
    """
    if isinstance(time, str) and re.search("^-?(\d{2}:){2}\d{2}\.\d{3}$", time):
        return time
    elif isinstance(time, float) or isinstance(time, int):
        return s_to_timestamp(time)
    raise TypeError("Invalid timestamp (%s)" % str(time))


def time_interval_to_s(interval):
    """
    Args:
        interval: pair of float or str timestamps

    Returns:
        interval: pair of float timestamps
    """
    if len(interval) != 2:
        raise ValueError("Invalid interval: %s" % str(interval))
    return [time_to_s(interval[0]), time_to_s(interval[1])]


def time_interval_to_timestamp(interval):
    """
    Args:
        interval: pair of float or str timestamps

    Returns:
        interval: pair of str timestamps
    """
    if len(interval) != 2:
        raise ValueError("Invalid interval: %s" % str(interval))
    return [time_to_timestamp(interval[0]), time_to_timestamp(interval[1])]


def timestamp_to_s(timestamp):
    """
    Takes in a timestamp and converts to seconds

    Args:
        timestamp (string): format HH:MM:SS.MSS

    Returns:
        seconds (float): seconds
    """

    if not isinstance(timestamp, str):
        raise TypeError("Invalid timestamp (%s) is not a string" % str(timestamp))
    elif not re.search("^-?(\d{2}:){2}\d{2}\.\d{3}$", timestamp):
        raise ValueError("Invalid timestamp format (%s) should be HH:MM:SS.MSS")

    sign = -1 if timestamp[0] == '-' else 1
    tsplit = timestamp.split(':')
    hours = abs(int(tsplit[0]))
    minutes = abs(int(tsplit[1]))
    ssplit = tsplit[2].split('.')
    seconds = abs(int(ssplit[0]))
    milliseconds = abs(int(ssplit[1]))

    return sign * (3600*hours + 60*minutes + seconds + float(milliseconds/1000.))


def s_to_timestamp(s):
    """
    Takes in number of seconds and converts to a timestamp

    Args:
        s (float or int): seconds

    Returns:
        timestamp (string): format HH:MM:SS.MSS
    """

    if not isinstance(s, float) and not isinstance(s, int):
        raise TypeError("Invalid seconds (%s) is not a float" % str(s))

    sign = '-' if s < 0 else ''
    remainder = abs(s)
    hours = int(remainder/3600.)
    remainder -= 3600*hours
    minutes = int(remainder/60.)
    remainder -= 60*minutes
    seconds = int(remainder)
    remainder -= seconds
    milliseconds = int(1000*remainder)

    return "%s%02d:%02d:%02d.%03d" % (sign, hours, minutes, seconds, milliseconds)


def parse_version_string(version):
    """
    Args:
        version (string)

    Returns:
        major: int
        minor: int
        patch: int
    """
    parsed_version = version.split('.')
    major = int(parsed_version[0])
    minor = int(parsed_version[1])
    patch = int(parsed_version[2])

    return major, minor, patch
