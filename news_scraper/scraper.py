from seleniumbase import Driver, SB
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from seleniumwire.utils import decode as decodesw
from selenium.webdriver.common.by import By

import logging, time, json, random, datetime



class ArticleLinkScraper():
    '''
    A flexible scraper to parse links for news articles from any news outlet.

    :param str scraping_mode: Determines how links should be parsed from the site. Options: 'RSS', 'FRONTEND' or 'API'
    :param dict selenium_settings: Determines what kind of driver and how it is started. Default: mode=uc, headed=True, proxy=None
    :param [str] urls: The URLs to parse links from. Needs to be a list, even for RSS feeds where only the first entry is parsed
    :param str/lambda article_url_selector: The XPATH selector to access the article links or a lambda expression that takes a JSON and returns a list of links, i.e.
    lambda response: [x['url'] for x in response['docs']]
    '''
    def __init__(
        self,
        scraping_mode,
        selenium_settings={
            'mode': 'uc',
            'headed': True,
            'proxy': None
        },
        urls=None,
        article_url_selector=None
    ):
        self.scraping_mode=scraping_mode
        self.selenium_settings=selenium_settings
        self.urls=urls
        self.article_url_selector=article_url_selector
        

    def create_selenium_driver(self):
        '''
        Starts Selenium using SeleniumBase and returns the driver.
        Note: SeleniumBase's wire-mode needs an explicit headed param while uc-mode is in headed mode by default
        '''
        if self.selenium_mode == 'wire':
            if self.selenium_headed:
                driver = Driver(wire=True, headed=True, proxy=self.proxy)
            else:
                driver = Driver(wire=True, proxy=self.proxy)
            driver.set_window_size(1920, 1080)
            return driver
        elif self.selenium_mode == 'uc':
            if self.selenium_headed:
                driver = Driver(uc=True, proxy=self.proxy)
            else:
                driver = Driver(uc=True, headless=True, proxy=self.proxy)
            driver.set_window_size(1920, 1080)
            return driver
        else:
            logging.error(f'Invalid parameter set for selenium_mode: "{self.selenium_mode}". Use either "wire" or "uc".')
            raise ValueError('Invalid parameter for selenium_mode')


    def get_element_by_xpath(self, driver, xpath_selector, multiple=False):
        '''
        Returns the element defined by the selector.
        If multiple is set to True, it returns a list of elements.
        '''
        if xpath_selector != None:
            if multiple:
                element = driver.find_elements(By.XPATH, xpath_selector)
            else:
                element = driver.find_element(By.XPATH, xpath_selector)
        else:
            element = None
        return element


    def scrape_links_rss(self, driver):
        '''
        Calls the first url in self.urls assuming it returns an RSS XML response.
        Returns a list of links for the latest articles.
        '''
        driver.set_window_size(1920, 1080)
        if self.selenium_settings['mode'] == 'uc':
            driver.uc_open_with_reconnect(self.urls[0])
        else:
            driver.get(self.urls[0])
        try:
            if self.selenium_settings['mode'] == 'uc':
                xml_content = driver.get_page_source()
            else:
                xml_content = driver.page_source
            root = ET.fromstring(xml_content)
            link_list = [x.find('link').text for x in root.findall('.//item')]
            return link_list
        except Exception as e:
            logging.error(f'RSS could not be parsed: {e}')
            raise
        finally:
            time.sleep(2)
            if not self.selenium_settings['mode'] == 'uc':
                driver.quit()


    def scrape_links_api(self, driver):
        '''
        Loops over and calls the urls in self.urls assuming they return an API JSON response.
        Returns a list of links for the latest articles.
        '''
        driver.set_window_size(1920, 1080)
        link_list = []
        for page in self.urls:
            try:
                driver.get(page)
                for i, v in enumerate(driver.requests):
                    if page == v.url:
                        data = decodesw(
                            v.response.body,
                            v.response.headers.get('Content-Encoding', 'identity')
                        )
                        response = json.loads(data.decode('utf-8'))
                        link_list.extend(self.article_url_selector(response))
                time.sleep(2)
                driver.requests.clear()
            except Exception as e:
                logging.error(f'Error opening or parsing of url {page}. Skipping this one - {e}')
                continue
        if link_list:
            time.sleep(2)
            driver.quit()
            return link_list
        else:
            time.sleep(2)
            driver.quit()
            raise Exception('No links could be parsed. link_list is empty.')
        

    def scrape_links_frontend(self, driver):
        '''
        Loops over and calls urls in self.urls and scrapes the article links from the frontend.
        Returns a list of links for the latest articles.
        '''
        driver.set_window_size(1920, 1080)
        link_list = []
        for page in self.urls:
            try:
                if self.selenium_settings['mode'] == 'uc':
                    driver.uc_open_with_reconnect(page)
                else:
                    driver.get(page)
                [link_list.append(x.get_attribute('href')) for x in self.get_element_by_xpath(driver, self.article_url_selector, multiple=True)]
            except Exception as e:
                logging.error(f'Error opening or parsing of url {page}. Skipping this one - {e}')
                continue
        if link_list:
            time.sleep(2)
            if not self.selenium_settings['mode'] == 'uc':
                driver.quit()
            return link_list
        else:
            time.sleep(2)
            if not self.selenium_settings['mode'] == 'uc':
                driver.quit()
            raise Exception('No links could be parsed. link_list is empty.')

    
    def run(self):
        '''
        Starts a run, creates a driver and returns a list of links.
        '''
        if self.scraping_mode == 'RSS':
            if self.selenium_settings['mode'] == 'uc':
                with SB(uc=True, headed=self.selenium_settings['headed'], proxy=self.selenium_settings['proxy']) as driver:
                    return self.scrape_links_rss(driver)
            else:
                driver = Driver(wire=True, headed=self.selenium_settings['headed'], proxy=self.selenium_settings['proxy'])
                return self.scrape_links_rss(driver)
        elif self.scraping_mode == 'API':
            logging.info('Note: Combining wire mode and a proxy will always start a headed browser. Also, using a proxy will probably interfere with capturing API requests. Use RSS or FRONTEND mode instead.')
            if self.selenium_settings['mode'] == 'uc':
                raise ValueError('API requests cannot be parsed in Seleniumbase UC-mode. Use wire mode instead.')
            else:
                driver = Driver(wire=True, headed=self.selenium_settings['headed'], proxy=self.selenium_settings['proxy'])
                return self.scrape_links_api(driver)
        elif self.scraping_mode == 'FRONTEND':
            if self.selenium_settings['mode'] == 'uc':
                with SB(uc=True, headed=self.selenium_settings['headed'], proxy=self.selenium_settings['proxy']) as driver:
                    return self.scrape_links_frontend(driver)
            else:
                driver = Driver(wire=True, headed=self.selenium_settings['headed'], proxy=self.selenium_settings['proxy'])
                return self.scrape_links_frontend(driver)
        else:
            raise ValueError('You need to specify a scraping method')


class ArticleContentScraper():
    '''
    A flexible scraper to parse content from articles from any news outlet.
    Selectors are passed as tuples with three entries:
    The first entry is the XPATH selector to select the element/s.
    The second entry is a boolean - true to parse multiple elements for the same XPATH selector.
    The third entriy is a lambda function to parse the content, i.e.: lambda response: [x.get_attribute('href) for x in response]

    :param str scraping_mode: Determines how links should be parsed from the site. Options: 'RSS', 'FRONTEND' or 'API'
    :param str proxy: An optional proxy URL
    :param str selenium_mode: Either 'uc' for SeleniumBase's undetected mode or 'wire' to capture backend responses. Default mode is uc
    :param boolean selenium_headed: True to run Selenium in a headed Chrome instance. Default mode is headless
    :param (str, boolean, func) datetime_published_selector: The date and time of publication
    :param (str, boolean, func) image_url_selector: The url of the main article image
    :param (str, boolean, func) category_selector: The category of the article
    :param (str, boolean, func) kicker_selector: The kicker/topline of the article
    :param (str, boolean, func) headline_selector: The headline of the article
    :param (str, boolean, func) teaser_selector: The teaser of the article
    :param (str, boolean, func) body_selector: The body of the article
    :param (str, boolean, func) subheadlines_selector: The subheadlines of the article
    :param (str, boolean, func) paywall_selector: A HTML element that's present if the article is paywalled
    :param (str, boolean, func) author_selector: The author/s of the article
    :param [func] pre_hooks: One or more functions to run before parsing content, i.e. to close a modal
    :param [func] post_hooks: One or more functions to parse additional data that is not included in all news outlets
    '''
    def __init__(
        self,
        scraping_mode,
        proxy=None,
        selenium_mode='uc',
        selenium_headed=False,
        link_list=None,
        medium=None,
        db=None,
        pre_hooks=None,
        post_hooks=None,
        datetime_published_selector=None,
        image_url_selector=None,        
        category_selector=None,
        kicker_selector=None,
        headline_selector=None,
        teaser_selector=None,
        body_selector=None,
        subheadlines_selector=None,
        paywall_selector=None,
        author_selector=None
    ):
        self.scraping_mode = scraping_mode
        self.proxy = proxy
        self.selenium_mode = selenium_mode
        self.selenium_headed = selenium_headed
        self.link_list = link_list
        self.medium = medium
        self.diff_to_utc = self.set_utc_difference()
        self.db = db
        self.pre_hooks = pre_hooks
        self.post_hooks = post_hooks
        self.datetime_published_selector = datetime_published_selector
        self.image_url_selector = image_url_selector
        self.category_selector = category_selector
        self.kicker_selector = kicker_selector
        self.headline_selector = headline_selector
        self.teaser_selector = teaser_selector
        self.body_selector = body_selector
        self.subheadlines_selector = subheadlines_selector
        self.paywall_selector = paywall_selector
        self.author_selector = author_selector

    
    def set_utc_difference(self):
        '''
        Determines the difference to UTC time for central Europe.
        '''
        if datetime.datetime.now(ZoneInfo('Europe/Brussels')).dst() != datetime.timedelta(0):
            return 2
        else:
            return 1
            

    def create_selenium_driver(self):
        '''
        Starts Selenium using SeleniumBase and returns the driver.
        Note: SeleniumBase's wire-mode needs an explicit headed param while uc-mode is in headed mode by default
        '''
        if self.selenium_mode == 'wire':
            if self.selenium_headed:
                driver = Driver(wire=True, headed=True, proxy=self.proxy)
            else:
                driver = Driver(wire=True, proxy=self.proxy)
            driver.set_window_size(1920, 1080)
            return driver
        elif self.selenium_mode == 'uc':
            if self.selenium_headed:
                driver = Driver(uc=True, proxy=self.proxy)
            else:
                driver = Driver(uc=True, headless=True, proxy=self.proxy)
            driver.set_window_size(1920, 1080)
            return driver
        else:
            logging.error(f'Invalid parameter set for selenium_mode: "{self.selenium_mode}". Use either "wire" or "uc".')
            raise ValueError('Invalid parameter for selenium_mode')


    def get_element_by_xpath(self, driver, xpath_selector, multiple=False, func=None):
        if xpath_selector != None:
            if multiple:
                if func:
                    element = func(driver.find_elements(By.XPATH, xpath_selector))
                else:
                    element = driver.find_elements(By.XPATH, xpath_selector)
            else:
                if func:
                    element = func(driver.find_element(By.XPATH, xpath_selector))
                else:
                    element = driver.find_element(By.XPATH, xpath_selector)
        else:
            element = None
        return element


    def scrape_article_rss(self):
        '''
        TODO
        '''
        pass


    def scrape_article_api(self):
        '''
        TODO
        '''
        pass


    def scrape_article_frontend(self, driver, link):
        '''
        Navigates to the given link and scrapes the data from the article page by selecting elements from the frontend.
        '''
        article_data = {}
        if self.pre_hooks:
            for hook in self.pre_hooks:
                try:
                    hook(driver)
                except Exception as e:
                    logging.error(f'Could not run pre_hook {hook}: {e}')
                    continue
        try:
            datetime_published = self.get_element_by_xpath(driver, self.datetime_published_selector[0], func=self.datetime_published_selector[2])
        except Exception as e:
            datetime_published = None
            logging.error(f'datetime_published could not be parsed: {e} ')
        try:
            paywall = self.get_element_by_xpath(driver, self.paywall_selector[0], multiple=self.paywall_selector[1], func=self.paywall_selector[2])
        except Exception as e:
            paywall = None
            logging.error(f'paywall could not be identified: {e}')
        try:
            author = self.get_element_by_xpath(driver, self.author_selector[0], func=self.author_selector[2])
        except Exception as e:
            author = None
            logging.error(f'author could not be parsed: {e} ')
        try:
            category = self.get_element_by_xpath(driver, self.category_selector[0], multiple=self.category_selector[1], func=self.category_selector[2])
        except Exception as e:
            category = None
            logging.error(f'category could not be parsed: {e} ')
        try:
            image_url = self.get_element_by_xpath(driver, self.image_url_selector[0], func=self.image_url_selector[2])
        except Exception as e:
            image_url = None
            logging.error(f'image_url could not be parsed: {e} ')
        try:
            kicker = self.get_element_by_xpath(driver, self.kicker_selector[0], multiple=self.kicker_selector[1], func=self.kicker_selector[2])
        except Exception as e:
            kicker = None
            logging.error(f'kicker could not be parsed: {e} ')
        try:
            headline = self.get_element_by_xpath(driver, self.headline_selector[0], func=self.headline_selector[2])
        except Exception as e:
            headline = None
            logging.error(f'headline could not be parsed: {e} ')
        try:
            teaser = self.get_element_by_xpath(driver, self.teaser_selector[0], multiple=self.teaser_selector[1], func=self.teaser_selector[2])
        except Exception as e:
            teaser = None
            logging.error(f'teaser could not be parsed: {e} ')
        try:
            body = self.get_element_by_xpath(driver, self.body_selector[0], multiple=self.body_selector[1], func=self.body_selector[2])
        except Exception as e:
            body = None
            logging.error(f'body could not be parsed: {e} ')
        try:
            subheadlines = self.get_element_by_xpath(driver, self.subheadlines_selector[0], multiple=self.subheadlines_selector[1], func=self.subheadlines_selector[2])
        except Exception as e:
            subheadlines = None
            logging.error(f'subheadlines could not be parsed: {e} ')
        article_data['medium'] = self.medium
        article_data['datetime_saved'] = datetime.datetime.utcnow()
        article_data['datetime_published'] = datetime_published
        article_data['paywall'] = paywall
        article_data['url'] = driver.current_url
        article_data['author'] = author
        article_data['category'] = category
        article_data['image_url'] = image_url
        article_data['kicker'] = kicker
        article_data['headline'] = headline
        article_data['teaser'] = teaser
        article_data['body'] = body
        article_data['subheadlines'] = subheadlines
        article_data['archive_url'] = link
        if self.post_hooks:
            for hook in self.post_hooks:
                try:
                    hook(driver, article_data)
                except Exception as e:
                    logging.error(f'Could not run post_hook {hook}: {e}')
                    continue
        return article_data

    
    def run(self):
        '''
        Starts the scraper.
        '''
        if self.link_list:
            articles = []
            if self.scraping_mode == 'RSS':
                pass # TODO
            elif self.scraping_mode == 'API':
                pass # TODO
            elif self.scraping_mode == 'FRONTEND':
                driver = self.create_selenium_driver()
                for link in self.link_list:
                    driver.get(link)
                    article_data = self.scrape_article_frontend(driver, link)
                    articles.append(article_data)
                    time.sleep(random.randint(1, 5))
                driver.quit()
                return articles
            else:
                raise ValueError('You need to specify a scraping method.')
        else:
            raise ValueError('link_list is empty.')