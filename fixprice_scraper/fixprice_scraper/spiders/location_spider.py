import scrapy


class LocationSpiderSpider(scrapy.Spider):
    name = "location_spider"
    allowed_domains = ["fix-price.com"]
    start_urls = ["https://fix-price.com/catalog"]

    custom_settings = {
        "COOKIES_ENABLED": True,
        "ROBOTSTXT_OBEY": False
    }

    cookie_string = f"""
            i18n_redirected=ru; _cfuvid=SS9rd5CCsT8.K3BBl1EQo8TNIir0Po91YIlO7yMJQVg-1745298974184-0.0.1.1-604800000; sigma_experiments=%7B%22mainchange_zbrkjexu%22%3A%7B%22value%22%3Afalse%2C%22date%22%3A%222025-04-22%22%7D%7D; token=MzgwOTc4MzMzMQ%3D%3D%3Ae056c232ca0a8b75367c73987c5cb421; _ymab_param=QqS8n_pb_OnCP8-yhGmRB6P59cseidUwZXkwChMjkOU17RRNJderkUXXNckJYkobuBLZsMxLuLfLvzHza_42ZhzX9AQ; is-logged=; visited=true; skip-city=true; cf_clearance=8DQ6tZcFeKM7Pu3Bg0D2wPEMWHC9J2RChgwIrTnjhQ4-1745577439-1.2.1.1-owWAhX3BzbpkmMI6sKEj3cP0yWizR2eLsmhWl59f1XHJsZwyE1S1En1.AtYlfMRnm_ILeC_MdMieds4nquS.pwrDo6b4nCmhUixDRCbNnT3T2kkBP2LCzkNC0Asa3In2R3ic.6mDT6bJT3FhLRg78S_dYbQ.aFbHfXyL0rR1yq7YqjHPWLwiS6o53hL9hVPYAYw7s9pMv7TzSFevFsF9cFt2.XmuEanOgW12752zRBCydD9mlAWoAU_rljaGUnAMUBHfa0qDpsLGR3UnxW64ZAicuZie51Q_jAgsUcSIQzTUXnd2._py9UTCXP8XGa842KQTWmL2B6APm9.dTUV3IO08PlZG5oTm3Y2ngKbKqXE; locality=%7B%22city%22%3A%22%D0%95%D0%BA%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%BD%D0%B1%D1%83%D1%80%D0%B3%22%2C%22cityId%22%3A55%2C%22longitude%22%3A60.597474%2C%22latitude%22%3A56.838011%2C%22prefix%22%3A%22%D0%B3%22%7D
            """

    def start_requests(self):
        cookies = dict(cookie.strip().split('=', 1) for cookie in self.cookie_string.strip().split('; ') if '=' in cookie)

        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.parse,
            cookies=cookies,
            dont_filter=True,
        )

    def parse(self, response):
        # Extract city names from <span class="geo">
        cities = response.css("span.geo::text").getall()

        # Optional: remove duplicates
        unique_cities = list(set(cities))

        yield {"cities": unique_cities}
