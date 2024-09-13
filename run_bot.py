import os

from src.tg.outage_bot import main
from freezegun import freeze_time


@freeze_time("2024-09-04 23:44:59", tz_offset=-3)
def start() -> None:
    token = str(os.getenv("TOKEN"))
    main(token)


if __name__ == "__main__":
    start()
