from sqlalchemy import Column, Integer, String, Double
from mirage.history.history_db_config import Base


class Trade(Base):
    __tablename__ = 'trade'
    id = Column(Integer, primary_key=True, autoincrement=True)

    first_symbol = Column(String)
    first_amount = Column(Double)
    first_price_usd = Column(Double)

    second_symbol = Column(String)
    second_amount = Column(Double)
    second_price_usd = Column(Double)
