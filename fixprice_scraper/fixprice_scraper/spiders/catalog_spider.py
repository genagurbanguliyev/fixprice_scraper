import scrapy
import json


class CatalogSpiderSpider(scrapy.Spider):
    name = "catalog_spider"
    allowed_domains = ["fix-price.com"]
    start_urls = ["https://fix-price.com/catalog"]

    custom_settings = {
        "COOKIES_ENABLED": True,
        "ROBOTSTXT_OBEY": False
    }

    # Paste your cookie string here
    cookie_string = f"""
        i18n_redirected=ru; _cfuvid=SS9rd5CCsT8.K3BBl1EQo8TNIir0Po91YIlO7yMJQVg-1745298974184-0.0.1.1-604800000; sigma_experiments=%7B%22mainchange_zbrkjexu%22%3A%7B%22value%22%3Afalse%2C%22date%22%3A%222025-04-22%22%7D%7D; token=MzgwOTc4MzMzMQ%3D%3D%3Ae056c232ca0a8b75367c73987c5cb421; _ymab_param=QqS8n_pb_OnCP8-yhGmRB6P59cseidUwZXkwChMjkOU17RRNJderkUXXNckJYkobuBLZsMxLuLfLvzHza_42ZhzX9AQ; is-logged=; visited=true; skip-city=true; cf_clearance=8DQ6tZcFeKM7Pu3Bg0D2wPEMWHC9J2RChgwIrTnjhQ4-1745577439-1.2.1.1-owWAhX3BzbpkmMI6sKEj3cP0yWizR2eLsmhWl59f1XHJsZwyE1S1En1.AtYlfMRnm_ILeC_MdMieds4nquS.pwrDo6b4nCmhUixDRCbNnT3T2kkBP2LCzkNC0Asa3In2R3ic.6mDT6bJT3FhLRg78S_dYbQ.aFbHfXyL0rR1yq7YqjHPWLwiS6o53hL9hVPYAYw7s9pMv7TzSFevFsF9cFt2.XmuEanOgW12752zRBCydD9mlAWoAU_rljaGUnAMUBHfa0qDpsLGR3UnxW64ZAicuZie51Q_jAgsUcSIQzTUXnd2._py9UTCXP8XGa842KQTWmL2B6APm9.dTUV3IO08PlZG5oTm3Y2ngKbKqXE; locality=%7B%22city%22%3A%22%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3%22%2C%22cityId%22%3A55%2C%22longitude%22%3A60.597474%2C%22latitude%22%3A56.838011%2C%22prefix%22%3A%22%D0%B3%22%7D
        """

    def start_requests(self):
        cookies = {k.strip(): v for k, v in (item.split("=") for item in self.cookie_string.split(";"))}
        yield scrapy.Request(
            url=self.start_urls[0],
            cookies=cookies,
            callback=self.parse_catalog
        )

    def parse_catalog(self, response):
        catalog_data = []

        accordion_blocks = response.css('div.category-tree > div.accordion')
        for block in accordion_blocks:
            item = self.parse_block(block)
            if item:
                catalog_data.append(item)

        with open("catalog.json", "w", encoding="utf-8") as f:
            json.dump(catalog_data, f, ensure_ascii=False, indent=4)

        self.log("Saved catalog data to catalog.json")

    def parse_block(self, block):
        title_el = block.css("a.title:not(.subtitle)")
        if not title_el:
            return None

        item = {
            "text": title_el.css("::text").get(default="").strip(),
            "link": title_el.attrib.get("href"),
            "subcatalog": []
        }

        # Check for sub-items
        sub_links = block.css("ul.children > li > a.subtitle")
        if sub_links:
            for sub in sub_links:
                sub_item = {
                    "text": sub.css("::text").get(default="").strip(),
                    "link": sub.attrib.get("href"),
                    "subcatalog": None
                }
                item["subcatalog"].append(sub_item)

        if not item["subcatalog"]:
            item["subcatalog"] = None

        return item
