import scrapy
import json
import time
from urllib.parse import urljoin
from scrapy.http import Request

class FixPriceSpider(scrapy.Spider):
    name = "fixprice0"
    allowed_domains = ["fix-price.com"]
    start_urls = [
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-volosami",
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-kozhey"
    ]

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'fixprice_products.json',
        'COOKIES_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        },
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/89.0.4389.82 Safari/537.36',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse_category,
                cookies={'city_id': '66'},  # Yekaterinburg region
                meta={'proxy': 'http://your_proxy_here'}  # Replace with your proxy
            )

    def parse_category(self, response):
        product_links = response.css('a.product-card__link::attr(href)').getall()
        for link in product_links:
            yield response.follow(
                url=link,
                callback=self.parse_product,
                cookies={'city_id': '66'},
                meta={'proxy': 'http://your_proxy_here'}  # Replace with your proxy
            )

        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(
                url=next_page,
                callback=self.parse_category,
                cookies={'city_id': '66'},
                meta={'proxy': 'http://your_proxy_here'}  # Replace with your proxy
            )

    def parse_product(self, response):
        timestamp = int(time.time())
        rpc = response.css('div.product-card__article::text').re_first(r'\d+')
        url = response.url
        title = response.css('h1.product-card__title::text').get().strip()
        color = response.css('div.product-card__color::text').get()
        volume = response.css('div.product-card__volume::text').get()
        if color:
            title += f", {color.strip()}"
        if volume:
            title += f", {volume.strip()}"

        marketing_tags = response.css('div.product-card__labels span::text').getall()
        brand = response.css('div.product-card__brand::text').get()
        section = response.css('ul.breadcrumbs__list li a::text').getall()[1:]  # Skipping 'Home'

        price_current = response.css('span.product-card__price-current::text').re_first(r'\d+')
        price_original = response.css('span.product-card__price-old::text').re_first(r'\d+')
        if price_current:
            price_current = float(price_current)
        if price_original:
            price_original = float(price_original)
        else:
            price_original = price_current

        sale_tag = ""
        if price_original and price_current and price_original > price_current:
            discount_percentage = int((price_original - price_current) / price_original * 100)
            sale_tag = f"Скидка {discount_percentage}%"

        in_stock = bool(response.css('div.product-card__availability::text').re_first(r'В наличии'))
        stock_count = 0  # Assuming stock count is not available

        main_image = response.css('div.product-card__image img::attr(src)').get()
        set_images = response.css('div.product-card__thumbnails img::attr(src)').getall()
        view360 = []  # Assuming 360 view images are not available
        video = response.css('div.product-card__video source::attr(src)').getall()

        description = response.css('div.product-card__description::text').get()
        metadata = {
            "__description": description.strip() if description else ""
        }
        characteristics = response.css('ul.product-card__characteristics li')
        for item in characteristics:
            key = item.css('span::text').get()
            value = item.css('::text').getall()[-1].strip()
            metadata[key] = value

        variants = 0
        if color:
            variants += 1
        if volume:
            variants += 1

        yield {
            "timestamp": timestamp,
            "RPC": rpc,
            "url": url,
            "title": title,
            "marketing_tags": marketing_tags,
            "brand": brand,
            "section": section,
            "price_data": {
                "current": price_current,
                "original": price_original,
                "sale_tag": sale_tag
            },
            "stock": {
                "in_stock": in_stock,
                "count": stock_count
            },
            "assets": {
                "main_image": main_image,
                "set_images": set_images,
                "view360": view360,
                "video": video
            },
            "metadata": metadata,
            "variants": variants
        }
