from Products.CMFCore.utils import getToolByName
from opengever.dossier.testing import OPENGEVER_DOSSIER_FUNCTIONAL_TESTING
from plone.app.testing import setRoles, TEST_USER_ID
from plone.testing.z2 import Browser
from plone.app.testing import TEST_USER_NAME, TEST_USER_PASSWORD
import json
import transaction
import unittest2 as unittest

class TestOpenDossiersJson(unittest.TestCase):

    layer = OPENGEVER_DOSSIER_FUNCTIONAL_TESTING

    def setUp(self):
        super(TestOpenDossiersJson, self).setUp()
        self.portal = self.layer['portal']

    def test_renders_json_containing_all_open_dossiers(self):
        self.store_dossiers(2)
        transaction.commit()

        self.visit("http://nohost/plone/list-open-dossiers-json")
        self.assertEquals("application/json", self.browser.headers['Content-Type'])

        json_data = json.loads(self.browser.contents)

        self.assertEquals(json_data,
            [{
                u'url': u'http://nohost/plone/testdossier-1',
                u'path': u'testdossier-1',
                u'review_state': u'dossier-state-active',
                u'title': u'Testdossier 1',
                u'reference_number': u'OG / 1'
            },
            {
                u'url': u'http://nohost/plone/testdossier-2',
                u'path': u'testdossier-2',
                u'review_state': u'dossier-state-active',
                u'title': u'Testdossier 2',
                u'reference_number': u'OG / 2'
            }])

    def test_does_not_include_resolved_dossiers(self):
        self.store_dossiers(1)
        self.resolve_dossier(self.portal.get('testdossier-1'))
        transaction.commit()

        self.visit("http://nohost/plone/list-open-dossiers-json")

        json_data = json.loads(self.browser.contents)
        self.assertEquals([], json_data,
                          "the JSON should not contain resolved dossiers")

    def store_dossiers(self, number, title = "Testdossier"):
        for i in range(1, number + 1):
            handle = '%s-%s' % (title.lower(), i)
            self.portal.invokeFactory(
                'opengever.dossier.businesscasedossier',
                handle,
                title='%s %s' % (title, i))

            obj = self.portal.get(handle)
            obj.reindexObject(idxs=['modified'])

    def resolve_dossier(self, dossier):
        setRoles(self.portal, TEST_USER_ID, ['Reviewer', 'Manager'])
        workflow = getToolByName(self.portal, 'portal_workflow')
        workflow.doActionFor(dossier, 'dossier-transition-resolve')

    def visit(self, path):
        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (TEST_USER_NAME, TEST_USER_PASSWORD,))
        self.browser.open(path)