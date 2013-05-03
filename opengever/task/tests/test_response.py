from opengever.task.adapters import IResponseContainer
from opengever.task.interfaces import ISuccessorTaskController
from opengever.task.task import ITask
from opengever.task.testing import OPENGEVER_TASK_FUNCTIONAL_TESTING
from opengever.task.util import add_simple_response
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME, TEST_USER_PASSWORD
from plone.app.testing import setRoles, login
from plone.dexterity.utils import createContentInContainer
from plone.testing.z2 import Browser
import transaction
import unittest2 as unittest
import urllib


class TestResponse(unittest.TestCase):

    layer = OPENGEVER_TASK_FUNCTIONAL_TESTING

    def setUp(self):

        self.portal = self.layer['portal']
        self.portal.portal_types['opengever.task.task'].global_allow = True

        setRoles(
            self.portal, TEST_USER_ID, ['Contributor', 'Editor'])
        login(self.portal, TEST_USER_NAME)

        self.dossier = createContentInContainer(
            self.portal, 'opengever.dossier.businesscasedossier',
            checkConstraints=False)

        self.task = createContentInContainer(
            self.dossier, 'opengever.task.task', checkConstraints=False,
            title="Test task 1", issuer=TEST_USER_ID, text=u'',
            responsible='testuser2', responsible_client='client2',
            task_type="direct-execution")

        self.successor = createContentInContainer(
            self.dossier, 'opengever.task.task', checkConstraints=False,
            title="Test task 1", responsible='testuser2',
            issuer=TEST_USER_ID, text=u'',
            task_type="direct-execution", responsible_client='client2')

        self.doc1 = createContentInContainer(
            self.dossier, 'opengever.document.document',
            checkConstraints=False, title="Doc 1")

        self.doc2 = createContentInContainer(
            self.dossier, 'opengever.document.document',
            checkConstraints=False, title="Doc 2")

        transaction.commit()

        self.browser = Browser(self.layer['app'])
        self.browser.handleErrors = False
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (
                TEST_USER_NAME, TEST_USER_PASSWORD))

    def test_response_view(self):
        # test added objects info
        add_simple_response(
            self.task, text=u'field', added_object=[self.doc1, self.doc2])

        # test field changes info
        add_simple_response(
            self.task, text=u'field',
            field_changes=(
                (ITask['responsible'], TEST_USER_ID),
                (ITask['responsible_client'], 'plone'),
                ),
            transition=u'task-transition-open-in-progress')

        # test successsor info
        successor_oguid = ISuccessorTaskController(self.successor).get_oguid()
        add_simple_response(self.task, successor_oguid=successor_oguid)

        transaction.commit()

        self.assertEquals(len(IResponseContainer(self.task)), 3)

        # test different responeses and their infos
        self.browser.open(
            '%s/tabbedview_view-overview' % self.task.absolute_url())

        successor_info = """<span class="label">
                        Added successor task
                    </span>
                    <span class="issueChange"><span class="wf-task-state-open"><a href="http://nohost/plone/dossier-1/task-2" title="[plone] > dossier-1 > Test task 1"><span class="rollover-breadcrumb icon-task-remote-task">Test task 1</span></a>  <span class="discreet">(client2 / <a href="http://nohost/plone/@@user-details/testuser2">User 2 Test (testuser2)</a>)</span></span></span>"""

        self.assertTrue(successor_info in self.browser.contents)

        responsible_change_info = """<span class="label">label_responsible</span>
                    <span class="issueChange"><a href="http://nohost/plone/@@user-details/testuser2">User 2 Test (testuser2)</a></span>
                    &rarr;
                    <span class="issueChange"><a href="http://nohost/plone/@@user-details/test_user_1_">User Test (test_user_1_)</a></span>"""

        self.assertTrue(responsible_change_info in self.browser.contents)

        doc_added_info = """<a href="http://nohost/plone/dossier-1/document-1" class="contenttype-opengever-document-document">
	                            <span>Doc 1</span>
	                        </a>"""

        self.assertTrue(doc_added_info in self.browser.contents)

        # edit and delete should not be possible
        edit_button = '<input class="context" type="submit" value="Edit" />'
        delete_button = '<input class="destructive" type="submit" value="Delete" />'

        self.assertTrue(edit_button not in self.browser.contents)
        self.assertTrue(delete_button not in self.browser.contents)

    def test_add_form(self):
        data = {'form.widgets.transition':'task-transition-open-in-progress'}
        self.browser.open('%s/addresponse' % self.task.absolute_url(),
                          data=urllib.urlencode(data))

        # the label should be adjusted with the given transition
        title = '<h1 class="documentFirstHeading">Test task 1: ' \
            'task-transition-open-in-progress</h1>'
        self.assertTrue(title in self.browser.contents)

        self.browser.getControl(
            name="form.widgets.text").value = "Lorem ipsum"
        self.browser.getControl(
            name="form.buttons.save").click()

        self.assertEquals(len(IResponseContainer(self.task)), 1)

    def test_add_form_with_related_items(self):
        self.browser.open('%s/addresponse' % self.task.absolute_url())

        #Get Control over the Query Field and enter a value.
        self.browser.getControl(
            name="form.widgets.relatedItems.widgets.query").value = u"Doc 1"
        #Click the Searchbutton
        self.browser.getControl(
            name="form.widgets.relatedItems.buttons.search").click()

        self.browser.getControl("Doc 1").selected = True

        self.browser.getControl(name="form.buttons.save").click()

        self.assertEquals(len(IResponseContainer(self.task)), 1)
        self.assertEquals(self.task.relatedItems[0].to_object, self.doc1)