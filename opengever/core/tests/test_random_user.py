from opengever.testing import FunctionalTestCase
from opengever.testing import create_ogds_user
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from opengever.core.user import get_random_user

class TestGetRandomUser(FunctionalTestCase):

    def setUp(self):
        super(TestGetRandomUser, self).setUp()
        create_ogds_user('hugo.boss', firstname='Hugo', lastname='Boss')
        create_ogds_user('peter.muster', firstname='Peter', lastname='Muster')
        create_ogds_user('hanspeter.linder', firstname='Hans-peter', lastname='Linder')

    def test_get_random_user(self):
        self.vocabulary_factory = getUtility(
            IVocabularyFactory, name='opengever.ogds.base.UsersVocabulary')
        self.assertInTerms(get_random_user(self.layer['portal']), self.vocabulary_factory(self.layer['portal']))
