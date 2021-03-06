from opengever.base.interfaces import ISequenceNumber
from opengever.base.source import RepositoryPathSourceBinder
from opengever.document import _
from plone.app.content.interfaces import INameFromTitle
from plone.directives import form
from z3c.relationfield.schema import RelationChoice, RelationList
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implements


class IRelatedDocuments(form.Schema):
    """The relatedDocument behvavior is a opengever.document
    specific relateditems behavior. Only allows opengever.documents
    """

    relatedItems = RelationList(
        title=_(u'label_related_documents', default=u'Related Documents'),
        default=[],
        value_type=RelationChoice(
            title=u"Related",
            source=RepositoryPathSourceBinder(
                portal_type=("opengever.document.document", "ftw.mail.mail"),
                navigation_tree_query={
                    'object_provides':
                        ['opengever.repository.repositoryroot.IRepositoryRoot',
                         'opengever.repository.repositoryfolder.' +
                            'IRepositoryFolderSchema',
                         'opengever.dossier.behaviors.dossier.IDossierMarker',
                         'opengever.document.document.IDocumentSchema',
                         'ftw.mail.mail.IMail', ]
                }),
            ),
        required=False,
        )

    form.fieldset(
        u'common',
        label=_(u'fieldset_common', default=u'Common'),
        fields=[
            u'relatedItems',
            ],
        )


alsoProvides(IRelatedDocuments, form.IFormFieldProvider)


class IDocumentNameFromTitle(INameFromTitle):
    """Behavior interface.
    """


class DocumentNameFromTitle(object):
    """Speical name from title behavior for letting the normalizing name
    chooser choose the ID like want it to be.
    The of a document should be in the format: "document-{sequence number}"
    """

    implements(IDocumentNameFromTitle)

    format = u'document-%i'

    def __init__(self, context):
        self.context = context

    @property
    def title(self):
        seq_number = getUtility(ISequenceNumber).get_number(self.context)
        return self.format % seq_number


class IBaseDocument(Interface):
    """Marker interface for objects with a document like type
    (og.document, ftw.mail.mail) etc."""
