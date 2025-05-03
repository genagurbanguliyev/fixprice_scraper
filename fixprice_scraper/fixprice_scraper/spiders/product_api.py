import json

import scrapy

from fixprice_scraper.items import ProductItem


class ProductApiSpider(scrapy.Spider):
    name = "product_api"
    allowed_domains = ["fix-price.com", "api.fix-price.com"]
    start_urls = ["https://fix-price.com/catalog"]

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9,ru;q=0.8",
        "content-type": "application/json",
        "origin": "https://fix-price.com",
        "priority": "u=1, i",
        "referer": "https://fix-price.com/",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Linux\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-city": "55",
        "x-key": "MzgwOTc4MzMzMQ==:e056c232ca0a8b75367c73987c5cb421",
        "x-language": "ru"
    }

    def parse(self, response):
        catalogs_api = "https://api.fix-price.com/buyer/v1/category/menu"

        yield scrapy.Request(
            url=catalogs_api,
            callback=self.parse_catalog_api,
            headers={
                **self.headers,
                "x-client-route": "/catalog",
            }
        )

    def parse_catalog_api(self, response):
        try:
            data = json.loads(response.body)
            for catalog in data:
                if catalog["url"] == "vsye-po-35":
                    products_api = f"https://api.fix-price.com/buyer/v1/product/in/{catalog['url']}?page=1&limit=14&sort=sold"
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
                            "x-client-route": f"/catalog/{catalog['url']}"
                        },
                        body=request_body,
                        method='POST',
                    )
                    break
        except Exception as e:
            self.logger.error(f"Error parsing catalog API: {e}")

    def parse_products_api(self, response):
        if response.status != 200:
            self.logger.error(f"API Error {response.status}: {response.body}")
            return

        try:
            data = json.loads(response.body)
            self.log(len(data))
            self.log(data[0])
            yield scrapy.Request(
                url=f"https://fix-price.com/catalog/{data[0].get('url', '')}",
                callback=self.parse_products_page,
                headers={
                    **self.headers,
                    "x-client-route": f"/catalog/{data[0].get('url', '')}"
                },
                method='GET',
                meta={'product_data': data[0]}
            )
        except Exception as e:
            self.logger.error(f"Error parsing API products: {e}")

    def parse_products_page(self, response):
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
