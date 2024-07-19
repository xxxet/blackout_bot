import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

BLACK_ZONE = "black"
GREY_ZONE = "grey"
WHITE_ZONE = "white"
ZONES = [BLACK_ZONE, GREY_ZONE, WHITE_ZONE]
UNDEFINED_ZONE = "und"

Base = declarative_base()
engine = create_engine('sqlite:///blackout.db')
tz = pytz.timezone('Europe/Kyiv')

def get_session_maker():
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_timefinder():
    from tg.sql_time_finder import SqlTimeFinder
    tf = SqlTimeFinder("group5", tz)
    tf.read_schedule()
    print(tf.find_next_remind_time())


def test_sqlserv():
    from sql.sql_service import SqlOperationsService
    sch = SqlOperationsService.get_schedule_for("Monday", "group5")
    pass


if __name__ == '__main__':
    test_sqlserv()
