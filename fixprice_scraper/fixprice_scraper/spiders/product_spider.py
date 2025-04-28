import scrapy
import time
from ..items import ProductItem


class ProductSpiderSpider(scrapy.Spider):
    name = "product_spider"
    allowed_domains = ["fix-price.com"]
    # start_urls = ["https://fix-price.com"]

    def __init__(self, url=None, section=None, catalog_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.section = section or []
        self.catalog_name = catalog_name or "catalog"
        self.item_count = 0
        self.max_items = 70


    def parse(self, response):
        cards = response.css('div.product.one-product-in-row')
        for card in cards:
            if self.item_count >= self.max_items:
                return

            item = ProductItem()

            item['timestamp'] = int(time.time())
            href = card.css('a::attr(href)').get()
            item['url'] = response.urljoin(href)
            item['title'] = card.css('a.title::text').get().strip()
            item['section'] = self.section

            # Price block
            current_price = card.css('div.special-price::text').re_first(r'\d+')
            original_price = card.css('div.old-price::text').re_first(r'\d+')

            if not original_price:
                original_price = current_price

            price_data = {
                "current": float(current_price),
                "original": float(original_price),
                "sale_tag": ""
            }

            if current_price and original_price and current_price != original_price:
                try:
                    discount = int(100 - (int(current_price) / int(original_price)) * 100)
                    price_data['sale_tag'] = f"Скидка {discount}%"
                except ZeroDivisionError:
                    pass

            item['price_data'] = price_data

            # Variants
            variants_text = card.css('.variants-count::text').re_first(r'\d+')
            item['variants'] = int(variants_text) if variants_text else 0

            self.item_count += 1
            yield item

        # Go to next page if available and under 70
        if self.item_count < self.max_items:
            next_page = response.css('a.pagination__next::attr(href)').get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)

