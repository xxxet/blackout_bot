import pathlib

import pytz
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

BLACK_ZONE = "black"
GREY_ZONE = "grey"
WHITE_ZONE = "white"
ZONES = [BLACK_ZONE, GREY_ZONE, WHITE_ZONE]
UNDEFINED_ZONE = "und"
DEFAULT_NOTIF = 15
NOTIFY_BEFORE_OPTIONS = [DEFAULT_NOTIF, 15, 20, 30]
BASE_PATH = pathlib.Path(__file__).parent.absolute()
tz = pytz.timezone("Europe/Kyiv")


def get_engine() -> Engine:
    return create_engine(f"sqlite:///{BASE_PATH.joinpath("blackout.db")}")


def get_session_maker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
