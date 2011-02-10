from ftw.contentmenu.interfaces import IContentmenuPostFactoryMenu
from Acquisition import aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from five import grok
from opengever.inbox.inbox import IInbox
from opengever.ogds.base.utils import get_client_id
from opengever.task import _ as task_mf
from opengever.task.task import ITask, Task
from plone.directives import form
from plone.directives.dexterity import AddForm
from z3c.form.interfaces import HIDDEN_MODE
from zope import schema
from zope.app.container.interfaces import IObjectAddedEvent
from zope.interface import implements, Interface


class IForwarding(ITask):
    """Schema interface for forwardings.
    """

    # common fieldset
    form.omitted('task_type')

    # only hide relatedItems - we need it for remembering which documents
    # should be moved after creation when creating forwarding from tabbed view.
    form.mode(relatedItems=HIDDEN_MODE)

    # additional fieldset
    form.omitted('expectedStartOfWork')
    form.omitted('expectedDuration')
    form.omitted('expectedCost')
    form.omitted('effectiveDuration')
    form.omitted('effectiveCost')
    form.omitted('date_of_completion')

    # deadline is not required
    deadline = schema.Date(
        title=task_mf(u"label_deadline", default=u"Deadline"),
        description=task_mf(u"help_deadline", default=u""),
        required=False,
        )


class Forwarding(Task):
    """Forwarding model class.
    """
    implements(IForwarding)

    @property
    def task_type_category(self):
        return None

    def get_static_task_type(self):
        # Provide a marker string, which will be translated in the
        # tabbedview helper method.
        return 'forwarding_task_type'

    def set_static_task_type(self, value):
        # do not file when trying to set the task type - but ignore
        return

    task_type = property(get_static_task_type, set_static_task_type)


class AddForm(AddForm):
    """Provide a custom add-form which adds the selected documents
    (tabbed_view) to the hidden relatedItems field and sets some defaults.
    The documents are later moved by move_documents_into_forwarding (see
    below).
    """
    grok.name('opengever.inbox.forwarding')

    def update(self):
        # put default value for relatedItems into request - the added
        # objects will later be moved insed the forwarding

        paths = self.request.get('paths', [])
        if paths:
            utool = getToolByName(self.context, 'portal_url')
            portal_path = utool.getPortalPath()
            # paths have to be relative to the portal
            paths = [path[len(portal_path):] for path in paths]
            self.request.set('form.widgets.relatedItems', paths)

        # put default value for issuer into request
        if not self.request.get('form.widgets.issuer', None):
            self.request.set('form.widgets.issuer',
                             u'inbox:%s' % get_client_id())

        # put the default responsible into the request
        if not self.request.get('form.widgets.responsible_client', None):
            client = get_client_id()
            self.request.set('form.widgets.responsible_client', client)
            self.request.set('form.widgets.responsible',
                             [(u'inbox:%s' % client).encode('utf-8')])

        super(AddForm, self).update()


@grok.subscribe(IForwarding, IObjectAddedEvent)
def move_documents_into_forwarding(context, event):
    """When selecting documents in the tabbed view and creating a
    forwarding with this documents, they'll be added to the hidden field
    "relatedItems" (see custom AddForm above) - which is not yet the right
    place. After saving the forwarding, we need to move the documents into
    the forwarding (which did not exist before).
    """

    relations = context.relatedItems
    for relation in relations:
        obj = relation.to_object
        clipboard = aq_parent(aq_inner(obj)).manage_cutObjects(obj.id)
        context.manage_pasteObjects(clipboard)
    context.relatedItems = []


class RemoveForwardingFactoryMenuEntry(grok.MultiAdapter):
    """In Inboxes we should not be able to add forwardings using the factory
    menu, but only by selecting a task and clicking the "Forward"
    folder_contents button in the documents tab.
    So we need to remove the "create forwarding" action from the factory
    menu.
    """

    grok.adapts(IInbox, Interface)
    grok.implements(IContentmenuPostFactoryMenu)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, factories):
        new_factories = []

        for factory in factories:
            if isinstance(factory, dict) and \
                    factory.get('id', None) == 'opengever.inbox.forwarding':
                # remove the forwarding action
                pass

            else:
                new_factories.append(factory)

        return new_factories