import os
import subprocess
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from django.contrib.staticfiles.testing import StaticLiveServerTestCase


@unittest.skipIf(
    os.environ.get('TEST_SUITE') == 'nonfunctional',
    "nonfunctional tests specified in TEST_SUITE environment variable")
class SeleniumTestCase(StaticLiveServerTestCase):
    @classmethod
    def use_xvfb(cls):
        if not os.environ.get('SHOW_BROWSER', False):
            return subprocess.call(
                "type xvfb-run", shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

    @classmethod
    def get_firefox_driver(cls):
        # Get a driver that supports capturing the output of console.log
        return webdriver.Firefox()

    @classmethod
    def setUpClass(cls):
        super(SeleniumTestCase, cls).setUpClass()
        cls.use_saucelabs = os.environ.get('TRAVIS') \
            or os.environ.get('USE_SAUCELABS')
        if cls.use_saucelabs:
            browser, version, platform = os.environ['BROWSER'].split(":")
            caps = {'browserName': browser}
            caps['platform'] = platform
            caps['version'] = version
            username = os.environ["SAUCE_USERNAME"]
            access_key = os.environ["SAUCE_ACCESS_KEY"]
            if os.environ.get('TRAVIS'):
                caps["tunnel-identifier"] = os.environ.get(
                    "TRAVIS_JOB_NUMBER", 'n/a')
                caps["build"] = os.environ.get("TRAVIS_BUILD_NUMBER", 'n/a')
                caps["tags"] = ["CI"]
            else:
                caps["tags"] = ["from-dev-sandbox"]
            if os.environ.get('TRAVIS'):
                hub_url = "%s:%s@saucehost:4445" % (username, access_key)
            else:
                hub_url = "%s:%s@localhost:4445" % (username, access_key)
            cls.browser = webdriver.Remote(
                desired_capabilities=caps,
                command_executor="http://%s/wd/hub" % hub_url)
        else:
            if cls.use_xvfb():
                from pyvirtualdisplay import Display
                cls.display = Display(visible=0, size=(1200, 800))
                cls.display.start()
            cls.browser = cls.get_firefox_driver()
        cls.browser.maximize_window()
        cls.browser.implicitly_wait(1)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        if not cls.use_saucelabs and cls.use_xvfb():
            cls.display.stop()
        super(SeleniumTestCase, cls).tearDownClass()

    def find_by_xpath(self, locator):
        try:
            element = WebDriverWait(self.browser, 3).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            return element
        except TimeoutException:
            raise TimeoutException("Expected to find element %s" % locator)
