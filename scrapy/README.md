# Scrapy

This does not work currently. It is advised to download the .csv file directly, please go to the parent directory.

## Set Up
First, you have to make sure, to have Docker, Docker-Compose, Geckodriver (Firefox ftw.) and Python installed. It is recommend to use an virtualenv for Python.

Then, just follow the steps below:

```bash
# install scrapy, selenium and scrapyd-client
pip install scrapy selenium
```

## Usage:

To crawl a spider:
```bash
scrapy crawl NAME_OF_SPIDER -o output.json
```

Examples:
```bash
# search attributes (LOVs), seems to not work currently...
# scrapy crawl bmbf_search_attributes -o output.json

# search result list
scrapy crawl bmbf_search_result_list -o output.json
```