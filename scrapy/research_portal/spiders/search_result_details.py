import scrapy
import re
import research_portal.helper as helper
import research_portal.constants as const
from research_portal.items import SearchResultLoader

class SearchResultDetailsSpider(scrapy.Spider):
    name = 'bmbf_search_result_details'
    
    start_urls = [
        'https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=view&fkz=AAC2007'
    ] 

    def __init__(self, *args, **kwargs):
        super(SearchResultDetailsSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        details = response.xpath('//div[@class=$outer_content_class]/div[@class=$detail_view]/div[@class=$detail_view_item]',
                                outer_content_class=const.OUTER_CONTENT_CLASS,
                                detail_view=const.DETAIL_VIEW,
                                detail_view_item=const.DETAIL_VIEW_ITEM)
        loader = SearchResultLoader()
        # html sources of the details, for debugging purposes
        loader.add_value('html_cell_sources', details.getall())
        for detail in details:
            # a list like [key1, value1, key2, value2, ...]
            key_value_list = detail.xpath('./div/text()').getall()

            if len(key_value_list) % 2 == 0:
                self.add_to_loader(loader, key_value_list)
            else:
                self.logger.warn("Uneven values for key_val_list: {}, skipping them.".format(key_value_list))
        return loader.load_item()

    def add_to_loader(self, loader, key_value_list):
        main_key = key_value_list[0]
        if main_key == 'Laufzeit':
            start, end = helper.replace_whitespace(key_value_list[1]).split(' bis ')
            loader.add_value('laufzeit_start', start)
            loader.add_value('laufzeit_ende', end)
        elif main_key == 'Ressort':
            ressort, referat = helper.replace_whitespace(key_value_list[1]).split(', Referat ')
            loader.add_value('ressort', ressort)
            loader.add_value('referat', referat)
        elif main_key in const.IDENTIFIER_ITEM_NAME_MAP:
            loader.add_value(const.IDENTIFIER_ITEM_NAME_MAP[main_key], key_value_list[1])
            # this happens for either 'Zuwendungsempfänger' or 'Ausführende Stelle'
            if (len(key_value_list) > 2):
                main_item_key = const.IDENTIFIER_ITEM_NAME_MAP[main_key]
                # a list like [[key2, value2], [key3, value3], ...], with whitespace removed for the keys
                sub_key_value_list = [[helper.replace_whitespace(key_value_list[i]), key_value_list[i+1]] for i in range(2, len(key_value_list), 2)]
                for k, v in sub_key_value_list:
                    if k == 'Ort':
                        loader.add_value(main_item_key + const.ITEM_DELIMITER + 'ort', v)
                    elif k == 'Staat':
                        loader.add_value(main_item_key + const.ITEM_DELIMITER + 'staat', v)
                    elif k == 'Bundesland, Staat':
                        b, s = helper.replace_whitespace(v).split(', ')
                        loader.add_value(main_item_key + const.ITEM_DELIMITER + 'bundesland', b)
                        loader.add_value(main_item_key + const.ITEM_DELIMITER + 'staat', s)
                    else:
                        self.logger.warn("Unknown key: {} with value: {} below main key {}".format(k, v, main_key))
        else:
            self.logger.warn("Missing values for identifier {}, for key_val_list: {}".format(key_value_list[0], key_value_list))

