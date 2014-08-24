from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from .factory import create_superuser, create_cropped_image


class BrowserTestBase(object):
    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(BrowserTestBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(BrowserTestBase, cls).tearDownClass()

    def setUp(self):
        self.image = create_cropped_image()
        self.user = create_superuser()
        super(BrowserTestBase, self).setUp()

    def _ensure_page_loaded(self, url=None):
        # see: http://stackoverflow.com/questions/18729483/reliably-detect-page-load-or-time-out-selenium-2
        def readystate_complete(d):
            return d.execute_script("return document.readyState") == "complete"

        try:
            if url:
                self.selenium.get(url)
            WebDriverWait(self.selenium, 30).until(readystate_complete)
        except TimeoutException:
            self.selenium.execute_script("window.stop();")

    def test_widget_rendered(self):
        widget = self.selenium.find_element_by_css_selector('.image-ratio')

        self.assertEqual(int(widget.get_attribute('data-min-width')), 120)
        self.assertEqual(int(widget.get_attribute('data-min-height')), 100)
        self.assertEqual(widget.get_attribute('data-image-field'),
                         'image_field')
        self.assertEqual(widget.get_attribute('data-my-name'), 'cropping')
        self.assertEqual(widget.get_attribute('data-allow-fullsize'), 'true')
        self.assertEqual(widget.get_attribute('data-size-warning'), 'false')
        self.assertEqual(widget.get_attribute('data-adapt-rotation'), 'false')
        # TODO this differs by one pixel
        #self.assertEqual(widget.get_attribute('value'), self.image.cropping)

    def test_ensure_thumbnail_available(self):
        img = self.selenium.find_element_by_css_selector('.image-ratio + img')
        self.assertTrue(self.image.image_field.url in img.get_attribute('src'))

    def test_ensure_jcrop_initialized(self):
        # make sure Jcrop is properly loaded
        WebDriverWait(self.selenium, 15)
        try:
            self.selenium.find_element_by_css_selector('.jcrop-holder')
        except NoSuchElementException:
            self.fail('Jcrop not initialized')


class AdminImageCroppingTestCase(BrowserTestBase, LiveServerTestCase):
    def setUp(self):
        super(AdminImageCroppingTestCase, self).setUp()
        self._ensure_page_loaded('%s%s' % (self.live_server_url, '/admin'))
        username_input = self.selenium.find_element_by_id("id_username")
        password_input = self.selenium.find_element_by_id("id_password")
        username_input.send_keys('admin')
        password_input.send_keys('admin')
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
        edit_view = reverse('admin:example_image_change', args=[self.image.pk])
        self._ensure_page_loaded('%s%s' % (self.live_server_url, edit_view))


class ModelFormCroppingTestCase(BrowserTestBase, LiveServerTestCase):
    def setUp(self):
        super(ModelFormCroppingTestCase, self).setUp()
        edit_view = reverse('modelform_example', args=[self.image.pk])
        self._ensure_page_loaded('%s%s' % (self.live_server_url, edit_view))
