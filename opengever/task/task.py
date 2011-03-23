from Acquisition import aq_parent, aq_inner
from collective import dexteritytextindexer
from datetime import datetime, timedelta
from five import grok
from ftw.tabbedview.browser.listing import ListingView
from ftw.table import helper
from ftw.table.basesource import BaseTableSource
from ftw.table.interfaces import ITableSource, ITableSourceConfig
from opengever.base.browser.helper import client_title_helper
from opengever.base.interfaces import ISequenceNumber
from opengever.base.source import DossierPathSourceBinder
from opengever.globalindex.utils import indexed_task_link
from opengever.ogds.base.autocomplete_widget import AutocompleteFieldWidget
from opengever.ogds.base.interfaces import IContactInformation
from opengever.ogds.base.utils import get_client_id
from opengever.tabbedview.browser.tabs import Documents
from opengever.tabbedview.browser.tabs import OpengeverTab
from opengever.tabbedview.helper import readable_ogds_author
from opengever.task import util
from opengever.task import _
from opengever.task.helper import linked
from opengever.task.helper import path_checkbox
from opengever.task.interfaces import ISuccessorTaskController
from operator import attrgetter
from plone.dexterity.content import Container
from plone.directives import form, dexterity
from plone.directives.dexterity import DisplayForm
from plone.indexer import indexer
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName
from z3c.relationfield.schema import RelationChoice, RelationList
from zc.relation.interfaces import ICatalog
from zope import schema
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility, getMultiAdapter
from zope.interface import implements, Interface
from zope.schema.vocabulary import getVocabularyRegistry



class ITask(form.Schema):

    form.fieldset(
        u'common',
        label = _(u'fieldset_common', default=u'Common'),
        fields = [
            u'title',
            u'issuer',
            u'task_type',
            u'responsible_client',
            u'responsible',
            u'deadline',
            u'text',
            u'relatedItems',
            ],
        )

    form.fieldset(
        u'additional',
        label = _(u'fieldset_additional', u'Additional'),
        fields = [
            u'expectedStartOfWork',
            u'expectedDuration',
            u'expectedCost',
            u'effectiveDuration',
            u'effectiveCost',
            u'date_of_completion',
            ],
        )

    dexteritytextindexer.searchable('title')
    title = schema.TextLine(
        title=_(u"label_title", default=u"Title"),
        description=_('help_title', default=u""),
        required = True,
        )

    form.widget(issuer=AutocompleteFieldWidget)
    issuer = schema.Choice(
        title =_(u"label_issuer", default=u"Issuer"),
        description = _('help_issuer', default=u""),
        vocabulary=u'opengever.ogds.base.ContactsAndUsersVocabulary',
        required = True,
        )

    form.widget(task_type='z3c.form.browser.radio.RadioFieldWidget')
    task_type = schema.Choice(
        title =_(u'label_task_type', default=u'Task Type'),
        description = _('help_task_type', default=u''),
        required = True,
        readonly = False,
        default = None,
        missing_value = None,
        source = util.getTaskTypeVocabulary,
        )

    responsible_client = schema.Choice(
        title=_(u'label_resonsible_client',
                default=u'Responsible Client'),
        description=_(u'help_responsible_client',
                      default=u''),
        vocabulary='opengever.ogds.base.ClientsVocabulary',
        required=True)

    form.widget(responsible=AutocompleteFieldWidget)
    responsible = schema.Choice(
        title=_(u"label_responsible", default=u"Responsible"),
        description =_(u"help_responsible", default=""),
        vocabulary=u'opengever.ogds.base.UsersAndInboxesVocabulary',
        required = True,
        )

    deadline = schema.Date(
        title=_(u"label_deadline", default=u"Deadline"),
        description=_(u"help_deadline", default=u""),
        required = True,
        )

    date_of_completion = schema.Date(
        title=_(u"label_date_of_completion", default=u"Date of completion"),
        description=_(u"help_date_of_completion", default=u""),
        required = False,
        )

    dexteritytextindexer.searchable('text')
    form.primary('text')
    text = schema.Text(
        title=_(u"label_text", default=u"Text"),
        description=_(u"help_text", default=u""),
        required = False,
        )

    relatedItems = RelationList(
        title=_(u'label_related_items', default=u'Related Items'),
        default=[],
        value_type=RelationChoice(
            title=u"Related",
            source=DossierPathSourceBinder(
                portal_type=("opengever.document.document", "ftw.mail.mail"),
                navigation_tree_query={
                    'object_provides':
                        ['opengever.dossier.behaviors.dossier.IDossierMarker',
                         'opengever.document.document.IDocumentSchema',
                         'ftw.mail.mail.IMail',]
                    }),
            ),
        required=False,
        )

    expectedStartOfWork = schema.Date(
        title =_(u"label_expectedStartOfWork", default="Start with work"),
        description = _(u"help_expectedStartOfWork", default=""),
        required = False,
        )

    expectedDuration = schema.Float(
        title = _(u"label_expectedDuration", default="Expected duration", ),
        description = _(u"help_expectedDuration", default="Duration in h"),
        required = False,
        )

    expectedCost = schema.Float(
        title = _(u"label_expectedCost", default="expected cost"),
        description = _(u"help_expectedCost", default="Cost in CHF"),
        required = False,
        )

    effectiveDuration = schema.Float(
        title = _(u"label_effectiveDuration", default="effective duration"),
        description = _(u"help_effectiveDuration", default="Duration in h"),
        required = False,
        )

    effectiveCost = schema.Float(
        title=_(u"label_effectiveCost", default="effective cost"),
        description=_(u"help_effectiveCost", default="Cost in CHF"),
        required = False,
        )

    form.omitted('predecessor')
    predecessor = schema.TextLine(
        title=_(u'label_predecessor', default=u'Predecessor'),
        description=_(u'help_predecessor', default=u''),
        required=False)

    # TODO: doesn't work with Plone 4
    #form.order_before(**{'ITransition.transition': "responsible"})

# # XXX doesn't work yet.
#@form.default_value(field=ITask['issuer'])

def default_issuer(data):
    portal_state = getMultiAdapter(
        (data.context, data.request),
        name=u"plone_portal_state")
    member = portal_state.member()
    return member.getId()


class Task(Container):
    implements(ITask)

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)

    # REMOVED UNCOMMENT unused title function
    # def Title(self):
    #     registry = queryUtility(IRegistry)
    #     proxy = registry.forInterface(ITaskSettings)
    #     title = "#%s %s"% (
    #   getUtility(ISequenceNumber).get_number(self),self.task_type)
    #     relatedItems = getattr(self,'relatedItems',[])
    #     if len(relatedItems) == 1:
    #         title += " (%s)" % self.relatedItems[0].to_object.title
    #     elif len(relatedItems) > 1:
    #         title += " (%i Dokumente)" % len(self.relatedItems)
    #     if self.text:
    #         crop_length = int(getattr(proxy,'crop_length',20))
    #         text = self.text.encode('utf8')
    #         text = self.restrictedTraverse('@@plone').cropText(
    #   text,crop_length)
    #         text = text.decode('utf8')
    #         title += ": %s" % text
    #     return title
    @property
    def sequence_number(self):
        return self._sequence_number

    @property
    def task_type_category(self):
        for category in ['unidirectional_by_reference',
                         'unidirectional_by_value',
                         'bidirectional_by_reference',
                         'bidirectional_by_value']:
            voc = getVocabularyRegistry().get(
                self, 'opengever.task.' + category)
            if self.task_type in voc:
                return category
        return None

    @property
    def client_id(self):
        return get_client_id()


@form.default_value(field=ITask['deadline'])
def deadlineDefaultValue(data):
    # To get hold of the folder, do: context = data.context
    return datetime.today() + timedelta(5)


@form.default_value(field=ITask['responsible_client'])
def responsible_client_default_value(data):
    return get_client_id()


class Overview(DisplayForm, OpengeverTab):
    grok.context(ITask)
    grok.name('tabbedview_view-overview')
    grok.template('overview')

    def getSubTasks(self):
        tasks = self.context.getFolderContents(
            full_objects=False,
            contentFilter={'portal_type': 'opengever.task.task'})
        return tasks

    def getContainingTask(self):
        parent = aq_parent(aq_inner(self.context))
        if parent.portal_type == self.context.portal_type:
            return [parent, ]
        return None

    def getSubDocuments(self):
        brains = self.context.getFolderContents(
            full_objects=False,
            contentFilter={'portal_type': ['opengever.document.document',
                                           'ftw.mail.mail']})

        docs = []
        for doc in brains:
            docs.append(doc.getObject())

        relatedItems = getattr(self.context, 'relatedItems', None)
        if relatedItems:
            for rel in self.context.relatedItems:
                docs.append(rel.to_object)

        docs.sort(lambda x, y: cmp(x.Title(), y.Title()))
        return docs

    def responsible_link(self):
        info = getUtility(IContactInformation)
        task = ITask(self.context)

        if not len(self.groups[0].widgets['responsible_client'].value):
            # in some special cases the responsible client may not be set.
            return info.render_link(task.responsible)

        client = client_title_helper(task, self.groups[0].widgets['responsible_client'].value[0])
        return client +' / '+ info.render_link(task.responsible)

    def issuer_link(self):
        info = getUtility(IContactInformation)
        task = ITask(self.context)
        return info.render_link(task.issuer)

    def getPredecessorTask(self):
        controller = ISuccessorTaskController(self.context)
        return controller.get_predecessor()

    def getSuccessorTasks(self):
        controller = ISuccessorTaskController(self.context)
        return controller.get_successors()

    def render_indexed_task(self, item):
        return indexed_task_link(item, display_client=True)





class IRelatedDocumentsTableSourceConfig(ITableSourceConfig):
    """Related documents table source config
    """
    pass


class RelatedDocumentsTableSource(grok.MultiAdapter, BaseTableSource):
    """Related documents table source adapter
    """

    grok.implements(ITableSource)
    grok.adapts(IRelatedDocumentsTableSourceConfig, Interface)


    def build_query(self):
        """Builds the query based on `get_base_query()` method of config.
        Returns the query object.
        """
        # initalize config
        self.config.update_config()

        # get the base query from the config
        query = self.config.get_base_query()
        portal_catalog = getToolByName(self.config.context, 'portal_catalog')
        brains = portal_catalog(path={'query':query, 'depth': 2}, portal_type=['opengever.document.document', 'ftw.mail.mail'])
        objects = []
        for brain in brains:
            objects.append(brain.getObject())
        for item in self.config.context.relatedItems:
            
            obj = item.to_object
            if obj.portal_type=='opengever.document.document' or obj.portal_type=='ftw.mail.mail':
                objects.append(obj)
        objects = self.extend_query_with_ordering(objects)
        if self.config.filter_text:
            objects = self.extend_query_with_textfilter(
                objects, self.config.filter_text)
        objects = self.extend_query_with_batching(objects)
        return objects


    def extend_query_with_ordering(self, query):
        sort_index=self.request.get('sort',  '')
        column = {}
        objects = []
        if sort_index != 'draggable' and sort_index != 'checkbox' and sort_index:
            for item in self.config.columns:
                if item['column'] == sort_index:
                    column = item
            if 'transform' in column.keys():
                transform = column.get('transform', None)
                if transform != None:
                    for item in query:
                        objects.append((transform(item, item[sort_index]), item))
                    objects_sort = objects.sort()
                    return objects_sort
                else:
                    objects_sort = sorted(query, key=attrgetter(sort_index))
                    return objects_sort
            else:
                objects_sort = sorted(query, key=attrgetter(sort_index))
                return objects_sort
        else:
            return query

    def extend_query_with_texfilter(self, query, text):
        return query

    def extend_query_with_batching(self, query):
        """Extends the given `query` with batching filters and returns the
        new query. This method is only called when batching is enabled in
        the source config with the `batching_enabled` attribute.
        """
        return query

    def search_results(self, query):
        return query



class RelatedDocuments(Documents):

    grok.name('tabbedview_view-relateddocuments')
    grok.context(ITask)
    grok.implements(IRelatedDocumentsTableSourceConfig)


    lazy = False
    columns = (
        {'column':'',
         'column_title':'',
         'transform':helper.draggable},
        {'column':'',
         'column_title':'',
         'transform':path_checkbox},

        {'column': 'title',
         'column_title': _(u'label_title', default=u'Title'),
         'sort_index' : 'sortable_title',
         'transform':linked},

        {'column':'document_author',
         'column_title':_('label_document_author', default="Document Author"),
         'transform': readable_ogds_author},

        {'column':'document_date',
         'column_title':_('label_document_date', default="Document Date"),
         'transform':helper.readable_date},

        {'column':'receipt_date',
         'column_title':_('label_receipt_date', default="Receipt Date"),
         'transform':helper.readable_date},

        {'column':'delivery_date',
         'column_title':_('label_delivery_date', default="Delivery Date"),
         'transform':helper.readable_date},
        )

    enabled_actions = [
                       'send_as_email',
                       'checkout',
                       'checkin',
                       'cancel',
                       'create_task',
                       'trashed',
                       'send_documents',
                       'copy_documents_to_remote_client',
                       'move_items',
                       'copy_items',
                       ]

    major_actions = ['send_documents',
                     'checkout',
                     'checkin',
                     'create_task',
                     ]

    def get_base_query(self):
        import pdb; pdb.set_trace( )
        return '/'.join(self.context.getPhysicalPath())

    __call__ = ListingView.__call__
    render = __call__
    update = ListingView.update

# XXX
# setting the default value of a RelationField does not work as expected
# or we don't know how to set it.
# thus we use an add form hack by injecting the values into the request.

class AddForm(dexterity.AddForm):
    grok.name('opengever.task.task')

    def update(self):
        # put default value for relatedItems into request
        paths = self.request.get('paths', [])
        if paths:
            utool = getToolByName(self.context, 'portal_url')
            portal_path = utool.getPortalPath()
            # paths have to be relative to the portal
            paths = [path[len(portal_path):] for path in paths]
            self.request.set('form.widgets.relatedItems', paths)
        # put default value for issuer into request
        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u"plone_portal_state")
        member = portal_state.member()
        if not self.request.get('form.widgets.issuer', None):
            self.request.set('form.widgets.issuer', [member.getId()])
        super(AddForm, self).update()


@indexer(ITask)
def related_items(obj):
    # FIXME this indexer seems to return ALL relatedItems and
    # does not use the `obj`..
    catalog = getUtility(ICatalog)
    results = []
    relations = catalog.findRelations({'from_attribute': 'relatedItems'})
    for rel in relations:
        results.append(rel.to_id)
    return results
grok.global_adapter(related_items, name='related_items')


@indexer(ITask)
def date_of_completion(obj):
    # handle 'None' dates. we always need a date for indexing.
    if obj.date_of_completion is None:
        return datetime(1970, 1, 1)
    return obj.date_of_completion
grok.global_adapter(date_of_completion, name='date_of_completion')


@indexer(ITask)
def assigned_client(obj):
    """Indexes the client of the responsible. Since the he may be assigned
    to multiple clients, we need to use the client which was selected in the
    task.
    """

    if not obj.responsible or not obj.responsible_client:
        return ''
    else:
        return obj.responsible_client
grok.global_adapter(assigned_client, name='assigned_client')


@indexer(ITask)
def client_id(obj):
    return get_client_id()
grok.global_adapter(client_id, name='client_id')


@indexer(ITask)
def sequence_number(obj):
    """ Indexer for the sequence_number """
    return obj._sequence_number
grok.global_adapter(sequence_number, name='sequence_number')


# SearchableText
class SearchableTextExtender(grok.Adapter):
    grok.context(ITask)
    grok.name('ITask')
    grok.implements(dexteritytextindexer.IDynamicTextIndexExtender)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        searchable = []
        # append some other attributes to the searchableText index

        # sequence_number
        seqNumb = getUtility(ISequenceNumber)
        searchable.append(str(seqNumb.get_number(self.context)))

        #responsible
        info = getUtility(IContactInformation)
        dossier = ITask(self.context)
        searchable.append(info.describe(dossier.responsible).encode(
                'utf-8'))

        return ' '.join(searchable)


@grok.subscribe(ITask, IActionSucceededEvent)
def set_dates(task, event):
    if event.action == 'task-transition-open-in-progress':
        task.expectedStartOfWork = datetime.now()
    elif event.action == 'task-transition-in-progress-resolved':
        task.date_of_completion = datetime.now()

def related_document(context):
    intids = getUtility( IIntIds )
    return intids.getId( context )