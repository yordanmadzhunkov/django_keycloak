from datetime import datetime, timezone
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style


def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def str_to_datetime(str_dt:str) -> datetime:
    return datetime.strptime(str_dt, "%Y-%m-%dT%H:%M:%S%z")


def datetime_to_str(date_time:datetime) -> str:
    return date_time.strftime("%Y-%m-%dT%H:%M:%S%z")


colorama_init()

print(f"This is {Fore.GREEN}color{Style.RESET_ALL}!")


# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL
def print_yellow(message):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def print_red(message):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def print_blue(message):
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")


def print_green(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def green(message):
    return f"{Fore.GREEN}{message}{Style.RESET_ALL}"


def yellow(message):
    return f"{Fore.YELLOW}{message}{Style.RESET_ALL}"
