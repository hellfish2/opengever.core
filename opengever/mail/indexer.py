from collective import dexteritytextindexer
from datetime import datetime
from five import grok
from ftw.mail import utils
from ftw.mail.mail import IMail
from opengever.base.interfaces import IReferenceNumber, ISequenceNumber
from plone.indexer import indexer
from zope.component import getAdapter, getUtility
import re


def _is_bad_from(from_header):
    """Return True if the from header contains LDAP path
    or other Exchange informations."""

    angle_addr_match = re.search(r'<(.*)>', from_header)
    if not angle_addr_match:
        return False

    angle_addr = angle_addr_match.groups()[0]

    # If the stuff in between < > is separated by slashes and each
    # part looks like key=value, it smells like an LDAP path
    slash_separated_parts = [p for p in angle_addr.split('/') if p]
    bad = all([len(p.split('=')) == 2 for p in slash_separated_parts])
    return bad


@indexer(IMail)
def document_author(obj):
    """Return the sender address for the indexer document_author."""
    document_author = utils.get_header(obj.msg, 'From')

    # strip newlines
    document_author = document_author.replace('\n', '')

    if _is_bad_from(document_author):
        document_author = re.sub(r'<.*>', '', document_author).rstrip()

    document_author = document_author.replace('<', '&lt;')
    document_author = document_author.replace('>', '&gt;')
    return document_author
grok.global_adapter(document_author, name='document_author')


@indexer(IMail)
def document_date(obj):
    """Return the sent (not receipt) date of the mail for the
    document_date indexer.
    """
    document_date = utils.get_date_header(obj.msg, 'Date')
    return datetime.fromtimestamp(document_date).date()
grok.global_adapter(document_date, name="document_date")


@indexer(IMail)
def receipt_date(obj):
    """Return the receipt date of the mail for the receipt_date indexer.
    We currently approximate this date by using the document date.
    """
    # TODO: Parse received-values of header mail
    document_date = utils.get_date_header(obj.msg, 'Date')
    return datetime.fromtimestamp(document_date).date()
grok.global_adapter(receipt_date, name='receipt_date')


@indexer(IMail)
def sortable_author(obj):
    """Return the normalized author name for sortable_author indexer.
    For mails, this currently equals the document_author.
    """

    author = document_author(obj)()
    if author:
        return author.decode('utf8')
    else:
        return ''
grok.global_adapter(sortable_author, name='sortable_author')


@indexer(IMail)
def checked_out(obj):
    """Empty string checked out indexer, because we need an index value
    for sorted listings, but a mail can't be checked out so we return a
    empty string."""

    return ''
grok.global_adapter(checked_out, name='checked_out')


class SearchableTextExtender(grok.Adapter):
    """Specifix SearchableText Extender for the mail"""

    grok.context(IMail)
    grok.name('IOGMail')
    grok.implements(dexteritytextindexer.IDynamicTextIndexExtender)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        searchable = []
        # append some other attributes to the searchableText index
        # reference_number
        refNumb = getAdapter(self.context, IReferenceNumber)
        searchable.append(refNumb.get_number())

        # sequence_number
        seqNumb = getUtility(ISequenceNumber)
        searchable.append(str(seqNumb.get_number(self.context)))

        return ' '.join(searchable)
