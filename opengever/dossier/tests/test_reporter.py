from datetime import datetime
from ftw.testing import MockTestCase
from ftw.testing.layer import ComponentRegistryLayer
from grokcore.component.testing import grok
from mocker import ANY
from opengever.base.reporter import readable_author
from opengever.dossier.browser.report import DossierReporter
from opengever.dossier.filing.interfaces import IFilingNumberActivatedLayer
from opengever.dossier.filing.report import DossierFilingNumberReporter
from opengever.dossier.filing.report import filing_no_filing
from opengever.dossier.filing.report import filing_no_number
from opengever.dossier.filing.report import filing_no_year
from zope.annotation.interfaces import IAttributeAnnotatable
import xlrd


class ReporterZCMLLayer(ComponentRegistryLayer):

    def setUp(self):
        super(ReporterZCMLLayer, self).setUp()

        import zope.security
        self.load_zcml_file('meta.zcml', zope.security)

        import Products.statusmessages
        self.load_zcml_file('configure.zcml', Products.statusmessages)


REPORTER_ZCML_LAYER = ReporterZCMLLayer()


class TestDossierReporter(MockTestCase):

    layer = REPORTER_ZCML_LAYER

    def setUp(self):
        super(TestDossierReporter, self).setUp()
        grok('opengever.dossier.browser.report')
        grok('opengever.dossier.filing.report')

    def test_filing_no_year(self):
        self.assertEquals(
            filing_no_year('OG-Leitung-2012-1'), 2012)
        self.assertEquals(
            filing_no_year('Leitung'), None)
        self.assertEquals(
            filing_no_year('OG-Direktion-2011-555'), 2011)
        self.assertEquals(
            filing_no_year(None), None)

    def test_filing_no_number(self):
        self.assertEquals(
            filing_no_number('OG-Leitung-2012-1'), 1)
        self.assertEquals(
            filing_no_number('Leitung'), None)
        self.assertEquals(
            filing_no_number('OG-Direktion-2011-555'), 555)
        self.assertEquals(
            filing_no_number(None), None)

    def test_filing_no_filing(self):
        self.assertEquals(
            filing_no_filing('OG-Leitung-2012-1'), 'Leitung')
        self.assertEquals(
            filing_no_filing('Leitung'), 'Leitung')
        self.assertEquals(
            filing_no_filing('OG-Direktion-2011-555'), 'Direktion')
        self.assertEquals(
            filing_no_filing(None), None)

    def test_get_selected_dossiers(self):
        context = self.stub()
        request = self.stub_request()
        catalog = self.stub()

        self.expect(request.get('paths')).result(
            ['dossier2',
             'dossier55',
             'dossier1',
             ])

        self.mock_tool(catalog, 'portal_catalog')

        self.expect(catalog(path={'query': 'dossier2',
                      'depth': 0})).result(['brain_2'])
        self.expect(catalog(path={'query': 'dossier55',
                      'depth': 0})).result(['brain_55'])
        self.expect(catalog(path={'query': 'dossier1',
                      'depth': 0})).result(['brain_1'])
        self.replay()

        self.assertEquals(
            DossierReporter(
                context, request).get_selected_dossiers(),
            ['brain_2', 'brain_55', 'brain_1'])

    def test_report(self):

        class MockResponse(dict):
            def getStatus(self):
                return 200
            def setHeader(self, *args, **kwargs):
                pass
        class MockRequest(dict):
            def __init__(self):
                self['paths'] = ['path1', 'path2']
                self['HTTP_USER_AGENT'] = 'MSIE'
                self.response = MockResponse()
                self.RESPONSE = self.response

        context = self.providing_stub([IAttributeAnnotatable])
        request = MockRequest()

        author_helper = self.mocker.replace(readable_author)
        self.expect(author_helper('Foo Hugo')).result('Readable Foo Hugo')
        self.expect(author_helper('Bar Hugo')).result('Readable Bar Hugo')

        # dossier 1
        dossier1 = self.stub()
        self.expect(dossier1.Title).result('f\xc3\xb6\xc3\xb6 dossier')
        self.expect(dossier1.start).result(datetime(2012, 1, 1))
        self.expect(dossier1.end).result(datetime(2012, 12, 1))
        self.expect(dossier1.responsible).result('Foo Hugo')
        self.expect(dossier1.review_state).result('active')
        self.expect(dossier1.reference).result('OG 3.1 / 4')

        #dossier 2
        dossier2 = self.stub()
        self.expect(dossier2.Title).result('Foo Dossier')
        self.expect(dossier2.start).result(datetime(2012, 1, 1))
        self.expect(dossier2.end).result(datetime(2012, 12, 1))
        self.expect(dossier2.responsible).result('Bar Hugo')
        self.expect(dossier2.review_state).result('active')
        self.expect(dossier2.reference).result('OG 3.1 / 5')

        view = self.mocker.patch(DossierReporter(context, request))
        self.expect(view.get_selected_dossiers()).result(
            [dossier1, dossier2])

        self.replay()

        data = view()
        self.assertTrue(len(data) > 0)

        wb = xlrd.open_workbook(file_contents=data)
        sheet = wb.sheets()[0]
        row1 = sheet.row(1)
        self.assertEquals(
            [cell.value for cell in row1],
            [u'f\xf6\xf6 dossier',
             u'01.01.2012',
             u'01.12.2012',
             u'Readable Foo Hugo',
             u'active',
             u'OG 3.1 / 4']
            )

    def test_report_append_filing_fields_in_sites_with_filing_number_support(self):
        dossier1 = self.stub()
        self.expect(dossier1.Title).result('f\xc3\xb6\xc3\xb6 dossier')
        self.expect(dossier1.start).result(datetime(2012, 1, 1))
        self.expect(dossier1.end).result(datetime(2012, 12, 1))
        self.expect(dossier1.responsible).result('Foo Hugo')
        self.expect(dossier1.filing_no).result('OG-Leitung-2012-1')
        self.expect(dossier1.review_state).result('active')
        self.expect(dossier1.reference).result('OG 3.1 / 4')

        author_helper = self.mocker.replace(readable_author)
        self.expect(author_helper('Foo Hugo')).result('Readable Foo Hugo')

        context = self.providing_stub([IAttributeAnnotatable])

        # request response
        request = self.stub_request(interfaces=[IFilingNumberActivatedLayer, ],
                                    stub_response=False)
        self.expect(request.get('paths')).result(['path1', 'path2'])
        self.expect(request.get('HTTP_USER_AGENT', '')).result('MSIE')

        response = self.stub_response(request=request)
        self.expect(response.setHeader(ANY, ANY))

        view = self.mocker.patch(
            DossierFilingNumberReporter(context, request))

        self.expect(view.get_selected_dossiers()).result(
            [dossier1])

        self.replay()

        data = view()
        self.assertTrue(len(data) > 0)

        wb = xlrd.open_workbook(file_contents=data)
        sheet = wb.sheets()[0]
        row1 = sheet.row(1)
        self.assertEquals(
            [u'f\xf6\xf6 dossier',
             u'01.01.2012',
             u'01.12.2012',
             u'Readable Foo Hugo',
             u'Leitung',
             2012.0,
             1.0,
             u'OG-Leitung-2012-1',
             u'active',
             u'OG 3.1 / 4'],
            [cell.value for cell in row1])
