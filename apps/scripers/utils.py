from datetime import datetime, timezone


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
