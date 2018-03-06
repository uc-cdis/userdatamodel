from . import Base
import datetime
from sqlalchemy import (
    Integer, String, Column, Table, Boolean, BigInteger, DateTime, text)
from sqlalchemy import UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import LargeBinary
from sqlalchemy.orm.collections import MappedCollection, collection
import json


class PrivilegeDict(MappedCollection):
    '''
    PrivilegeDict is used to populate the list of all privileges
    a user by the project_id.
    User can have privilege access to a project via multiple groups,
    the list of privileges of a user in a project should be a union
    of all groups that user belongs.
    For example: user_1, group_1, project_1: [read-storage]
                 user_1, group_2, project_1: [write-storage]
                 --> user_1, project_1: [read-storage, write-storage]
    '''
    def __init__(self):
        MappedCollection.__init__(self, keyfunc=lambda node: node.project_id)

    @collection.internally_instrumented
    def __setitem__(self, key, value, _sa_initiator=None):
        # do something with key, value
        if self.has_key(key):
            for item in value.privilege:
                if item not in self[key].privilege:
                    self[key].privilege.append(item)
        else:
            super(PrivilegeDict, self).__setitem__(key, value, _sa_initiator)


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(40), unique=True)

    # id from identifier, which is not guarenteed to be unique
    # across all identifiers.
    # For most of the cases, it will be same as username
    id_from_idp = Column(String)
    email = Column(String)

    idp_id = Column(Integer, ForeignKey('identity_provider.id'))
    identity_provider = relationship('IdentityProvider', backref='users')

    google_proxy_group_id = Column(
        String(90), ForeignKey('google_proxy_group.id'))

    google_proxy_group = relationship(
        'GoogleProxyGroup', backref=backref(__tablename__, uselist=False))

    department_id = Column(Integer, ForeignKey('department.id'))
    department = relationship('Department', backref='users')

    groups = association_proxy(
        'user_to_groups',
        'group')

    group_privileges = relationship(
        'AccessPrivilege', primaryjoin='user_to_group.c.user_id==User.id',
        secondary='join(AccessPrivilege, Group, AccessPrivilege.group_id==Group.id).'
                  'join(user_to_group, Group.id == user_to_group.c.group_id)',
        collection_class=PrivilegeDict,
    )
    group_accesses = association_proxy('group_privileges',
                                       'privilege',
                                       creator=lambda k, v: AccessPrivilege(privilege=v, pj=k))

    active = Column(Boolean)
    is_admin = Column(Boolean, default=False)

    projects = association_proxy(
        'accesses_privilege',
        'project')

    project_access = association_proxy(
        'accesses_privilege',
        'privilege',
        creator=lambda k, v: AccessPrivilege(privilege=v, pj=k)
        )

    buckets = association_proxy(
        'user_to_buckets',
        'bucket')

    application = relationship('Application', backref='user', uselist=False)

    def __str__(self):
        str_out = {
            'id': self.id,
            'username': self.username,
            'id_from_idp': self.id_from_idp,
            'idp_id': self.idp_id,
            'department_id': self.department_id,
            'active': self.active,
            'is_admin': self.is_admin,
            'group_privileges': str(self.group_privileges),
            'group_accesses': str(self.group_accesses),
            'projects': str(self.projects),
            'project_access': str(self.project_access)
        }
        return json.dumps(str_out)

    def __repr__(self):
        return self.__str__()


class GoogleProxyGroup(Base):
    __tablename__ = "google_proxy_group"

    id = Column(String(90), primary_key=True)

    email = Column(
        String,
        unique=True,
        nullable=False
    )


class HMACKeyPair(Base):
    __tablename__ = 'hmac_keypair'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship('User', backref='hmac_keypairs')

    access_key = Column(String)
    # AES-128 encrypted
    secret_key = Column(String)

    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    expire = Column(Integer)
    active = Column(Boolean, default=True)

    @property
    def expiration_time(self):
        return self.timestamp + datetime.timedelta(seconds=self.expire)

    def check_and_archive(self, session):
        if self.expiration_time < datetime.datetime.utcnow():
            self.archive_keypair(session)
            return True
        return False

    def archive_keypair(self, session):
        archive = HMACKeyPairArchive(
            user_id=self.user_id,
            access_key=self.access_key,
            secret_key=self.secret_key,
            timestamp=self.timestamp,
            expire=self.expire)
        session.add(archive)
        session.delete(self)
        session.commit()

    def __str__(self):
        str_out = {
            'id': self.id,
            'user_id': self.user_id,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'timestamp': self.timestamp,
            'expire': self.expire,
            'active': self.active
        }
        return json.dumps(str_out)

    def __repr__(self):
        return self.__str__()


class HMACKeyPairArchive(Base):
    '''
    Archive table to store expired or deleted keypair
    '''
    __tablename__ = 'hmac_keypair_archive'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship('User', backref='archive_keypairs')

    access_key = Column(String)
    # AES-128 encrypted
    secret_key = Column(String)

    timestamp = Column(DateTime, nullable=False)
    expire = Column(Integer)


class UserToGroup(Base):
    '''
    Edge table between user and group
    '''
    __tablename__ = 'user_to_group'
    user_id = Column('user_id', Integer, ForeignKey('User.id'), primary_key=True)
    user = relationship(
        User,
        backref=backref('user_to_groups', cascade='all, delete-orphan')
    )

    group_id = Column('group_id', Integer, ForeignKey('Group.id'), primary_key=True)
    group = relationship(
        'Group',
        backref=backref('user_to_groups', cascade='all, delete-orphan')
    )

    roles = Column('roles', ARRAY(String))


class AccessPrivilege(Base):
    '''
    A group/user's privileges on a project.
    The group and user columns should be mutually exclusive
    '''
    __tablename__ = 'access_privilege'
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'project_id', name='uniq_ap'),
        CheckConstraint(
            'user_id is NULL or group_id is NULL',
            name='check_access_subject'),
        Index('unique_group_project_id', 'group_id', 'project_id', unique=True,
              postgresql_where=text('user_id is NULL')),
        Index('unique_user_project_id', 'user_id', 'project_id', unique=True,
              postgresql_where=text('group_id is NULL')),
        Index('unique_user_group_id', 'user_id', 'group_id', unique=True,
              postgresql_where=text('project_id is NULL'))
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(
        User,
        backref=backref('accesses_privilege',
                        collection_class=attribute_mapped_collection('pj'),
                        cascade="all, delete-orphan",
                        )
    )

    group_id = Column(Integer, ForeignKey('Group.id'))
    group = relationship(
        'Group',
        backref=backref('accesses_privilege', cascade='all, delete-orphan')
    )

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(
        'Project',
        backref=backref('accesses_privilege', cascade='all, delete-orphan')
    )
    pj = association_proxy('project', 'auth_id')

    privilege = Column(ARRAY(String))
    provider_id = Column(Integer, ForeignKey('authorization_provider.id'))
    auth_provider = relationship('AuthorizationProvider', backref='acls')

    def __str__(self):
        str_out = {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'group_id': self.group_id,
            'privilege': self.privilege,
            'provider_id': self.provider_id
        }
        return json.dumps(str_out)

    def __repr__(self):
        return self.__str__()


class UserToBucket(Base):
    __tablename__ = 'user_to_bucket'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(
        User,
        backref=backref('user_to_buckets', cascade='all, delete-orphan')
    )

    bucket_id = Column(Integer, ForeignKey('bucket.id'))

    bucket = relationship(
        'Bucket',
        backref=backref('user_to_buckets', cascade='all, delete-orphan')
    )
    privilege = Column(ARRAY(String))


class Group(Base):
    __tablename__ = 'Group'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

    users = association_proxy(
        'user_to_groups',
        'user')


class IdentityProvider(Base):
    __tablename__ = 'identity_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

    google = "google"
    itrust = "itrust"
    fence = "fence"


class AuthorizationProvider(Base):
    __tablename__ = 'authorization_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)


class Bucket(Base):
    __tablename__ = 'bucket'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    provider_id = Column(Integer, ForeignKey('cloud_provider.id'))
    provider = relationship('CloudProvider', backref='buckets')
    users = association_proxy(
        'user_to_buckets',
        'user')


class CloudProvider(Base):
    __tablename__ = 'cloud_provider'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    endpoint = Column(String, unique=True)
    backend = Column(String)
    description = Column(String)
    # type of service, can be compute, storage, or general
    service = Column(String)


class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    # identifier recognozied by the authorization provider
    auth_id = Column(String, unique=True)
    description = Column(String)
    parent_id = Column(Integer, ForeignKey('project.id'))
    parent = relationship('Project', backref='sub_projects', remote_side=[id])
    buckets = association_proxy(
        'project_to_buckets',
        'bucket')

    def __str__(self):
        str_out = {
            'id': self.id,
            'name': self.name,
            'auth_id': self.auth_id,
            'description': self.description,
            'parent_id': self.parent_id
        }
        return json.dumps(str_out)

    def __repr__(self):
        return self.__str__()


class ProjectToBucket(Base):
    __tablename__ = 'project_to_bucket'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(
        Project,
        backref=backref('project_to_buckets', cascade='all, delete-orphan')
    )

    bucket_id = Column(Integer, ForeignKey('bucket.id'))

    bucket = relationship('Bucket', backref='project_to_buckets')
    privilege = Column(ARRAY(String))


class ComputeAccess(Base):
    __tablename__ = 'compute_access'

    id = Column(Integer, primary_key=True)

    # compute access can be linked to a project/research group/user
    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', backref='compute_access')

    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship('User', backref='compute_access')

    group_id = Column(Integer, ForeignKey('Group.id'))
    group = relationship('Group', backref='compute_access')

    provider_id = Column(Integer, ForeignKey('cloud_provider.id'))
    provider = relationship('CloudProvider', backref='compute_access')

    instances = Column(Integer)
    cores = Column(Integer)
    ram = Column(BigInteger)
    floating_ips = Column(Integer)
    additional_info = Column(JSONB)


class StorageAccess(Base):
    '''
    storage access from a project/research group/user to a cloud_provider
    the project/group/user should be mutually exclusive
    '''
    __tablename__ = 'storage_access'

    __table_args__ = (
        CheckConstraint(
            'user_id is NULL or group_id is NULL or project_id is NULL',
            name='check_storage_subject'),
    )
    id = Column(Integer, primary_key=True)

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship('Project', backref='storage_access')

    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship('User', backref='storage_access')

    group_id = Column(Integer, ForeignKey('Group.id'))
    group = relationship('Group', backref='storage_access')

    provider_id = Column(Integer, ForeignKey('cloud_provider.id'))
    provider = relationship('CloudProvider', backref='storage_access')

    max_objects = Column(BigInteger)
    max_size = Column(BigInteger)
    max_buckets = Column(Integer)
    additional_info = Column(JSONB)


class EventLog(Base):
    __tablename__ = 'event_log'

    id = Column(Integer, primary_key=True)
    action = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    target = Column(String)
    target_type = Column(String)
    description = Column(String)


class Organization(Base):
    __tablename__ = 'organization'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)


class Department(Base):
    __tablename__ = 'department'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)

    org_id = Column(Integer, ForeignKey('organization.id'))
    organization = relationship('Organization', backref='departments')


# application related tables

class Application(Base):
    __tablename__ = 'application'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    resources_granted = Column(ARRAY(String))  # eg: ['compute', 'storage']
    certificates_uploaded = relationship(
        'Certificate',
        backref='user',
    )
    message = Column(String)


class Certificate(Base):
    __tablename__ = 'certificate'

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey('application.id'))
    name = Column(String(40))
    extension = Column(String)
    data = Column(LargeBinary)

    @property
    def filename(self):
        return '{}.{}'.format(self.name, self.extension)


class S3Credential(Base):
    __tablename__ = 's3credential'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship('User', backref='s3credentials')

    access_key = Column(String)

    timestamp = Column(
        DateTime, nullable=False, default=datetime.datetime.utcnow)
    expire = Column(Integer)
