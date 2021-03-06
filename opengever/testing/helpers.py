from Products.CMFCore.utils import getToolByName
from opengever.globalindex.interfaces import ITaskQuery
from opengever.ogds.base.utils import get_client_id
from zope.component import getUtility
from zope.intid.interfaces import IIntIds


def create_plone_user(portal, userid, password='demo09'):
    acl_users = getToolByName(portal, 'acl_users')
    acl_users.source_users.addUser(userid, userid, password)


def obj2brain(obj):
    catalog = getToolByName(obj, 'portal_catalog')
    query = {'path':
             {'query': '/'.join(obj.getPhysicalPath()),
              'depth': 0}}
    brains = catalog(query)
    if len(brains) == 0:
        raise Exception('Not in catalog: %s' % obj)
    else:
        return brains[0]


def index_data_for(obj):
    catalog = getToolByName(obj, 'portal_catalog')
    return catalog.getIndexDataForRID(obj2brain(obj).getRID())


def task2sqltask(obj):
    query = getUtility(ITaskQuery)
    return query.get_task(
        getUtility(IIntIds).getId(obj), get_client_id())
