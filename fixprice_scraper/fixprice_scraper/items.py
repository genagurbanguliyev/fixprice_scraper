# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from datetime import datetime


class ProductItem(Item):
    timestamp = Field(default_factory=datetime.now().isoformat())
    RPC = Field(default=None)
    url = Field(default=None)
    title = Field(default=None)
    marketing_tags = Field(default=list)
    brand = Field(default=None)
    section = Field(default=list)
    price_data = Field(default=dict)
    stock = Field(default=dict)
    assets = Field(default=dict)
    metadata = Field(default=dict)
    variants = Field(default=1)
