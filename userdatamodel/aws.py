from .user import User
from . import Base
from sqlalchemy import (
    Integer, String, Column, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
import json


class AWSHMACKeyPair(Base):
    __tablename__ = "aws_hmac_keypair"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship("User", backref="aws_hmac_keypairs")

    access_key = Column(String, unique=True)

    create_date = Column(DateTime, nullable=False)
    status = Column(String)

    def archive_keypair(self, session):
        archive = AWSHMACKeyPairArchive(
            user_id=self.user_id,
            access_key=self.access_key,
            create_date=self.create_date,
            status=self.status)
        session.add(archive)
        session.delete(self)
        session.commit()

    def __str__(self):
        str_out = {
            'id': self.id,
            'user_id': self.user_id,
            'access_key': self.access_key,
            'create_date': self.create_date,
            'status': self.status,
        }
        return json.dumps(str_out)

    def __repr__(self):
        return self.__str__()


class AWSHMACKeyPairArchive(Base):
    '''
    Archvie table to store deleted aws keypair
    '''
    __tablename__ = "aws_hmac_keypair_archive"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship("User", backref="aws_archive_keypairs")

    access_key = Column(String, unique=True)

    create_date = Column(DateTime, nullable=False)
    status = Column(String)
