from opengever.testing import FunctionalTestCase
from ftw.builder import Builder
from ftw.builder import session
from ftw.builder import create
from opengever.core.builder import get_repo_folders
from opengever.testing import create_ogds_user
import os


class TestGetRandomUser(FunctionalTestCase):

    def setUp(self):
        session.current_session = session.factory()
        session.current_session.file_path = os.path.split(__file__)[0] + '/files'
        session.current_session.get_docs_in_dossier = lambda x: x
        create(Builder('repository').titled(u'Test'))
        session.current_session.repofolders = list(get_repo_folders())
        create_ogds_user('hugo.boss', firstname='Hugo', lastname='Boss')
        create_ogds_user('peter.muster', firstname='Peter', lastname='Muster')
        create_ogds_user('hanspeter.linder', firstname='Hans-peter', lastname='Linder')
        super(TestGetRandomUser, self).setUp()

    def test_random_builder(self):
        create(Builder('gever').having(**{'num_dossiers': 1, 'num_files': 1}))
        cat = self.layer['portal'].portal_catalog
        dossiers = cat.search({'portal_type':'opengever.dossier.businesscasedossier'})
        self.assertEqual(1, len(dossiers), "We don't have the right number of dossiers we expected 1 got %s" % len(dossiers))
        docs = cat.search({'portal_type':'opengever.document.document'})
        self.assertEqual(1, len(docs), "We don't have the right number of documents we expected 1 got %s" % len(docs))
