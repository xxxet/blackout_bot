import csv

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Create an engine
engine = create_engine('sqlite:///timeseries.db')

# Define the base class
Base = declarative_base()


# Define the Days model
class Day(Base):
    __tablename__ = 'days'
    day_id = Column(Integer, primary_key=True)
    day_name = Column(String)


# Define the TimeSeries model
class Hours(Base):
    __tablename__ = 'hours'
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey('days.day_id'))
    hour = Column(Integer)
    zone = Column(String)
    day = relationship(Day)


# Create the tables
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Days of the week
days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# Insert days into Days table
for day_name in days_of_week:
    day = Day(day_name=day_name)
    session.add(day)
session.commit()

# Read CSV and populate the TimeSeries table
with open('../group5.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    headers = next(csvreader)  # Skip the header row

    for day_index, row in enumerate(csvreader):
        day_id = day_index + 1  # Day IDs start from 1 to 7

        for hour, zone in enumerate(row):
            timeseries = Hours(day_id=day_id, hour=hour, zone=zone)
            session.add(timeseries)

    session.commit()

# Close the session

hours = session.query(Hours).order_by(Hours.id)

for ind, h in enumerate(hours):
    print(ind)
    print(f"{h.id} {h.day_id} {h.hour} {h.day.day_name} {h.zone}")
session.close()
