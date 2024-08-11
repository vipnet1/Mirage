from sqlalchemy import Column, Integer, String, Double
from history import database


class Trade(database.Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)

    first_symbol = Column(String)
    first_amount = Column(Double)
    first_price_usd = Column(Double)

    second_symbol = Column(String)
    second_amount = Column(Double)
    second_price_usd = Column(Double)
