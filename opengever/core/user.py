from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
import random

def get_random_user(portal):
    vocabulary_factory = getUtility(
        IVocabularyFactory, name='opengever.ogds.base.UsersVocabulary')
    users = vocabulary_factory(portal)
    return random.sample(users, 1)[0].value
