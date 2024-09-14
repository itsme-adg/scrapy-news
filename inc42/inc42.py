import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import IgnoreRequest
from collections import Counter
import logging

class inc42spider(scrapy.Spider):
    name = "inc42_spider"
    def __init__(self, urls=None, *args, **kwargs):
        super(inc42spider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'inc42.json'
        self.stats_file = 'inc42_spider_stats.json'
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
            yield scrapy.Request(
                url, callback=self.parse, errback=self.errback_httpbin)

    def parse(self, response):
        self.stats['total_baseURL'] += 1
        self.stats['response_codes'][str(response.status)] += 1

        if response.status == 200:
            self.stats['successful_baseURL'] += 1
            # Extracting the specific link from the h2 tag with class 'entry-title recommended-block-head'
            
            
            links = response.xpath('//div[@class="card-wrapper horizontal-card card_big_4:3 card_43"]//figure[@class="card-image"]/a/@href').getall()
            # full_urls = [response.urljoin(url) for url in link]
        
            
            # Process the URL
            for url in links:  
                if url:
                    yield scrapy.Request(
                    url, 
                    callback=self.parse_article
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

            title = response.xpath('//h1[@class="entry-title"]/text()').get()
            author_name = response.xpath('//a[@rel="author"]/text()').get()
            author_url = response.xpath('//a[@rel="author"]/@href').get()
            published_date = response.xpath('//div[@class="date"]/span[1]/text()').get()
            article_content = response.xpath('//div[@class="storyPage_storyContent__m_MYl"]//p/text()').getall()
            article_content = ' '.join(response.xpath('//div[@class="single-post-content"]//p//text()').getall())
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
        try:
            # Load existing data from the JSON file
            with open(self.output_file, 'r+') as file:
                try:
                    articles = json.load(file)
                except json.JSONDecodeError:
                    # In case the file is empty or has invalid JSON, start with an empty list
                    articles = []
                # Append new article data
                articles.append(data)
                # Move cursor to the beginning of the file
                file.seek(0)
                # Write updated data
                json.dump(articles, file, indent=4)
        except FileNotFoundError:
            # If the file is not found, create it and write the data
            with open(self.output_file, 'w') as file:
                json.dump([data], file, indent=4)

    
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
    "https://inc42.com/industry/fintech/page/1/",
    "https://inc42.com/industry/travel-tech/page/1/",
    "https://inc42.com/industry/electric-vehicles/page/1/",
    "https://inc42.com/industry/electric-vehicles/page/1/",
    "https://inc42.com/industry/healthtech/page/1/",
    "https://inc42.com/industry/edtech/page/1/",
    "https://inc42.com/industry/it/page/1/",
    "https://inc42.com/industry/logistics/page/1/",
    "https://inc42.com/industry/retail/page/1/",
    "https://inc42.com/industry/ecommerce/page/1/",
    "https://inc42.com/industry/startup-ecosystem/page/1/",
    "https://inc42.com/industry/enterprisetech/page/1/",
    "https://inc42.com/industry/cleantech/page/1/",
    "https://inc42.com/industry/consumer-services/page/1/",
    "https://inc42.com/industry/agritech/page/1/",
    "https://inc42.com/buzz/page/2/",
    "https://inc42.com/features/page/1/",
    "https://inc42.com/startups/page/1/",
    "https://inc42.com/tag/what-the-financials/page/1/",
    "https://inc42.com/tag/30-startups-to-watch/page/1/",
    "https://inc42.com/tag/funding-galore/page/1/",
    "https://inc42.com/tag/new-age-tech-stocks/page/1/",
    "https://inc42.com/resources/page/1/",


]

process = CrawlerProcess()
# Pass the list of URLs
process.crawl(inc42spider, urls=urls_to_scrape)
process.start()
