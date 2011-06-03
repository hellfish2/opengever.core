from opengever.ogds.base.interfaces import IClient
from opengever.ogds.base.model.user import Group, Base
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import ForeignKey
from zope.interface import implements



class Client(Base):
    """Client model
    """

    implements(IClient)

    __tablename__ = 'clients'

    client_id = Column(String(30), primary_key=True)
    title = Column(String(30))
    enabled = Column(Boolean(), default=True)
    ip_address = Column(String(15))
    site_url = Column(String(100))
    public_url = Column(String(100))

    # #ehemals group
    # users_group_id = Column(String(), ForeignKey('groups.group_id'))
    # users_group = relationship(Group, backref=backref('group_client')) 
    # 
    # inbox_group_id = Column(String(), ForeignKey('groups.group_id'))
    # inbox_group = relationship(Group, backref=backref('inbox_group_client'))

    def __init__(self, client_id, **kwargs):
        self.client_id = client_id
        for key, value in kwargs.items():
            # provoke a AttributeError
            getattr(self, key)
            setattr(self, key, value)

    def __repr__(self):
        return '<Client %s>' % self.client_id
