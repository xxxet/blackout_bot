from datetime import datetime

DATE_FORMAT = "%m-%d-%Y %H:%M:%S %z"


def in_dateformat(date_string: str) -> datetime:
    return datetime.strptime(date_string, DATE_FORMAT)


def to_dateformat(date_obj: datetime) -> str:
    return date_obj.strftime(DATE_FORMAT)
