from sqlalchemy import Column, Integer
from mirage.history.history_db_config import Base


class BinanceOrder(Base):
    __tablename__ = 'binance_order'

    id = Column(Integer, primary_key=True)

    # Dynamically add columns based on Binance order object
    def __init__(self, order_data):
        for key, value in order_data.items():
            setattr(self, key, value)
