from scrapy import Spider


class CourtReserveSpider(Spider):
    name = 'courtreserve'
    allowed_domains = ['app.courtreserve.com']
    start_urls = ['https://app.courtreserve.com/Online/Portal/Index/6801']

    def parse(self, response):
        print("\n")
        print("HTTP STATUS: "+str(response.status))
        print(response.css("h3::text").get())
        print("\n")
