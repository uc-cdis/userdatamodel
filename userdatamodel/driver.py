from . import Base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.types import DateTime
from models import * # noqa

import datetime


class SQLAlchemyDriver(object):
    def __init__(self, conn, **config):
        self.engine = create_engine(conn, **config)

        Base.metadata.bind = self.engine
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.pre_migrate()
        Base.metadata.create_all()
        self.post_migrate()

    @property
    @contextmanager
    def session(self):
        '''
        Provide a transactional scope around a series of operations.
        '''
        session = self.Session()
        yield session

        try:
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create(self, session, model, query, props=None):
        '''
        Get or create a row
        Args:
            session: sqlalchemy session
            model: the ORM class from userdatamodel.models
            query: a dict of query parameters
            props: extra props aside from query to be added to the object on
                   creation
        Returns:
            result object of the model class
        '''
        result = session.query(model).filter_by(**query).first()
        if result is None:
            args = props if props is not None else {}
            args.update(query)
            result = model(**args)
            session.add(result)
        return result

    def pre_migrate(self):
        '''
        migration script to be run before create_all
        '''
        if not self.engine.dialect.supports_alter:
            print(
                "This engine dialect doesn't support altering"
                " so we are not migrating even if necessary!")
            return

        if (not self.engine.dialect.has_table(self.engine, 'Group') and
                self.engine.dialect.has_table(self.engine, 'research_group')):
            print("Altering table research_group to group")
            with self.session as session:
                session.execute('ALTER TABLE research_group rename to "Group"')

    def post_migrate(self):
        '''
        migration function to be run after create_all
        '''
        md = MetaData()
        user_table = Table(
            User.__tablename__,
            md,
            autoload=True,
            autoload_with=self.engine
        )
        if '_created_datetime' not in user_table.c:
            print "Altering table {} to add created_datetime column"
            c_col = Column(
                'created_datetime',
                DateTime,
                default=datetime.datetime.utcnow,
                nullable=False
            )
            c_col.create(user_table, populate_default=True)

        if '_updated_datetime' not in user_table.c:
            print "Altering table {} to add updated_datetime column"
            u_col = Column(
                'updated_datetime',
                DateTime,
                default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow,
                nullable=False
            )
            u_col.create(user_table, populate_default=True)
