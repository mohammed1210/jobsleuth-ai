from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    salary = Column(String)
    link = Column(String, nullable=False)
    source = Column(String, nullable=False)
    date_posted = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)