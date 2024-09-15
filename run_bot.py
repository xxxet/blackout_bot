import os

from src.tg.outage_bot import main


def start() -> None:
    token = str(os.getenv("TOKEN"))
    main(token)


if __name__ == "__main__":
    start()
