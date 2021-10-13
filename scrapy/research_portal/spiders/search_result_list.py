import scrapy
import re
import research_portal.constants as const
from research_portal.items import SearchResultLoader

class SearchResultListSpider(scrapy.Spider):
    name = 'bmbf_search_result_list'

    # changing this is not supportet by the website
    REQUESTS_PER_PAGE = 10

    def __init__(self, *args, **kwargs):
        self.total_hits = None
        super(SearchResultListSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        listrowfrom = 1
        while self.total_hits is None or listrowfrom < self.total_hits:
            self.logger.info("Starting Request for pages {} to {}".format(listrowfrom, listrowfrom+self.REQUESTS_PER_PAGE))
            formdata = {
                'suche.detailSuche':'false',
                'suche.schnellSuche': '',
                'suche.orderby': '1',
                'suche.order': 'asc',
                'suche.listrowfrom': str(listrowfrom),
                # sadly this only works for the first request, all the other requests default to 10...
                # 'suche.listrowpersite': str(self.REQUESTS_PER_PAGE),
            }
            yield scrapy.FormRequest('https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=searchlist',
                                    callback=self.parse,
                                    formdata=formdata)
            listrowfrom += self.REQUESTS_PER_PAGE

    def parse(self, response):
        content = response.xpath('//div[@class=$outer_content_class]', outer_content_class=const.OUTER_CONTENT_CLASS)

        # logging some metadata about the page (current items being processed)
        if self.total_hits is None:
            self.logger.info("Trying to find total hits")
            total_hits_array = re.findall(r'\d+', content.xpath('./h1/text()').get())
            if total_hits_array.count != 0:
                self.total_hits = int(total_hits_array[0])
            else:
                self.logger.warn('Total hits not found...')
        self.logger.info("Processing Items between: {} from a total of {} hits".format(
                        content.xpath('.//select[@id="listselect_suche_listrowfrom"]/option[@selected="selected"]/text()').get(),
                        self.total_hits)
                        )

        # parse the result list
        self.logger.debug("Number of rows found: {}".format(len(content.xpath('./div/table/tbody/tr'))))
        for row in content.xpath('./div/table/tbody/tr'):
            yield self.parse_row(row)


    def parse_row(self, row):
        loader = SearchResultLoader(selector=row)
        # first column 'FKZ'
        loader.add_xpath('foerderkennzeichen', './td[1]/a[1]/text()')
        # second column 'Ressort, Referat,...'
        cell_loader = loader.nested_xpath('./td[2]/a[1]')
        cell_loader.add_xpath('ressort', './text()[1]')
        cell_loader.add_xpath('referat', './text()[2]')
        cell_loader.add_xpath('projekttraeger', './text()[4]')
        # third column 'Zuwendungs-empfänger'
        loader.add_xpath('zuwendungsempfaenger', './td[3]/a[1]/text()')
        # fourth column 'Ausführende Stelle'
        loader.add_xpath('ausfuehrende_stelle', './td[4]/a[1]/text()')
        # fifth column 'Thema'
        loader.add_xpath('thema', './td[5]/a[1]/text()')
        # sixth column 'Laufzeit von / bis
        cell_loader = loader.nested_xpath('./td[6]/a[1]')
        cell_loader.add_xpath('laufzeit_start', './text()[1]')
        cell_loader.add_xpath('laufzeit_ende', './text()[2]')
        # seventh column 'Förder-summe'
        loader.add_xpath('foerdersumme', './td[7]/a[1]/text()')
        # eigth column 'Ver-bund'
        loader.add_xpath('foerdersumme', './td[8]/a[1]/text()')
        # html source of the row, for debugging purposes
        loader.add_xpath('html_cell_sources', './td')
        # yield the item
        return loader.load_item()