# -*- coding: utf-8 -*-
import unittest

from frontend.tests.test_api_measures import setUpModule as setUpMeasures
from selenium_base import SeleniumTestCase

from django.core import management


class GeneralFrontendTest(SeleniumTestCase):
    def setUp(self):
        fix_dir = 'frontend/tests/fixtures/'
        management.call_command('loaddata', fix_dir + 'chemicals.json',
                                verbosity=0)
        management.call_command('loaddata', fix_dir + 'sections.json',
                                verbosity=0)
        management.call_command('loaddata', fix_dir + 'ccgs.json',
                                verbosity=0)
        management.call_command('loaddata', fix_dir + 'practices.json',
                                verbosity=0)
        management.call_command('loaddata', fix_dir + 'measures.json',
                                verbosity=0)

    def test_menu_dropdown(self):
        for url in ['/ccg/03Q/',
                    '/practice/P87629/',
                    '/measure/cerazette/',
                    '/chemical/0202010D0/',
                    '/bnf/020201/',
                    '/analyse/',
                    '/about']:
            url = self.live_server_url + url
            self.browser.get(url)
            try:
                self.find_by_xpath("//a[contains(text(), 'More')]").click()
            except AssertionError as e:
                e.args += ("at URL %s" % url,)
                raise
            self.assertTrue(
                self.find_by_xpath(
                    "//a[contains(text(), 'About')]").is_displayed(),
                "dropdown functionality broken at %s" % url
            )

    def test_message_and_action(self):
        for url in ['/ccg/03Q/',
                    '/practice/P87629/',
                    '/measure/cerazette/',
                    '/chemical/0202010D0/',
                    '/bnf/020201/',
                    '/analyse/']:
            url = self.live_server_url + url
            self.browser.get(url)
            try:
                self.find_by_xpath('//a[@class="doorbell-show"]').click()
            except AssertionError as e:
                e.args += ("at URL %s" % url,)
                raise
            self.assertTrue(
                self.find_by_xpath('//div[@id="doorbell"]').is_displayed(),
                "get in touch functionality broken at %s" % url
            )

    def test_drug_name_typeahead(self):
        self.browser.get(self.live_server_url + '/analyse/')
        el = self.find_by_xpath(
            '//div[@id="denomIds-wrapper"]'
            '//input[@class="select2-search__field"]')
        el.send_keys("chl")
        # This should succeed; if not, the JSON dropdown-filling has not:
        self.find_by_xpath('//ul[@id="select2-denomIds-results"]//li')

    def test_practice_name_typeahead(self):
        self.browser.get(self.live_server_url + '/analyse/')
        self.find_by_xpath('//span[@id="select2-org-container"]').click()
        self.find_by_xpath(
            '//li[contains(text(), "a practice or practices")]').click()
        el = self.find_by_xpath(
            '//div[@id="orgIds-container"]'
            '//input[@class="select2-search__field"]')
        el.send_keys("ains")
        # This should succeed; if not, the JSON dropdown-filling has not:
        self.find_by_xpath('//ul[@id="select2-orgIds-results"]//li')

    def test_ccg_measures_sorting(self):
        # add CCGs and one measure
        setUpMeasures()

        # add another so we can sort
        month = '2015-09-01'
        measure_id = 'keppra'
        args = []
        opts = {
            'month': month,
            'measure': measure_id
        }
        management.call_command('import_measures', *args, **opts)

        url = self.live_server_url + '/ccg/02Q/measures/'
        self.browser.get(url)
        # The default should be sorting by percentile, then id
        self.assertEqual(self.find_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_cerazette')

        # Now click to sort by potential savings
        self.browser.find_element_by_xpath(
            "//button[@data-orderby='savings']").click()

        # hack: not sure of the correct way to await the element
        # being visible.
        import time
        time.sleep(1)
        self.assertEqual(self.find_by_xpath(
            "//div[@id='charts']/div[1]").get_attribute("id"),
                         'measure_keppra')

if __name__ == '__main__':
    unittest.main()
