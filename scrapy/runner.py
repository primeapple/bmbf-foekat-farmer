import os
from scrapy.cmdline import execute

os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    execute(
        [
            'scrapy',
            'crawl',
            'bmbf_search_results',
            '-o',
            'test.json'
        ]
    )
except SystemExit:
    pass