from . import Base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine
from models import *

class SQLAlchemyDriver(object):
    def __init__(self, conn, **config):
        self.engine = create_engine(conn, **config)

        Base.metadata.bind = self.engine
        Base.metadata.create_all()

        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    @property
    @contextmanager
    def session(self):
        '''
        Provide a transactional scope around a series of operations.
        '''
        session = self.Session()
        try:
            yield session
        except:
            session.rollback()
            session.close()
            raise

        try:
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
