import re


def read_config_timestamp(timestamp):
    """
    Reads in config time and returns seconds

    Args:
        timestamp (str or float): string in format HH:MM:SS.MSS or float in seconds

    Returns:
        seconds (float): seconds
    """
    if isinstance(timestamp, str):
        return timestamp_to_s(timestamp)
    elif isinstance(timestamp, float) or isinstance(timestamp, int):
        return timestamp
    raise TypeError("Invalid timestamp (%s)" % str(timestamp))


def read_config_interval(interval):
    """
    Reads in config pair of timestamps and returns pair of seconds

    Args:
        interval (timestamp, timestamp): pair of timestamps

    Returns:
        (timestamp_s, timestamp_s)
    """
    if len(interval) != 2:
        raise ValueError("Invalid interval: %s" % str(interval))
    return [read_config_timestamp(interval[0]), read_config_timestamp(interval[1])]


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
