# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FixpriceScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ProductItem(scrapy.Item):
    timestamp = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    section = scrapy.Field()
    price_data = scrapy.Field()
    variants = scrapy.Field()
