from collective import dexteritytextindexer
from collective.elephantvocabulary import wrap_vocabulary
from datetime import date
from ftw.datepicker.widget import DatePickerFieldWidget
from opengever.document import _
from plone.directives import form
from plone.namedfile.field import NamedBlobFile
from plone.z3cform.textlines.textlines import TextLinesFieldWidget
from zope import schema
from zope.interface import alsoProvides


class IDocumentMetadata(form.Schema):
    """Behavior for common GEVER document metadata
    """

    form.fieldset(
        u'common',
        label=_(u'fieldset_common', u'Common'),
        fields=[
            u'description',
            u'keywords',
            u'foreign_reference',
            u'document_date',
            u'receipt_date',
            u'delivery_date',
            u'document_type',
            u'document_author',
            u'archival_file',
            u'thumbnail',
            ],
        )

    dexteritytextindexer.searchable('description')
    description = schema.Text(
        title=_(u'label_description', default=u'Description'),
        description=_(u'help_description', default=u''),
        required=False,
        )

    dexteritytextindexer.searchable('keywords')
    keywords = schema.Tuple(
        title=_(u'label_keywords', default=u'Keywords'),
        description=_(u'help_keywords', default=u''),
        value_type=schema.TextLine(),
        required=False,
        missing_value=(),
        )
    form.widget(keywords=TextLinesFieldWidget)

    foreign_reference = schema.TextLine(
        title=_(u'label_foreign_reference', default='Foreign Reference'),
        description=_('help_foreign_reference', default=''),
        required=False,
        )

    # workaround because ftw.datepicker wasn't working
    form.widget(document_date=DatePickerFieldWidget)
    document_date = schema.Date(
        title=_(u'label_document_date', default='Document Date'),
        description=_(u'help_document_date', default=''),
        required=False,
        )

    document_type = schema.Choice(
        title=_(u'label_document_type', default='Document Type'),
        description=_(u'help_document_type', default=''),
        source=wrap_vocabulary('opengever.document.document_types',
                    visible_terms_from_registry='opengever.document' +
                            '.interfaces.IDocumentType.document_types'),
        required=False,
        )

    dexteritytextindexer.searchable('document_author')
    document_author = schema.TextLine(
        title=_(u'label_author', default='Author'),
        description=_(u'help_author',
                      default="Surname firstname or a userid"
                      "(would be automatically resolved to fullname)"),
        required=False,
        )

    form.omitted('archival_file')
    archival_file = NamedBlobFile(
        title=_(u'label_archival_file', default='Archival File'),
        description=_(u'help_archival_file', default=''),
        required=False,
        )

    form.omitted('thumbnail')
    thumbnail = NamedBlobFile(
        title=_(u'label_thumbnail', default='Thumbnail'),
        description=_(u'help_thumbnail', default=''),
        required=False,
        )

    form.omitted('preview')
    preview = NamedBlobFile(
        title=_(u'label_preview', default='Preview'),
        description=_(u'help_preview', default=''),
        required=False,
        )

    # workaround because ftw.datepicker wasn't working
    form.widget(receipt_date=DatePickerFieldWidget)
    receipt_date = schema.Date(
        title=_(u'label_receipt_date', default='Date of receipt'),
        description=_(u'help_receipt_date', default=''),
        required=False,
        )

    # workaround because ftw.datepicker wasn't working
    form.widget(delivery_date=DatePickerFieldWidget)
    delivery_date = schema.Date(
        title=_(u'label_delivery_date', default='Date of delivery'),
        description=_(u'help_delivery_date', default=''),
        required=False,
        )


alsoProvides(IDocumentMetadata, form.IFormFieldProvider)


# Default values
@form.default_value(field=IDocumentMetadata['document_date'])
def default_document_date(data):
    """Set today's date as the default document_date"""
    return date.today()
