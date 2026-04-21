from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

#Connection 
ENGINE = create_engine("sqlite:///queens.db", echo=False)
Base = declarative_base()
Session = sessionmaker(bind=ENGINE)

#Table 1: All valid solutions 
class Solution(Base):
    __tablename__ = "solutions"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    board       = Column(String, unique=True, nullable=False)
    is_claimed  = Column(Boolean, default=False)
    claimed_by  = Column(String, nullable=True)
    claimed_at  = Column(DateTime, nullable=True)

#2: Player correct answers
class PlayerAnswer(Base):
    __tablename__ = "player_answers"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    player_name  = Column(String, nullable=False)
    solution     = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now)
    time_taken = Column(Float, nullable=True)

#3: Solver performance logs
class SolverRun(Base):
    __tablename__ = "solver_runs"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    solver_type    = Column(String, nullable=False)
    time_taken     = Column(Float, nullable=False)
    solutions_found = Column(Integer, nullable=False)
    run_at         = Column(DateTime, default=datetime.now)

#Create all tables
def init_db():
    Base.metadata.create_all(ENGINE)
    print("Database ready.")

def get_session():
    return Session()