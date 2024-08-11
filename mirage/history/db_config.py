import sqlalchemy as sa
from mirage import consts

engine = sa.create_engine(
    f'sqlite:///{consts.DATABASES_FOLDER}/{consts.HISTORY_DB_NAME}')
Session = sa.orm.sessionmaker(bind=engine)
Base = sa.ext.declarative.declarative_base()
