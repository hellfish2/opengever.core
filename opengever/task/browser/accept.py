from Products.CMFCore.PortalFolder import PortalFolderBase
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from five import grok
from opengever.base.source import RepositoryPathSourceBinder
from opengever.globalindex.interfaces import ITaskQuery
from opengever.ogds.base.interfaces import ITransporter
from opengever.ogds.base.utils import get_client_id
from opengever.ogds.base.utils import remote_request
from opengever.repository.interfaces import IRepositoryFolder
from opengever.task import _
from opengever.task.interfaces import ISuccessorTaskController
from opengever.task.task import ITask
from opengever.task.util import add_simple_response
from persistent.dict import PersistentDict
from plone.dexterity.i18n import MessageFactory as dexterityMF
from plone.directives.form import Schema
from plone.z3cform.layout import FormWrapper
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.button import buttonAndHandler
from z3c.form.field import Fields
from z3c.form.form import Form
from z3c.form.interfaces import INPUT_MODE
from z3c.relationfield.schema import RelationChoice
from zope import schema
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm



# ------------------- WIZARD --------------------------


class AcceptWizardFormMixin(object):
    """Mixin class for adding wizard support.
    """

    steps = (

        ('accept_choose_method',
         _(u'accept_step_1', default=u'Step 1')),

        ('...', u'...'),
        )

    label = _(u'title_accept_task', u'Accept task')
    template = ViewPageTemplateFile(
        'templates/wizard_wrappedform.pt')
    ignoreContext = True

    passed_data = []

    def wizard_steps(self):
        current_reached = False

        for name, label in self.steps:
            classes = ['wizard-step-%s' % name]
            if name == self.step_name:
                current_reached = True
                classes.append('selected')

            elif not current_reached:
                classes.append('visited')

            yield {'name': name,
                   'label': label,
                   'class': ' '.join(classes)}

    def get_passed_data(self):
        for key in self.passed_data:
            yield {'key': key,
                   'value': self.request.get(key, '')}


class AcceptTask(grok.View):
    grok.context(ITask)
    grok.name('accept_task')
    grok.require('cmf.AddPortalContent')

    def render(self):
        url = '@@accept_choose_method'
        return self.request.RESPONSE.redirect(url)


class WizardStepBaseView(FormWrapper, grok.View):
    grok.baseclass()

    def __init__(self, *args, **kwargs):
        FormWrapper.__init__(self, *args, **kwargs)
        grok.View.__init__(self, *args, **kwargs)



# ------------------- SESSION --------------------------


class AcceptTaskSessionDataManager(object):

    KEY = 'accept-task-wizard'

    def __init__(self, request):
        self.request = request
        self.oguid = self.request.get('oguid')
        assert self.oguid, 'Could not find "oguid" in request.'
        self.session = request.SESSION

    def get_data(self):
        if self.KEY not in self.session.keys():
            self.session[self.KEY] = PersistentDict()

        wizard_data = self.session[self.KEY]

        if self.oguid not in wizard_data:
            wizard_data[self.oguid] = PersistentDict()

        return wizard_data[self.oguid]

    def get(self, key, default=None):
        return self.get_data().get(key, default)

    def set(self, key, value):
        return self.get_data().set(key, value)

    def update(self, data):
        self.get_data().update(data)


# ------------------- CHOOSE METHOD --------------------------


method_vocabulary = SimpleVocabulary([
                SimpleTerm(value=u'participate',
                           title=_(u'accept_method_participate',
                                   default=u"process in issuer's dossier")),

                SimpleTerm(value=u'existing_dossier',
                           title=_(u'accept_method_existing_dossier',
                                   default=u'file in existing dossier')),

                SimpleTerm(value=u'new_dossier',
                           title=_(u'accept_method_new_dossier',
                                   default=u'file in new dossier'))])


class IChooseMethodSchema(Schema):

    method = schema.Choice(
        title=_('label_accept_choose_method',
                default=u'Accept the task and ...'),
        vocabulary=method_vocabulary,
        required=True)


class ChooseMethodStepForm(AcceptWizardFormMixin, Form):
    fields = Fields(IChooseMethodSchema)
    fields['method'].widgetFactory[INPUT_MODE] = RadioFieldWidget

    step_name = 'accept_choose_method'

    @buttonAndHandler(_(u'button_continue', default=u'Continue'), name='save')
    def handle_continue(self, action):
        data, errors = self.extractData()

        if not errors:
            method = data.get('method')
            if method == 'participate':
                transition = 'task-transition-open-in-progress'
                url = '@@addresponse?form.widgets.transition=%s' % transition
                return self.request.RESPONSE.redirect(url)

            elif method == 'existing_dossier':
                raise NotImplementedError()

            elif method == 'new_dossier':
                # XXX: redirect to target client
                intids = getUtility(IIntIds)
                iid = intids.getId(self.context)
                oguid = '%s:%s' % (get_client_id(), str(iid))

                portal_url = getToolByName(self.context, 'portal_url')
                # XXX: should "ordnungssystem" really be hardcode?
                url = '@@accept_select_repositoryfolder?oguid=%s' % oguid
                return self.request.RESPONSE.redirect('/'.join((
                            portal_url(), 'ordnungssystem', url)))

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        return self.request.RESPONSE.redirect('.')


class ChooseMethodStepView(WizardStepBaseView):
    grok.context(ITask)
    grok.name('accept_choose_method')
    grok.require('cmf.AddPortalContent')

    form = ChooseMethodStepForm


# ################### NEW DOSSIER ##########################


class AcceptWizardNewDossierFormMixin(AcceptWizardFormMixin):

    steps = (

        ('accept_choose_method',
         _(u'accept_step_1', default=u'Step 1')),

        ('accept_select_repositoryfolder',
         _(u'accept_step_2', default=u'Step 2')),

        ('accept_select_dossier_type',
         _(u'accept_step_3', default=u'Step 3')),

        ('accept_dossier_add_form',
         _(u'accept_step_4', default=u'Step 4')),
        )


# ------------------- SELECT REPOSITORY FOLDER --------------------------

class ISelectRepositoryfolderSchema(Schema):

    repositoryfolder = RelationChoice(
        title=_(u'label_accept_select_repositoryfolder',
                default=u'Repository folder'),
        description=_(u'help_accept_select_repositoryfolder',
                      default=u'Select the repository folder within the '
                      'dossier should be created.'),
        required=True,

        source=RepositoryPathSourceBinder(
            object_provides='opengever.repository.repositoryfolder.' + \
                'IRepositoryFolderSchema',
            navigation_tree_query={
                'object_provides': [
                    'opengever.repository.repositoryroot.IRepositoryRoot',
                    'opengever.repository.repositoryfolder.' + \
                        'IRepositoryFolderSchema',
                    ]
                }))


class SelectRepositoryfolderStepForm(AcceptWizardNewDossierFormMixin, Form):
    fields = Fields(ISelectRepositoryfolderSchema)

    step_name = 'accept_select_repositoryfolder'
    passed_data = ['oguid']

    @buttonAndHandler(_(u'button_continue', default=u'Continue'), name='save')
    def handle_continue(self, action):
        data, errors = self.extractData()

        # XXX validate if repositoryfolder can contain a dossier
        if not errors:
            folder = data['repositoryfolder']
            url = folder.absolute_url()

            url += '/@@accept_select_dossier_type?oguid=%s' % (
                self.request.get('oguid'))
            return self.request.RESPONSE.redirect(url)

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        portal_url = getToolByName(self.context, 'portal_url')
        url = '%s/resolve_oguid?oguid=%s' % (
            portal_url(), self.request.get('oguid'))
        return self.request.RESPONSE.redirect(url)

    def updateWidgets(self):
        super(SelectRepositoryfolderStepForm, self).updateWidgets()


class SelectRepositoryfolderStepView(WizardStepBaseView):
    grok.context(Interface)
    grok.name('accept_select_repositoryfolder')
    grok.require('zope2.View')

    form = SelectRepositoryfolderStepForm


# ------------------- SELECT DOSSIER TYPE --------------------------


@grok.provider(IContextSourceBinder)
def allowed_dossier_types_vocabulary(context):
    dossier_behavior = 'opengever.dossier.behaviors.dossier.IDossier'

    terms = []
    for fti in PortalFolderBase.allowedContentTypes(context):
        if dossier_behavior not in getattr(fti, 'behaviors', ()):
            continue

        title = MessageFactory(fti.i18n_domain)(fti.title)
        terms.append(SimpleTerm(value=fti.id, title=title))

    return SimpleVocabulary(terms)


class ISelectDossierTypeSchema(Schema):

    # XXX hide if only one dossier type is selectable?
    dossier_type = schema.Choice(
        title=_('label_accept_select_dossier_type', default=u'Dossier type'),
        description=_(u'help_accept_select_dossier_type',
                      default=u'Select the type for the new dossier.'),
        source=allowed_dossier_types_vocabulary,
        required=True)

    text = schema.Text(
        title=_(u'label_response', default=u'Response'),
        description=_(u'help_accept_task_response',
                      default=u'Enter a answer text which will be shown '
                      u'as response when the task is accepted.'),
        required=False,
        )


class SelectDossierTypeStepForm(AcceptWizardNewDossierFormMixin, Form):
    fields = Fields(ISelectDossierTypeSchema)
    step_name = 'accept_select_dossier_type'
    passed_data = ['oguid']

    @buttonAndHandler(_(u'button_continue', default=u'Continue'), name='save')
    def handle_continue(self, action):
        data, errors = self.extractData()

        if not errors:
            AcceptTaskSessionDataManager(self.request).update(data)
            url = '%s/@@accept_dossier_add_form?oguid=%s&' % (
                self.context.absolute_url(),
                self.request.get('oguid'))
            return self.request.RESPONSE.redirect(url)

    @buttonAndHandler(_(u'button_cancel', default=u'Cancel'))
    def handle_cancel(self, action):
        portal_url = getToolByName(self.context, 'portal_url')
        url = '%s/resolve_oguid?oguid=%s' % (
            portal_url(), self.request.get('oguid'))
        return self.request.RESPONSE.redirect(url)

    def updateWidgets(self):
        super(SelectDossierTypeStepForm, self).updateWidgets()


class SelectDossierTypeStepView(WizardStepBaseView):
    grok.context(IRepositoryFolder)
    grok.name('accept_select_dossier_type')
    grok.require('zope2.View')

    form = SelectDossierTypeStepForm



# ------------------- DOSSIER ADD FORM --------------------------


class DossierAddFormView(WizardStepBaseView):
    grok.context(IRepositoryFolder)
    grok.name('accept_dossier_add_form')
    # XXX improve permissions
    grok.require('zope2.View')

    def __init__(self, context, request):
        typename = AcceptTaskSessionDataManager(request).get('dossier_type')

        ttool = getToolByName(context, 'portal_types')
        self.ti = ttool.getTypeInfo(typename)

        FormWrapper.__init__(self, context, request)
        grok.View.__init__(self, context, request)

        # Set portal_type name on newly created form instance
        if self.form_instance is not None and \
                not getattr(self.form_instance, 'portal_type', None):
            self.form_instance.portal_type = self.ti.getId()

    @property
    def form(self):
        if getattr(self, '_form', None) is not None:
            return self._form

        add_view = queryMultiAdapter((self.context, self.request, self.ti),
                                     name=self.ti.factory)
        if add_view is None:
            add_view = queryMultiAdapter((self.context, self.request,
                                          self.ti))

        self._form = self._wrap_form(add_view.form)

        return self._form

    def _wrap_form(self, formclass):
        class WrappedForm(AcceptWizardNewDossierFormMixin, formclass):
            step_name = 'accept_dossier_add_form'
            passed_data = ['oguid']

            @buttonAndHandler(dexterityMF('Save'), name='save')
            def handleAdd(self, action):
                data, errors = self.extractData()
                if errors:
                    self.status = self.formErrorsMessage
                    return
                obj = self.createAndAdd(data)
                if obj is not None:
                    # mark only as finished if we get the new object
                    self._finishedAdd = True

                # Get a properly aq wrapped object
                dossier = self.context.get(obj.id)

                oguid = self.request.get('oguid')
                query = getUtility(ITaskQuery)
                task = query.get_task_by_oguid(oguid)

                # XXX also transport responses
                # XXX also transport related documents
                transporter = getUtility(ITransporter)
                taskobj = transporter.transport_from(
                    dossier, task.client_id, task.physical_path)

                successor_controller = ISuccessorTaskController(taskobj)
                successor_controller.set_predecessor(oguid)

                text = AcceptTaskSessionDataManager(self.request).get('text')
                successor_oguid = successor_controller.get_oguid()

                query = getUtility(ITaskQuery)
                predecessor_task = query.get_task_by_oguid(oguid)

                # XXX also make workflow change on successor task.
                response = remote_request(predecessor_task.client_id,
                               '@@accept_task_workflow_transition',
                               path=predecessor_task.physical_path,
                               data={'text': text,
                                     'successor_oguid': successor_oguid})

                if response.read().strip() != 'OK':
                    raise Exception('Adding the response and changing the '
                                    'workflow state on the predecessor task '
                                    'failed.')

                self.request.RESPONSE.redirect(taskobj.absolute_url())

            @buttonAndHandler(dexterityMF(u'Cancel'), name='cancel')
            def handleCancel(self, action):
                portal_url = getToolByName(self.context, 'portal_url')
                url = '%s/resolve_oguid?oguid=%s' % (
                    portal_url(), self.request.get('oguid'))
                return self.request.RESPONSE.redirect(url)

        WrappedForm.__name__ = 'WizardForm: %s' % formclass.__name__
        return WrappedForm

    def __call__(self):
        oguid = self.request.get('oguid')

        query = getUtility(ITaskQuery)
        task = query.get_task_by_oguid(oguid)

        # XXX use DOSSIER title as default title, not TASK title - the
        # globalindex contianing_dossier is missing yet, see:
        # Issue #1253 Darstellung Dossiertitel bei Suchresultaten (Subdossiers, Dokumente, Aufgaben)
        # https://extranet.4teamwork.ch/projects/opengever-kanton-zug/sprint-backlog/1253

        title_key = 'form.widgets.IOpenGeverBase.title'

        if self.request.form.get(title_key, None) is None:
            title = task.title
            if isinstance(title, unicode):
                title = title.encode('utf-8')
            self.request.set(title_key, title)

        return FormWrapper.__call__(self)


class AcceptTaskWorkflowTransitionView(grok.View):
    grok.context(ITask)
    grok.name('accept_task_workflow_transition')
    grok.require('cmf.AddPortalContent')

    def render(self):
        text = self.request.get('text')
        successor_oguid = self.request.get('successor_oguid')
        response = add_simple_response(self.context, text=text,
                                       successor_oguid=successor_oguid)

        transition = 'task-transition-open-in-progress'
        wftool = getToolByName(self.context, 'portal_workflow')

        before = wftool.getInfoFor(self.context, 'review_state')
        before = wftool.getTitleForStateOnType(before, self.context.Type())

        wftool.doActionFor(self.context, transition)

        after = wftool.getInfoFor(self.context, 'review_state')
        after = wftool.getTitleForStateOnType(after, self.context.Type())

        response.add_change('review_state', _(u'Issue state'),
                            before, after)
        return 'OK'
