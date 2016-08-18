from pyquery import PyQuery as pq
from django.core import management
from django.test import TestCase
from frontend.models import Measure, MeasureValue, MeasureGlobal

def setUpModule():
    fix_dir = 'frontend/tests/fixtures/'
    management.call_command('loaddata', fix_dir + 'chemicals.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'sections.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'ccgs.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'practices.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'shas.json',
                            verbosity=0)
    management.call_command('loaddata', fix_dir + 'prescriptions.json',
                            verbosity=0)
    Measure.objects.create(id='ace', name='ACE inhibitors',
        title='ACE inhibitors', description='foo')

def tearDownModule():
    management.call_command('flush', verbosity=0, interactive=False)


class TestFrontendViews(TestCase):

    def test_call_view_homepage(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_javascript_inclusion(self):
        with self.settings(DEBUG=False):
            response = self.client.get('')
            doc = pq(response.content)
            mainjs = doc('script')[-2].attrib['src']
            self.assertIn('openprescribing.min.js', mainjs)
        with self.settings(DEBUG=True, INTERNAL_IPS=('127.0.0.1',)):
            response = self.client.get('')
            doc = pq(response.content)
            mainjs = doc('script')[-2].attrib['src']
            self.assertIn('openprescribing.js', mainjs)

    def test_call_view_analyse(self):
        response = self.client.get('/analyse/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analyse.html')

    def test_call_view_bnf_all(self):
        response = self.client.get('/bnf/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_bnf.html')
        self.assertContains(response, '<h1>All BNF sections</h1>')
        doc = pq(response.content)
        sections = doc('#all-results li')
        self.assertEqual(len(sections), 5)
        first_section = doc('#all-results li:first')
        self.assertEqual(first_section.text(), '2: Cardiovascular System')

    def test_call_view_bnf_chapter(self):
        response = self.client.get('/bnf/02/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '2: Cardiovascular System')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 2)

    def test_call_view_bnf_section(self):
        response = self.client.get('/bnf/0202/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '2.2: Diuretics')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(), 'Part of chapter 2 Cardiovascular System')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 1)

    def test_call_view_bnf_para(self):
        response = self.client.get('/bnf/020201/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bnf_section.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(
            title.text(), '2.2.1: Thiazides And Related Diuretics')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(),
            'Part of chapter 2 Cardiovascular System , section 2.2 Diuretics')
        subsections = doc('a.subsection')
        self.assertEqual(len(subsections), 0)

    def test_call_view_chemical_all(self):
        response = self.client.get('/chemical/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_chemicals.html')
        self.assertContains(response, '<h1>All chemicals</h1>')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'All chemicals')
        sections = doc('#all-results li')
        self.assertEqual(len(sections), 4)
        first_section = doc('#all-results li:first')
        self.assertEqual(first_section.text(),
                         'Bendroflumethiazide (0202010B0)')

    def test_call_view_chemical_section(self):
        response = self.client.get('/chemical/0202010D0/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chemical.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'Chlorothiazide (0202010D0)')
        lead = doc('.lead')
        self.assertEqual(
            lead.text(),
            ('Part of chapter 2 Cardiovascular System , section 2.2 '
             'Diuretics , paragraph 2.2.1 Thiazides And Related Diuretics')
        )

    def test_call_view_ccg_all(self):
        response = self.client.get('/ccg/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_ccgs.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'All CCGs')
        ccgs = doc('a.ccg')
        self.assertEqual(len(ccgs), 2)

    def test_call_view_ccg_section(self):
        response = self.client.get('/ccg/03V/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'CCG: NHS Corby')
        practices = doc('#practices li')
        self.assertEqual(len(practices), 1)

    def test_call_view_practice_all(self):
        response = self.client.get('/practice/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'all_practices.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'Find a practice')
        practices = doc('#all-results a.practice')
        self.assertEqual(len(practices), 0)

    def test_call_view_practice_section(self):
        response = self.client.get('/practice/P87629/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_practice.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '1/ST ANDREWS MEDICAL PRACTICE')
        lead = doc('.lead:first')
        self.assertEqual(
            lead.text(),
            ('Address: ST.ANDREWS MEDICAL CENTRE, 30 RUSSELL STREET '
             'ECCLES, MANCHESTER, M30 0NU'))
        lead = doc('.lead:last')

    def test_call_view_measure_ccg(self):
        response = self.client.get('/ccg/03V/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), 'CCG: NHS Corby')
        practices = doc('#practices li')
        self.assertEqual(len(practices), 1)

    def test_call_view_measure_practice(self):
        response = self.client.get('/practice/P87629/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measures_for_one_practice.html')
        doc = pq(response.content)
        title = doc('h1')
        self.assertEqual(title.text(), '1/ST ANDREWS MEDICAL PRACTICE')

    def test_call_view_measure_practices_in_ccg(self):
        response = self.client.get('/ccg/03V/ace/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'measure_for_practices_in_ccg.html')
        doc = pq(response.content)
        title = doc('h1')
        t = ('ACE inhibitors prescribing '
             'by GP practices in NHS Corby')
        self.assertEqual(title.text(), t)

    def test_call_view_practice_redirect(self):
        response = self.client.get('/practice/P87629/measures/')
        self.assertEqual(response.status_code, 301)

    def test_call_view_ccg_redirect(self):
        response = self.client.get('/ccg/03V/measures/')
        self.assertEqual(response.status_code, 301)
