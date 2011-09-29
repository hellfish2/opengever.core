from Products.CMFCore.utils import getToolByName
from ftw.table import helper
from opengever.latex.template import LatexTemplateFile
from opengever.latex.views.baselisting import BasePDFListing
from opengever.ogds.base.interfaces import IContactInformation
from opengever.ogds.base.utils import get_current_client
from zope.component import getUtility
from zope.i18n import translate

class DossierListingPDF(BasePDFListing):
    """Listing of all dossiers as PDF (recursive). Is called from
    a tabbed view or folder_contents and expects "paths" to be in
    the request.
    """

    template = LatexTemplateFile('dossierlisting_content.tex')

    def render(self):
        return self.template(rows=self.get_listing_rows())

    def get_listing_rows(self):
        """Returns the listing rows rendered in latex.
        """

        data = []
        info = getUtility(IContactInformation)
        client = get_current_client()

        for brain in self.get_selected_data():
            data.append(self._prepare_table_row(
                    unicode(brain.sequence_number).encode('utf-8'),
                    getattr(brain, 'filing_no', None) or '',
                    self.get_repository_title(brain),
                    unicode(brain.Title).encode('utf-8'),
                    '%s / %s' % (client.title,
                                 info.describe(brain.responsible)),
                    translate(brain.review_state,
                              domain='plone',
                              context=self.request),
                    helper.readable_date(brain, brain.start),
                    ))

        return ''.join(data)

    def get_repository_title(self, brain):
        """Searches the title of the first parental repository folder of the
        brain.
        """

        rf_marker = 'opengever.repository.interfaces.IRepositoryFolder'

        path = brain.getPath().split('/')[:-1]
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        portal_path = '/'.join(portal.getPhysicalPath())
        catalog = getToolByName(self.context, 'portal_catalog')

        while path and '/'.join(path) != portal_path:
            brains = catalog({'path': {'query': '/'.join(path),
                                       'depth': 0},
                              'object_provides': rf_marker})

            if len(brains):
                title = brains[0].Title
                if isinstance(title, unicode):
                    title = title.encode('utf-8')
                return title
            else:
                path = path[:-1]

        return ''