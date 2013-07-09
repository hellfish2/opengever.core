from opengever.core.file import get_random_file
from opengever.testing import FunctionalTestCase
import os
from plone.namedfile.file import NamedBlobFile

class TestRandomFile(FunctionalTestCase):

    def test_get_existing_file(self):
        file_ = get_random_file(os.path.split(__file__)[0] + '/files')
        self.assertTrue(file_ != None)
        self.assertEqual(NamedBlobFile, file_.__class__)

    def test_get_files_from_empty(self):
        with self.assertRaises(KeyError) as cm:
            get_random_file(os.path.split(__file__)[0] + '/hans')
        self.assertEqual('No files were Found in the given folder', cm.exception.message)
