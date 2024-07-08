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


def get_session_maker():
    return sessionmaker(bind=engine, expire_on_commit=False)


def test():
    from tg.sql_time_finder import SqlTimeFinder
    tf = SqlTimeFinder("group5", 'Europe/Kyiv')
    tf.read_schedule()
    print(tf.find_next_remind_time())


if __name__ == '__main__':
    test()
