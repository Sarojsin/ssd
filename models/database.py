from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./survey.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    responses = relationship("Response", back_populates="survey", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    survey = relationship("Survey", back_populates="responses")


class PersonalHealthData(Base):
    __tablename__ = "personal_health_data"
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer, nullable=True)
    height = Column(String(20), nullable=True)
    weight = Column(String(20), nullable=True)
    stress_level = Column(String(50), nullable=True)
    exercise_frequency = Column(String(50), nullable=True)
    sleep_hours = Column(String(20), nullable=True)
    diet = Column(String(50), nullable=True)
    cycle_start_date = Column(String(50), nullable=True)
    cycle_length = Column(Integer, nullable=True)
    period_length = Column(Integer, nullable=True)
    symptoms = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cycle_histories = relationship("CycleHistory", back_populates="personal_health", cascade="all, delete-orphan")


class CycleHistory(Base):
    __tablename__ = "cycle_history"
    id = Column(Integer, primary_key=True, index=True)
    personal_health_id = Column(Integer, ForeignKey("personal_health_data.id"), nullable=False)
    cycle_start_date = Column(String(50), nullable=True)
    cycle_length = Column(Integer, nullable=True)
    period_length = Column(Integer, nullable=True)
    symptoms = Column(Text, nullable=True)
    personal_health = relationship("PersonalHealthData", back_populates="cycle_histories")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
