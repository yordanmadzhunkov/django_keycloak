import pytz
TIMEZONE_CHOICES = []
for tz in pytz.all_timezones:
    TIMEZONE_CHOICES.append((tz, tz))
TIMEZONE_CHOICES = tuple(TIMEZONE_CHOICES)