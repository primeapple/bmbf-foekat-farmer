# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst, Identity, MapCompose, Compose
from scrapy.loader import ItemLoader
import research_portal.helper as helper

################ HELPERS ################
def trim_all(iterator):
    return [[str.strip(value) for value in iterator]]

def remove_whitespace_in_html(html):
    return helper.replace_whitespace(html, whitespace_chars='\n\t\r')


################# ITEMS #################
class SearchAttributeItem(scrapy.Item):
    form_title = scrapy.Field()
    table_title = scrapy.Field()
    url = scrapy.Field()
    original_rows = scrapy.Field()
    after_search_rows = scrapy.Field()


class SearchResultItem(scrapy.Item):
    foerderkennzeichen = scrapy.Field()
    thema = scrapy.Field()
    ressort = scrapy.Field()
    referat = scrapy.Field()
    laufzeit_start = scrapy.Field()
    laufzeit_ende = scrapy.Field()
    foerderart = scrapy.Field()
    verbund = scrapy.Field()
    foerdersumme = scrapy.Field()
    projekttraeger = scrapy.Field()
    leistungsplansystematik = scrapy.Field()
    foerderprofil = scrapy.Field()
    zuwendungsempfaenger = scrapy.Field()
    zuwendungsempfaenger_ort = scrapy.Field()
    zuwendungsempfaenger_bundesland = scrapy.Field()
    zuwendungsempfaenger_staat = scrapy.Field()
    ausfuehrende_stelle = scrapy.Field()
    ausfuehrende_stelle_ort = scrapy.Field()
    ausfuehrende_stelle_bundesland = scrapy.Field()
    ausfuehrende_stelle_staat = scrapy.Field()
    html_cell_sources = scrapy.Field()
        
################# LOADERS ################
class SearchAttributeLoader(scrapy.loader.ItemLoader):
    default_item_class = SearchAttributeItem
    default_output_processor = TakeFirst()
    original_rows_out = Identity()
    original_rows_in = MapCompose(trim_all)
    after_search_rows_out = Identity()
    after_search_rows_in = MapCompose(trim_all)


class SearchResultLoader(scrapy.loader.ItemLoader):
    default_item_class = SearchResultItem
    default_output_processor = TakeFirst()
    default_input_processor = MapCompose(str.strip)
    html_cell_sources_out = Identity()
    html_cell_sources_in = MapCompose(remove_whitespace_in_html)
