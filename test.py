import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging

import scrapy

class LivemintSpider(scrapy.Spider):
    name = 'livemint_spider'

    def __init__(self, start_url=None, *args, **kwargs):
        super(LivemintSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else [
            'https://www.livemint.com/market/'
        ]

    # Define headers to simulate a browser
    custom_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Referer': 'https://www.livemint.com/',
                    'Upgrade-Insecure-Requests': '1'
                    }


    def parse(self, response):
        # Extract all div blocks that have article links
        article_divs = response.xpath('//div[@class="listingNew clearfix impression-candidate ga-tracking eventFired"]')

        for article in article_divs:
            # Extract the relative URL from the <a> tag
            relative_url = article.xpath('.//a/@href').get()
            print("************************************************************************************",relative_url)
            # Form the full URL by combining the base URL with the relative URL
            full_url = response.urljoin(relative_url)

            # Make a request to each article URL and call the parse_article method
            yield scrapy.Request(
                full_url, 
                callback=self.parse_article, 
                headers=self.custom_headers  # Include headers in each request
            )

    def parse_article(self, response):
        if response.status == 200:
            # Successful response, extract the data
            title = response.xpath('//h1/text()').get()
            author_name = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/strong/text()').get()
            author_url = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/@href').get()
            published_date = response.xpath('//div[contains(@class, "storyPage_date__JS9qJ")]//span/text()').get()
            article_content = response.xpath('//div[@class="storyPage_storyContent__m_MYl"]//p/text()').getall()
            article_content = ' '.join([p.strip() for p in article_content if p.strip()])
        else:
            # Unsuccessful response, set all fields to None or empty
            title = None
            author_name = None
            author_url = None
            published_date = None
            article_content = None

        # Yield the extracted data as a dictionary
        yield {
            "Response Code": response.status,  # Include response code in the output
            "Article URL": response.url,
            "Title": title,
            "Author Name": author_name,
            "Author URL": author_url,
            "Article Content": article_content,
            "Published Date": published_date
        }

process = CrawlerProcess(settings={
    "FEEDS": {
        "articles.json": {"format": "json"},
    }
})

custom_settings = {
    'ROBOTSTXT_OBEY': False,  # Ignore robots.txt rules
    'COOKIES_ENABLED': True,  # Enable cookies
    'DOWNLOAD_DELAY': 2,  # Delay requests to avoid being blocked
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
}

process.crawl(LivemintSpider)
process.start()
