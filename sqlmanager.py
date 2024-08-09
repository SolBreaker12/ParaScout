from sqlalchemy import create_engine, Column, String, ARRAY, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///test.db')


class User(Base):
    __tablename__ = 'users'
    name = Column(String, primary_key=True, unique=True, nullable=False)
    password = Column(String, nullable=False)


class Team(Base):
    __tablename__ = 'teams'
    team_number = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    events = Column(ARRAY(String), nullable=False)
    matches = Column(ARRAY(String))


class Match(Base):
    __tablename__ = 'matches'
    match_id = Column(String, primary_key=True, unique=True, nullable=False)
    blue_alliance = Column(ARRAY(Integer), nullable=False)
    red_alliance = Column(ARRAY(Integer), nullable=False)


class Match_Data(Base):
    __tablename__ = 'match_data'
    team_number = Column(Integer, primary_key=True, unique=True, nullable=False)
    event = Column(String, nullable=False)
    match_id = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    auto_pieces = Column(Integer, nullable=False)
    teleop_pieces = Column(Integer, nullable=False)
    driver_rating = Column(Integer, nullable=False)


class Pit_Data(Base):
    __tablename__ = 'pit_data'
    team_number = Column(Integer, primary_key=True, unique=True, nullable=False)
    event = Column(String, nullable=False)
    drivetrain_type = Column(String, nullable=False)
    mechanisms = Column(ARRAY(String), nullable=False)
    auto_num = Column(Integer, nullable=False)
