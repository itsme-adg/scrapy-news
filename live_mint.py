import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess

class livemintspider(scrapy.Spider):
    name = 'livemint_spider'
    
    def __init__(self, urls=None, *args, **kwargs):
        super(livemintspider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'livemint.json'

        # Create an empty list in the file if it doesn't exist
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w') as f:
                json.dump([], f)
        
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })

    def parse(self, response):
        relative_urls = response.css('div.listingNew a.imgSec::attr(href)').getall()
        full_urls = [response.urljoin(url) for url in relative_urls]

        for url in full_urls:            
            if url:
                yield scrapy.Request(
                    url, 
                    callback=self.parse_article,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                )

    def parse_article(self, response):    
        if response.status == 200:
            title = response.xpath('//h1/text()').get()
            author_name = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/strong/text()').get()
            author_url = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/@href').get()
            published_date = response.xpath('//div[contains(@class, "storyPage_date__JS9qJ")]//span/text()').get()
            article_content = response.xpath('//div[@class="storyPage_storyContent__m_MYl"]//p/text()').getall()
            article_content = ' '.join([p.strip() for p in article_content if p.strip()])
        else:
            title = None
            author_name = None
            author_url = None
            published_date = None
            article_content = None

        article_data = {
            "Response Code": response.status,
            "Article URL": response.url,
            "Title": title,
            "Author Name": author_name,
            "Author URL": author_url,
            "Article Content": article_content,
            "Published Date": published_date
        }

        # Append article data to the JSON file
        self.append_to_json_file(article_data)

    def append_to_json_file(self, data):
        # Load existing data from the JSON file
        with open(self.output_file, 'r+') as file:
            articles = json.load(file)
            # Append new article data
            articles.append(data)
            # Move cursor to the beginning of the file
            file.seek(0)
            # Write updated data
            json.dump(articles, file, indent=4)

# List of URLs to scrape
urls_to_scrape = [
    "https://www.livemint.com/market/stock-market-news/page-1",
    "https://www.livemint.com/market/commodities/page-1",
    "https://www.livemint.com/market/live-blog/page-1",
    "https://www.livemint.com/market/mark-to-market/page-1",
    "https://www.livemint.com/market/cryptocurrency/page-1",
    "https://www.livemint.com/market/ipo/page-1",
    "https://www.livemint.com/latest-news/page-1",
    "https://www.livemint.com/news/india/page-1",
    "https://www.livemint.com/news/world/page-1",
    "https://www.livemint.com/wsj/page-1",
    "https://www.livemint.com/economist/page-1",
    "https://www.livemint.com/companies/start-ups/page-1",
    "https://www.livemint.com/companies/company-results/page-1",
    "https://www.livemint.com/companies/people/page-1",
    "https://www.livemint.com/money/personal-finance/page-1",
    "https://www.livemint.com/insurance/news/page-1",
    "https://www.livemint.com/money/ask-mint-money/page-1",
    "https://www.livemint.com/mutual-fund/page-1",
    "https://www.livemint.com/technology/gadgets",
    "https://www.livemint.com/technology/tech-reviews",
    "https://www.livemint.com/topic/new-app",
    "https://www.livemint.com/topic/5g-tech",
    "https://www.livemint.com/topic/foldable-smartphones",
    "https://www.livemint.com/politics",
    "https://www.livemint.com/opinion"


]

process = CrawlerProcess()

# Pass the list of URLs
process.crawl(livemintspider, urls=urls_to_scrape)
process.start()
