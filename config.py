import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

BLACK_ZONE = "black"
GREY_ZONE = "grey"
WHITE_ZONE = "white"
ZONES = [BLACK_ZONE, GREY_ZONE, WHITE_ZONE]
UNDEFINED_ZONE = "und"

engine = create_engine("sqlite:///blackout.db")
tz = pytz.timezone("Europe/Kyiv")


def get_session_maker() -> Session:
    return sessionmaker(bind=engine, expire_on_commit=False)
