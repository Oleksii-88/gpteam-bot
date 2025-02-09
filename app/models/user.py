from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database.connection import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, approved, rejected
