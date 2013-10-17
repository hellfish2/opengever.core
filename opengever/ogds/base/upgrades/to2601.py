from Products.LDAPMultiPlugins.interfaces import ILDAPMultiPlugin
from ftw.upgrade import UpgradeStep


class ActivateLDAPCaching(UpgradeStep):

    def __call__(self):
        for item in self.portal.get('acl_users').objectValues():
            if ILDAPMultiPlugin.providedBy(item):
                item.ZCacheable_setManagerId('RAMCache')
                item.ZCacheable_setEnabled(1)
