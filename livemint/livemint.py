import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import IgnoreRequest
from collections import Counter
import logging

class livemintSpider(scrapy.Spider):
    name = 'livemint_spider'   
    def __init__(self, urls=None, *args, **kwargs):
        super(livemintSpider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'livemint.json'
        self.stats_file = 'livemint_spider_stats.json'
        self.stats = {
            'total_baseURL': 0,
            'total_requests': 0,
            'successful_baseURL': 0,
            'failed_baseURL': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'articles_scraped': 0,
            'response_codes': Counter(),
            'errors': []
        }

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
            }, callback=self.parse, errback=self.errback_httpbin)

    def parse(self, response):
        self.stats['total_baseURL'] += 1
        self.stats['response_codes'][str(response.status)] += 1
        
        if response.status == 200:
            # self.stats['successful_requests'] += 1
            self.stats['successful_baseURL'] += 1
            relative_urls = response.css('div.listingNew a.imgSec::attr(href)').getall()
            full_urls = [response.urljoin(url) for url in relative_urls]

            for url in full_urls:            
                if url:
                    yield scrapy.Request(
                        url, 
                        callback=self.parse_article,
                        errback=self.errback_httpbin,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                    )
        else:
            self.stats['failed_baseURL'] += 1
            self.logger.error(f"Failed to parse page: {response.url} with status code: {response.status}")

    def parse_article(self, response):
        self.stats['total_requests'] += 1
        self.stats['response_codes'][str(response.status)] += 1
        
        if response.status == 200:
            self.stats['successful_requests'] += 1
            self.stats['articles_scraped'] += 1
            
            title = response.xpath('//h1/text()').get()
            author_name = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/strong/text()').get()
            author_url = response.xpath('//div[contains(@class, "storyPage_authorDesc__zPjwo")]/a/@href').get()
            published_date = response.xpath('//div[contains(@class, "storyPage_date__JS9qJ")]//span/text()').get()
            article_content = response.xpath('//div[@class="storyPage_storyContent__m_MYl"]//p/text()').getall()
            article_content = ' '.join([p.strip() for p in article_content if p.strip()])
        else:
            self.stats['failed_requests'] += 1
            self.logger.error(f"Failed to parse article: {response.url} with status code: {response.status}")
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

    def errback_httpbin(self, failure):
        self.stats['failed_requests'] += 1
        if failure.check(IgnoreRequest):
            self.logger.error(f"IgnoreRequest error on {failure.request.url}")
            self.stats['errors'].append(f"IgnoreRequest error on {failure.request.url}")
        else:
            self.logger.error(f"Error on {failure.request.url}: {str(failure.value)}")
            self.stats['errors'].append(f"Error on {failure.request.url}: {str(failure.value)}")

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

    def closed(self, reason):
        # Save statistics to a JSON file
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=4)
        
        
        self.logger.info(f"Total BaseURLs: {self.stats['total_baseURL']}")
        self.logger.info(f"Successful BaseURL requests: {self.stats['successful_baseURL']}")
        self.logger.info(f"Failed BaseURL requests: {self.stats['failed_baseURL']}")
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total requests: {self.stats['total_requests']}")
        self.logger.info(f"Successful requests: {self.stats['successful_requests']}")
        self.logger.info(f"Failed requests: {self.stats['failed_requests']}")
        self.logger.info(f"Articles scraped: {self.stats['articles_scraped']}")
        self.logger.info(f"Response codes: {dict(self.stats['response_codes'])}")

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

process = CrawlerProcess({
    'LOG_LEVEL': 'INFO',
    'CONCURRENT_REQUESTS': 16,
    'DOWNLOAD_DELAY': 1,
    'RANDOMIZE_DOWNLOAD_DELAY': True,
})

# Pass the list of URLs
process.crawl(livemintSpider, urls=urls_to_scrape)
process.start()