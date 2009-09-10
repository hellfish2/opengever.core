
from zope import schema
from z3c.form.browser import checkbox

from plone.directives import form

from opengever.repository import _

class IDocumentSchema(form.Schema):
    """ Document Schema Interface
    """

    foreign_reference = schema.Text(
            title = _(u'label_foreign_reference', default='Foreign Reference'),
            description = _('help_foreign_reference', default=''),
            required = False,
    )

    receipt_date = schema.Date(
            title = _(u'label_receipt_date', default='Date of receipt'),
            description = _(u'help_receipt_Date', default=''),
            required = False,
    )

    # XXX : use SQLFile
    file = schema.TextLine(
            title = _(u'label_file', default='File'),
            description = _(u'help_file', default=''),
            required = False,
    )

    form.widget(paper_form=checkbox.CheckBoxWidget)
    paper_form = schema.Bool(
            title = _(u'label_paper_form', default='Paper form'),
            description = _(u'help_paper_form', default='Available in paper form only'),
            required = False,
    )

    form.widget(preserved_as_paper=checkbox.CheckBoxWidget)
    preserved_as_paper = schema.Bool(
            title = _(u'label_preserved_as_paper', default='Preserved as paper'),
            description = _(u'help_preserved_as_paper', default=''),
            required = False,
    )

    # XXX : use SQLFile
    archival_file = schema.TextLine(
            title = _(u'label_archival_file', default='Archival File'),
            description = _(u'help_archival_file', default=''),
            required = False,
    )

    # XXX : use SQLFile
    thumbnail = schema.TextLine(
            title = _(u'label_thumbnail', default='Thumbnail'),
            description = _(u'help_thumbnail', default=''),
            required = False,
    )

    preview = schema.Text(
            title = _(u'label_preview', default='Preview'),
            description = _(u'help_preview', default=''),
            required = False,
    )

