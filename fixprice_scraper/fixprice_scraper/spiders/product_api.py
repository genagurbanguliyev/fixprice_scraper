import json

import scrapy

from fixprice_scraper.items import ProductItem


class ProductApiSpider(scrapy.Spider):
    name = "product_api"
    allowed_domains = ["fix-price.com", "api.fix-price.com"]
    base_url = "https://fix-price.com"

    custom_settings = {
        'COOKIES_ENABLED': True,
        'COMPRESSION_ENABLED': False,
        'CONCURRENT_REQUESTS': 1,
    }

    cookie_string = """
           i18n_redirected=ru; _cfuvid=SS9rd5CCsT8.K3BBl1EQo8TNIir0Po91YIlO7yMJQVg-1745298974184-0.0.1.1-604800000; sigma_experiments=%7B%22mainchange_zbrkjexu%22%3A%7B%22value%22%3Afalse%2C%22date%22%3A%222025-04-22%22%7D%7D; token=MzgwOTc4MzMzMQ%3D%3D%3Ae056c232ca0a8b75367c73987c5cb421; _ymab_param=QqS8n_pb_OnCP8-yhGmRB6P59cseidUwZXkwChMjkOU17RRNJderkUXXNckJYkobuBLZsMxLuLfLvzHza_42ZhzX9AQ; is-logged=; visited=true; skip-city=true; cf_clearance=8DQ6tZcFeKM7Pu3Bg0D2wPEMWHC9J2RChgwIrTnjhQ4-1745577439-1.2.1.1-owWAhX3BzbpkmMI6sKEj3cP0yWizR2eLsmhWl59f1XHJsZwyE1S1En1.AtYlfMRnm_ILeC_MdMieds4nquS.pwrDo6b4nCmhUixDRCbNnT3T2kkBP2LCzkNC0Asa3In2R3ic.6mDT6bJT3FhLRg78S_dYbQ.aFbHfXyL0rR1yq7YqjHPWLwiS6o53hL9hVPYAYw7s9pMv7TzSFevFsF9cFt2.XmuEanOgW12752zRBCydD9mlAWoAU_rljaGUnAMUBHfa0qDpsLGR3UnxW64ZAicuZie51Q_jAgsUcSIQzTUXnd2._py9UTCXP8XGa842KQTWmL2B6APm9.dTUV3IO08PlZG5oTm3Y2ngKbKqXE; locality=%7B%22city%22%3A%22%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3%22%2C%22cityId%22%3A55%2C%22longitude%22%3A60.597474%2C%22latitude%22%3A56.838011%2C%22prefix%22%3A%22%D0%B3%22%7D
           """

    def __init__(self, catalogs: list, product_quantity: int = 24, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookies = {k.strip(): v for k, v in (item.split("=") for item in self.cookie_string.split(";"))}
        self.catalogs = catalogs
        self.start_urls = [catalog.get('url') for catalog in catalogs]
        self.item_count = 0
        self.product_quantity = product_quantity

        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8",
            "content-type": "application/json",
            "origin": self.base_url,
            "priority": "u=1, i",
            "referer": f"{self.base_url}/",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-city": "55",
            "x-key": "MzgwOTc4MzMzMQ==:e056c232ca0a8b75367c73987c5cb421",
            "x-language": "ru"
        }

    def start_requests(self):
        try:
            query_params = f"page=1&limit={self.product_quantity}&sort=sold"
            for catalog in self.catalogs:
                catalog_slug = catalog['url'].split('/')[-1] if catalog['url'] else ''
                products_api = f"https://api.fix-price.com/buyer/v1/product/in/{catalog_slug}?{query_params}"
                request_body = json.dumps({
                    "brand": [],
                    "category": catalog["title"],
                    "isDividedPrice": False,
                    "isHit": False,
                    "isNew": False,
                    "isSpecialPrice": False,
                    "price": [],
                })

                yield scrapy.Request(
                    url=products_api,
                    callback=self.parse_products_api,
                    headers={
                        **self.headers,
                        "x-client-route": catalog['url']
                    },
                    body=request_body,
                    method='POST',
                )
        except Exception as e:
            self.logger.error(f"Error parsing catalog API: {e}")

    def parse_products_api(self, response):
        if response.status != 200:
            self.logger.error(f"API Error {response.status}: {response.body}")
            return

        try:
            data = json.loads(response.body)
            for product in data:
                yield scrapy.Request(
                    url=f"https://fix-price.com/catalog/{product.get('url', '')}",
                    callback=self.parse_product_detail_page,
                    headers={
                        **self.headers,
                        "x-client-route": f"/catalog/{product.get('url', '')}"
                    },
                    method='GET',
                    meta={'product_data': product}
                )
        except Exception as e:
            self.logger.error(f"Error parsing API products: {e}")

    def parse_product_detail_page(self, response):
        if response.status != 200:
            self.logger.error(f"parse_products_page Error {response.status}: {response.body}")
            return

        try:
            product_data = self.gen_product_item_from_api_data(response.meta['product_data'])
            product_data['section'] = response.xpath('//div[contains(@class, "crumb")]//span[@itemprop="name"]/text()').getall()[2:-1]

            # Assets (images)
            assets = {
                "main_image": response.xpath('//meta[@itemprop="image"]/@content').get() or None,
                "set_images": [],
                "view360": [],
                "video": []
            }
            slides = response.css('div.swiper-wrapper div.swiper-slide')
            for slide in slides:
                # Check for image slides
                image_link = slide.css('link[itemprop="contentUrl"]::attr(href)').get()
                if image_link:
                    assets['set_images'].append(image_link)
                    continue

                # Check for video slides
                video_iframe = slide.css('iframe::attr(src)').get()
                if video_iframe:
                    assets['video'].append(video_iframe)

            if not assets['main_image'] and assets['set_images']:
                assets['main_image'] = assets['set_images'][0]

            product_data['assets'] = assets

            # Metadata (description, characteristics)
            properties = response.css('div.properties p.property')

            product_data['brand'] = properties.css('span.title:contains("Бренд") + span.value a::text').get()

            metadata = {
                "__description": response.xpath('//meta[@itemprop="description"]/@content').get().strip(),
            }
            for prop in properties:
                title = prop.css('span.title::text').get()
                value = prop.css('span.value *::text').get()

                if title and value and (not title == "Бренд"):
                    title = title.strip()
                    value = value.strip()

                    metadata[title] = value

            product_data['metadata'] = metadata

            yield product_data
        except Exception as e:
            self.logger.error(f"Error parsing Page products: {e}")

    def gen_product_item_from_api_data(self, api_data: dict):
        return ProductItem(
            RPC=api_data["id"],
            url="https://fix-price.com/catalog/" + api_data["url"],
            title=api_data["title"],
            brand=api_data["brand"]["title"],
            price_data=self.price_calc(api_data["price"], api_data["specialPrice"]),
            stock={
                "in_stock": api_data["inStock"] > 0,
                "count": api_data["inStock"]
            },
            variants=api_data["variantCount"]
        )

    @staticmethod
    def price_calc(price: float, special_price: float | None):
        price_data = {
            "current": price,
            "original": price,
            "sale_tag": ""
        }

        if special_price and price and price != special_price:
            try:
                discount = int(100 - (float(special_price) / float(price))) * 100
                price_data['sale_tag'] = f"Скидка {discount}%"
                price_data["current"] = special_price
            except (ValueError, ZeroDivisionError):
                pass
        return price_data
