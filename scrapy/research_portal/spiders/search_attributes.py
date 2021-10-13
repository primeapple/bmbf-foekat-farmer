import scrapy
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from scrapy.http import HtmlResponse
from research_portal.items import SearchAttributeLoader

class SearchAttributesSpider(scrapy.Spider):
    name = "bmbf_search_attributes"
    
    start_urls = [
        'https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=searchmask'
    ]

    # Site Specific Identifier for XPaths
    SEARCH_FORM_ID = 'searchForm'
    LOV_ICON_SRC = '../images/lov.gif'

    # enter this string in the searchbar to find every result
    FIND_ALL_STRING = '*'

    # Webdriver default Wait time
    WEBDRIVER_DEFAULT_WAIT = 5

    @staticmethod
    def page_loaded(driver):
        return driver.execute_script('return document.readyState') == 'complete'


    def __init__(self, *args, **kwargs):
        super(SearchAttributesSpider, self).__init__(*args, **kwargs)
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.set_headless()
        self.driver = webdriver.Firefox(firefox_options=firefox_options)
    
    def popup_response(self, base_url, javascript_command, search_text=None):
        self.driver.get(base_url)
        self.driver.execute_script(javascript_command)
        # wait until two windows are open
        WebDriverWait(self.driver, self.WEBDRIVER_DEFAULT_WAIT).until(lambda d: len(d.window_handles) == 2)
        self.driver.switch_to.window(self.driver.window_handles[1])
        # wait until page appears
        WebDriverWait(self.driver, self.WEBDRIVER_DEFAULT_WAIT).until(self.page_loaded)
        if search_text is not None:
            self.driver.find_element_by_id('lov_searchField').send_keys(search_text)
            self.driver.find_element_by_id('LovAction_general_search').click()
            WebDriverWait(self.driver, self.WEBDRIVER_DEFAULT_WAIT).until(self.page_loaded)
        response = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
        # add staring
        self.driver.close()
        # wait until window was closed
        WebDriverWait(self.driver, 5).until(lambda d: len(self.driver.window_handles) == 1)
        self.driver.switch_to.window(self.driver.window_handles[0])
        return response


    def parse(self, response):
        table_elements_with_lov_link = response.xpath('//form[@id=$search_form]/div[1]//tr/td[div/a/img/@src=$lov_icon_src]',
                                                      search_form=self.SEARCH_FORM_ID,
                                                      lov_icon_src=self.LOV_ICON_SRC)
        for table_cell_with_lov_link in table_elements_with_lov_link:
            javascript_command = table_cell_with_lov_link.xpath('./div/a[img/@src=$lov_icon_src]/@href', lov_icon_src=self.LOV_ICON_SRC).get()
            popup = self.popup_response(response.url, javascript_command)
            popup_after_search = self.popup_response(response.url, javascript_command, search_text=self.FIND_ALL_STRING)
            loader = SearchAttributeLoader(selector=table_cell_with_lov_link)
            loader.add_xpath('form_title', './preceding-sibling::td[1]/div[@class="formname"]/label/text()')
            loader.add_value('table_title', popup.xpath('//form/h1/text()').get())
            loader.add_value('url', popup.url)
            for row in popup.xpath('//table/tbody/tr'):
                loader.add_value('original_rows', [row.xpath('./td/a/text()').getall()])
            for row in popup_after_search.xpath('//table/tbody/tr'):
                loader.add_value('after_search_rows', [row.xpath('./td/a/text()').getall()])
            yield loader.load_item()

    def closed(self, reason):
        self.driver.quit()