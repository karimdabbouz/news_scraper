from seleniumbase import Driver, SB
import xml.etree.ElementTree as ET
from seleniumwire.utils import decode as decodesw
from selenium.webdriver.common.by import By

import logging, time, json



class ArticleLinkScraper():
    '''
    A flexible scraper to parse links for news articles from any news outlet.

    :param str scraping_mode: Determines how links should be parsed from the site. Options: 'RSS', 'FRONTEND' or 'API'
    :param str proxy: An optional proxy URL
    :param str selenium_mode: Either 'uc' for SeleniumBase's undetected mode or 'wire' to capture backend responses. Default mode is uc
    :param boolean selenium_headed: True to run Selenium in a headed Chrome instance. Default mode is headless
    :param [str] urls: The URLs to parse links from. Needs to be a list, even for RSS feeds where only the first entry is parsed
    :param str/lambda article_url_selector: The XPATH selector to access the article links or a lambda expression that takes a JSON and returns a list of links, i.e.
    lambda response: [x['url'] for x in response['docs']]
    '''
    def __init__(
        self,
        scraping_mode,
        proxy=None,
        selenium_mode='uc',
        selenium_headed=False,
        urls=None,
        article_url_selector=None
    ):
        self.scraping_mode=scraping_mode
        self.proxy=proxy
        self.selenium_mode=selenium_mode
        self.selenium_headed=selenium_headed
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


    def get_element_for_xpath(self, driver, xpath_selector, multiple=False):
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


    def scrape_links_rss(self):
        '''
        Calls the first url in self.urls assuming it returns an RSS XML response.
        Returns a list of links for the latest articles.
        '''
        driver = self.create_selenium_driver()
        driver.get(self.urls[0])
        try:
            xml_content = driver.page_source
            root = ET.fromstring(xml_content)
            link_list = [x.find('link').text for x in root.findall('.//item')]
            return link_list
        except Exception as e:
            logging.error(f'RSS could not be parsed: {e}')
            raise
        finally:
            time.sleep(2)
            driver.quit()


    def scrape_links_api(self):
        '''
        Loops over and calls the urls in self.urls assuming they return an API JSON response.
        Returns a list of links for the latest articles.
        '''
        driver = self.create_selenium_driver()
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
            logging.error(f'No links could be parsed. link_list is empty.')
            time.sleep(2)
            driver.quit()
            raise Exception('No links could be parsed.')
        

    def scrape_links_frontend(self):
        '''
        Loops over and calls urls in self.urls and scrapes the article links from the frontend.
        Returns a list of links for the latest articles.
        '''
        driver = self.create_selenium_driver()
        link_list = []
        for page in self.urls:
            try:
                driver.get(page)
                [link_list.append(x.get_attribute('href')) for x in self.get_element_for_xpath(driver, self.article_url_selector, multiple=True)]
            except Exception as e:
                logging.error(f'Error opening or parsing of url {page}. Skipping this one - {e}')
                continue
        if link_list:
            time.sleep(2)
            driver.quit()
            return link_list
        else:
            logging.error(f'No links could be parsed. link_list is empty.')
            time.sleep(2)
            driver.quit()
            raise Exception('No links could be parsed.')
        

    def run(self):
        '''
        Starts a run and returns a list of links.
        '''
        if self.scraping_mode == 'RSS':
            return self.scrape_links_rss()
        elif self.scraping_mode == 'API':
            return self.scrape_links_api()
        elif self.scraping_mode == 'FRONTEND':
            return self.scrape_links_frontend()
        else:
            raise ValueError('You need to specify a scraping method.')