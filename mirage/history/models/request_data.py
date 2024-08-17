from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from mirage.history.history_db_config import Base


class RequestData(Base):
    __tablename__ = 'request_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # pylint: disable=not-callable
    created_at = Column(DateTime, server_default=func.now())
    source = Column(String)
    content = Column(String)
