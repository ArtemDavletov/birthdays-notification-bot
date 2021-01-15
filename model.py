import uuid

from sqlalchemy import create_engine, Column, String, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import config


engine = create_engine(
    config.DB_URL,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Birthday(Base):
    __tablename__ = 'birthdays'

    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)
    chat_id = Column(Integer)
    name = Column(String)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)


class Notification(Base):
    __tablename__ = 'notification'

    id = Column(UUID(as_uuid=True), unique=True, primary_key=True, default=uuid.uuid4)
    chat_id = Column(Integer)
    time = Column(String)


Base.metadata.create_all(bind=engine)

db = SessionLocal()
