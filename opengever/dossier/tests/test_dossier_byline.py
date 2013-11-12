from datetime import date
from ftw.builder import Builder
from ftw.builder import create
from opengever.base.tests.byline_base_test import TestBylineBase
from opengever.testing import create_ogds_user
from zope.component import getUtility
from zope.intid.interfaces import IIntIds


class TestDossierByline(TestBylineBase):
    
    def setUp(self):
        super(TestDossierByline, self).setUp()
        
        self.intids = getUtility(IIntIds)
        
        create_ogds_user('hugo.boss')

        self.dossier = create(Builder('dossier')
               .in_state('dossier-state-active')
               .having(reference_number_prefix='5',
                       responsible='hugo.boss',
                       start=date(2013, 11, 6),
                       end=date(2013, 11, 7),
                       filing_no='OG-Amt-2013-5'))

        self.browser.open(self.dossier.absolute_url())
        
    def test_dossier_byline_icon_display(self):
        icon = self.get_byline_element_by_class('byline-icon')
        self.assertEquals('byline-icon contenttype-opengever-dossier-businesscasedossier',
                          icon.target.get('class'))

    def test_dossier_byline_responsible_display(self):
        responsible = self.get_byline_value_by_label('by:')
        self.assertEquals('Boss Hugo (hugo.boss)', responsible.text_content())

    def test_dossier_byline_state_display(self):
        state = self.get_byline_value_by_label('State:')
        self.assertEquals('dossier-state-active', state.text_content())
        
    def test_dossier_byline_start_date_display(self):
        start_date = self.get_byline_value_by_label('from:')
        self.assertEquals('Nov 06, 2013', start_date.text_content())
        
    def test_dossier_byline_sequence_number_display(self):
        seq_number = self.get_byline_value_by_label('Sequence Number:')
        self.assertEquals('1', seq_number.text_content())
        
    def test_dossier_byline_reference_number_display(self):
        ref_number = self.get_byline_value_by_label('Reference Number:')
        self.assertEquals('OG / 1', ref_number.text_content())
        
    def test_dossier_byline_filing_number_display(self):
        filing_number = self.get_byline_value_by_label('Filing Number:')
        self.assertEquals('OG-Amt-2013-5', filing_number.text_content())

    def test_dossier_byline_email_display(self):
        dossier_id = self.intids.getId(self.dossier)
        mail = self.get_byline_value_by_label('E-Mail:')
        self.assertEquals('%d@opengever.4teamwork.ch' % dossier_id, mail.text_content())