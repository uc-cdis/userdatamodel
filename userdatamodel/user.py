from . import Base
from sqlalchemy import Integer, String, Column, Table, Boolean,BigInteger, DateTime, text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgres import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import LargeBinary

class UserAccess(object):
    __tablename__ = "user_access"
    user_id = Column('user_id', Integer, ForeignKey('user.id')),
    user = relationship('user', backref='user_access')

    project_id = Column('project_id', Integer, ForeignKey('project.id'))

    project = relationship('Project', backref='user_accesses')
    privilege = Column("privilege", ARRAY(String))

    provider_id = Column(Integer, ForeignKey('authorization_provider.id'))
    auth_provider = relationship('AuthorizationProvider', backref='acls')

user_group = Table(
    'user_group', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('group_id', Integer, ForeignKey('research_group.id'))
)

class ResearchGroup(Base):
    __tablename__ = "research_group"

    id = Column(Integer, primary_key=True)
    name = Column(Integer, unique=True)

    lead_id = Column(Integer, ForeignKey('user.id'))
    lead = relationship('User', backref='lead_group')


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(40), unique=True)

    idp_id = Column(Integer, ForeignKey('identity_provider.id'))
    identity_provider = relationship('IdentityProvider', backref='users')

    research_groups = relationship("ResearchGroup", secondary=user_group, backref='users')

    active = Column(Boolean)
    project_access = association_proxy(
        "user_accesses",
        "project")


class IdentityProvider(Base):
    __tablename__ = 'identity_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    
class AuthorizationProvider(Base):
    __tablename__ = 'authorization_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

class Bucket(Base):
    __tablename__ = 'bucket'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    provider_id = Column(Integer, ForeignKey('storage_provider.id'))
    provider = relationship('StorageProvider', backref='buckets')


class StorageProvider(Base):
    __tablename__ = 'storage_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    host = Column(String, unique=True)
    description = Column(String)


class ComputeProvider(Base):
    __tablename__ = 'compute_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    auth_url = Column(String, unique=True)
    description = Column(String)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    parent_id = Column(Integer, ForeignKey('project.id'))
    parent = relationship('Project', backref='sub_projects', remote_side=[id])

class ComputeQuota(Base):
    __tablename__ = "compute_quota"

    id = Column(Integer, primary_key=True)

    # compute quota can be linked to a project/research group/user
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', backref='compute_quota')

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref='compute_quota')

    group_id = Column(Integer, ForeignKey('research_group.id'))
    research_group = relationship('ResearchGroup', backref='compute_quota')

    provider_id = Column(Integer, ForeignKey('compute_provider.id'))
    provider = relationship('ComputeProvider', backref='compute_quota')

    instances = Column(Integer)
    cores = Column(Integer)
    ram = Column(BigInteger)
    floating_ips = Column(Integer)


class StorageQuota(Base):
    __tablename__ = "storage_quota"

    id = Column(Integer, primary_key=True)

    # storage quota can be linked to a project/research group/user
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', backref='storage_quota')

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref='storage_quota')

    group_id = Column(Integer, ForeignKey('research_group.id'))
    research_group = relationship('ResearchGroup', backref='storage_quota')

    provider_id = Column(Integer, ForeignKey('storage_provider.id'))
    provider = relationship('StorageProvider', backref='storage_quota')

    max_objects = Column(BigInteger)
    max_size = Column(BigInteger)
    max_buckets = Column(Integer)

class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True)
    action = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    target = Column(String)
    target_type = Column(String)
    description = Column(String)

# application related tables

class Application(Base):
    __tablename__ = "application"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref='application')
    resources_granted = Column(ARRAY(String)) # eg: ["compute", "storage"]
    certificates_uploaded = relationship(
        "Certificate",
        backref='user',
    )
    message = Column(String)


class Certificate(Base):
    __tablename__ = "certificate"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('application.id'))
    name = Column(String(40))
    data = Column(LargeBinary)

