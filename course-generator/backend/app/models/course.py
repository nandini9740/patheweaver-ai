from sqlalchemy import Column, String, Text, JSON, DateTime
from ..db.database import Base
from datetime import datetime
import uuid

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    topic = Column(Text, index=True)
    skill_level = Column(String)
    learning_style = Column(String)
    goal = Column(Text)
    generated_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
