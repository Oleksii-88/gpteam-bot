from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database.connection import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_message = Column(Text)
    ai_request = Column(Text)
    ai_response = Column(Text)
    status = Column(String)  # success/error
