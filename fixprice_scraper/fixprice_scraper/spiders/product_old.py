import scrapy
from ..items import ProductItem


class ProductOldSpider(scrapy.Spider):
    name = "product_old"
    allowed_domains = ["fix-price.com"]
    base_url = "https://fix-price.com"
    # cookie_string = """
    #        i18n_redirected=ru; _cfuvid=SS9rd5CCsT8.K3BBl1EQo8TNIir0Po91YIlO7yMJQVg-1745298974184-0.0.1.1-604800000; sigma_experiments=%7B%22mainchange_zbrkjexu%22%3A%7B%22value%22%3Afalse%2C%22date%22%3A%222025-04-22%22%7D%7D; token=MzgwOTc4MzMzMQ%3D%3D%3Ae056c232ca0a8b75367c73987c5cb421; _ymab_param=QqS8n_pb_OnCP8-yhGmRB6P59cseidUwZXkwChMjkOU17RRNJderkUXXNckJYkobuBLZsMxLuLfLvzHza_42ZhzX9AQ; is-logged=; visited=true; skip-city=true; cf_clearance=8DQ6tZcFeKM7Pu3Bg0D2wPEMWHC9J2RChgwIrTnjhQ4-1745577439-1.2.1.1-owWAhX3BzbpkmMI6sKEj3cP0yWizR2eLsmhWl59f1XHJsZwyE1S1En1.AtYlfMRnm_ILeC_MdMieds4nquS.pwrDo6b4nCmhUixDRCbNnT3T2kkBP2LCzkNC0Asa3In2R3ic.6mDT6bJT3FhLRg78S_dYbQ.aFbHfXyL0rR1yq7YqjHPWLwiS6o53hL9hVPYAYw7s9pMv7TzSFevFsF9cFt2.XmuEanOgW12752zRBCydD9mlAWoAU_rljaGUnAMUBHfa0qDpsLGR3UnxW64ZAicuZie51Q_jAgsUcSIQzTUXnd2._py9UTCXP8XGa842KQTWmL2B6APm9.dTUV3IO08PlZG5oTm3Y2ngKbKqXE; locality=%7B%22city%22%3A%22%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3%22%2C%22cityId%22%3A55%2C%22longitude%22%3A60.597474%2C%22latitude%22%3A56.838011%2C%22prefix%22%3A%22%D0%B3%22%7D
    #        """
    cookie_string = "i18n_redirected=ru;  _cfuvid=SS9rd5CCsT8.K3BBl1EQo8TNIir0Po91YIlO7yMJQVg-1745298974184-0.0.1.1-604800000; "

    def __init__(self, *args, **kwargs):
        # self.cookies = {k.strip(): v for k, v in (item.split("=") for item in self.cookie_string.split(";"))}
        self.cookies = {"i18n_redirected": 'ru'}
        self.start_urls = ["https://fix-price.com/catalog/vsye-po-35"]
        self.section = []
        self.catalog_name = "Распродажа! Всё по 35 руб"
        self.item_count = 0
        self.max_items = 70
        super().__init__(*args, **kwargs)

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            cookies=self.cookies,
            callback=self.parse_product
        )

    def parse_product(self, response):
        cards = response.css('div.one-product-in-row')
        # cards = response.xpath('//*[@data-observer-tag="intersectionItem"]//div.details')
        # self.log(f"cards::::::::::: {cards[0]}")
        # breadcrumb_texts = response.xpath('//div[contains(@class, "crumb")]//span[@itemprop="name"]/text()').getall()[2:]
        # item['section'] = response.xpath('//div[contains(@class, "crumb")]//span[@itemprop="name"]/text()').getall()[2:]
        # if breadcrumb_texts:
        #     self.section = breadcrumb_texts[2:]

        for card in cards:
            if self.item_count >= self.max_items:
                return

            item = ProductItem()

            item['RPC'] = card.attrib.get('id')
            title_href_element = card.css('a.title')
            item['url'] = self.base_url + title_href_element.attrib.get('href')

            # Price block
            # regular_price = card.css('div.regular-price::text').re_first(r'\d+')
            # self.log(f"regular_price:::: {regular_price}")
            #
            # current_price = card.css('div.special-price::text').re_first(r'\d+')
            # self.log(f"current_price:::: {current_price}")
            #
            # if current_price is None:
            #     current_price = regular_price
            #
            # price_data = {
            #     "current": float(current_price) or None,
            #     "original": float(regular_price) or None,
            #     "sale_tag": ""
            # }
            #
            # if current_price and regular_price and current_price != regular_price:
            #     try:
            #         discount = int(100 - (int(current_price) / int(regular_price)) * 100)
            #         price_data['sale_tag'] = f"Скидка {discount}%"
            #     except ZeroDivisionError:
            #         pass
            #
            # item['price_data'] = price_data

            # Variants
            variants_text = card.css('div.variants-count::text').re_first(r'\d+')
            item['variants'] = int(variants_text) if variants_text else 1

            # self.item_count += 1
            yield scrapy.Request(
                url=item['url'],
                cookies=self.cookies,
                callback=self.parse_product_detail,
                meta={'item': item}
            )
            break

        # Go to next page if available and under 70
        # if self.item_count < self.max_items:
        #     next_page = response.css('a.pagination__next::attr(href)').get()
        #     if next_page:
        #         yield response.follow(next_page, callback=self.parse)

    def parse_product_detail(self, response):
        item = response.meta['item']

        # item['title'] = response.xpath('//meta[@itemprop="name"]/@content').get().strip()
        item['section'] = response.xpath('//div[contains(@class, "crumb")]//span[@itemprop="name"]/text()').getall()[2:-1]

        # Price data
        price_data = {
            "current": None,
            "original": None,
            "sale_tag": ""
        }

        current_price = response.css('div.price-block')
        self.log(f"current_price:::::::::::: {current_price[0]}")
        original_price = response.css('div.regular-price::text').get()
        self.log(f"original_price:::::::::::: {original_price}")
        c = original_price.re_first(r'[\d.]+')
        self.log(f"c:::::::::::: {c}")

        if current_price:
            price_data['current'] = float(current_price.re_first(r'[\d.]+'))
        if original_price:
            price_data['original'] = float(original_price.re_first(r'[\d.]+'))

        if current_price and original_price and current_price != original_price:
            try:
                discount = int(100 - (float(current_price) / float(original_price))) * 100
                price_data['sale_tag'] = f"Скидка {discount}%"
            except (ValueError, ZeroDivisionError):
                pass

        item['price_data'] = price_data

        # Stock information
        stock = {
            "in_stock": True,  # Default to True, adjust based on actual data
            "count": 0
        }

        availability = response.css('div.product-availability::text').get()
        if availability and "нет в наличии" in availability.lower():
            stock['in_stock'] = False

        # Try to extract stock count if available
        stock_text = response.css('div.product-stock::text').re_first(r'\d+')
        if stock_text:
            stock['count'] = int(stock_text)

        item['stock'] = stock

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

        item['assets'] = assets

        # Metadata (description, characteristics)
        properties = response.css('div.properties p.property')

        item['brand'] = properties.css('span.title:contains("Бренд") + span.value a::text').get()

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

        item['metadata'] = metadata

        # Add more characteristics as needed
        # characteristics = response.css('div.product-characteristics div.characteristic')
        # for char in characteristics:
        #     name = char.css('div.char-name::text').get()
        #     value = char.css('div.char-value::text').get()
        #     if name and value:
        #         metadata[name.strip()] = value.strip()
        #
        # item['metadata'] = metadata

        self.item_count += 1
        yield item
