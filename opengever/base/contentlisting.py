from Missing import Value as MissingValue
from opengever.base.browser.helper import get_css_class
from plone.app.contentlisting.catalog import \
    CatalogContentListingObject as CoreListingObject
from zope.component import getMultiAdapter
from Products.CMFCore.utils import getToolByName
from opengever.repository.interfaces import IRepositoryFolderRecords
from zope.component import getUtility
from plone.registry.interfaces import IRegistry


class OpengeverCatalogContentListingObject(CoreListingObject):
    """OpenGever specific catalog content listing.
    Provides correct MIME type icons and containing dossier for rendering
    breadcrumbs in search results. Additionaly it provides cropped Title and
    Description methods.
    """

    def ContentTypeClass(self):
        """Here we set the correct content type class so that documents with
        files have the correct MIME type icons displayed.
        """
        return get_css_class(self._brain)

    def getIcon(self):
        """Because we use CSS sprites for icons, we don't return an icon here.
        """
        return None

    def _crop_text(self, text, length):
        if not text or text == MissingValue:
            return ''

        plone_view = getMultiAdapter((self, self.request), name=u'plone')
        return plone_view.cropText(text, length)

    def containing_dossier(self):
        """Returns the the title of the containing_dossier cropped to 200
        characters."""

        return self._crop_text(self._brain.containing_dossier, 200)

    def CroppedTitle(self):
        """Returns the title cropped to 200 characters"""

        return self._crop_text(self.Title(), 200)

    def CroppedDescription(self):
        """The CroppedDescription method from the corelisting
        is not implemented yet."""

        return self._crop_text(self.Description(), 400)

    def Title(self):
        """Returns the title in the preferred language if exists.
        Title have to be available in title or alternative_title"""

        # get configured alternative language
        registry = getUtility(IRegistry)
        reg_proxy = registry.forInterface(IRepositoryFolderRecords)
        alternative_language_code = reg_proxy.alternative_language_code

        language_tool = getToolByName(self._brain, 'portal_languages')
        if language_tool.getPreferredLanguage() == alternative_language_code:
            if hasattr(self._brain, 'alternative_title'):
                if getattr(self._brain, 'alternative_title'):
                    return getattr(self._brain, 'alternative_title')

        return self._brain.Title
