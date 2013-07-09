from opengever.testing import FunctionalTestCase
from opengever.core.builder import Builder


class TestGetRandomUser(FunctionalTestCase):

    def setUp(self):
        super(TestGetRandomUser, self).setUp()

    def test_random_builder(self):
        builder = Builder("gever")
        builder(1, 1)
        cat = self.layer['portal'].portal_catalog
        dossiers = cat.search({'portal_type':'opengever.dossier.businesscasedossier'})
        self.assertEqual(1, len(dossiers), "We don't have the right number of dossiers we expected 1 got %s" % len(dossiers))
        docs = cat.search({'portal_type':'opengever.document.document'})
        self.assertEqual(1, len(docs), "We don't have the right number of documents we expected 1 got %s" % len(docs))
