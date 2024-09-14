import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import IgnoreRequest
from collections import Counter
import logging

class economistspider(scrapy.Spider):
    name = "economist_spider"
    def __init__(self, urls=None, *args, **kwargs):
        super(economistspider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'economist.json'
        self.stats_file = 'economist_spider_stats.json'
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
            
            
            # links = response.xpath('//div[@class="card-wrapper horizontal-card card_big_4:3 card_43"]//figure[@class="card-image"]/a/@href').getall()
            links=response.css('h3.css-1jzypbl a::attr(href)').getall()
            full_urls = [response.urljoin(url) for url in links]
        
            
            # Process the URL
            for url in full_urls:  
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

            title = response.css('div.css-b4a1pi span.css-rjcumh::text').getall()[1]
            author_name = response.css('div.css-1902i5q div.css-1s3lugw a::text').getall()
            author_url = response.css('div.css-1902i5q div.css-1s3lugw a::attr(href)').getall()
            published_date = response.css('time::text').getall()[1]
            article_content = ' '.join(response.css('p[data-component="paragraph"]::text').getall())
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
    "https://www.economist.com/science-and-technology?page=2",
    "https://www.economist.com/graphic-detail?page=2",
    "https://www.economist.com/briefing?page=2",
    "https://www.economist.com/essay?page=2",
    "https://www.economist.com/schools-brief?page=2",
    "https://www.economist.com/finance-and-economics?page=2",
    "https://www.economist.com/business?page=2",
    "https://www.economist.com/economic-and-financial-indicators?page=2",
    "https://www.economist.com/1843?page=2",
    "https://www.economist.com/culture?page=2",
    "https://www.economist.com/obituary?page=2",
    "https://www.economist.com/the-economist-reads?page=2",
    "https://www.economist.com/the-economist-reads?page=2",
    "https://www.economist.com/christmas-specials?page=2",
    "https://www.economist.com/the-world-this-week?page=2",
    "https://www.economist.com/asia?page=2",
    "https://www.economist.com/topics/china?page=2",
    "https://www.economist.com/international?page=2",
    "https://www.economist.com/the-americas?page=2",
    "https://www.economist.com/leaders?page=2",
    "https://www.economist.com/letters?page=2",
    "https://www.economist.com/by-invitation?page=2",


]

process = CrawlerProcess()
# Pass the list of URLs
process.crawl(economistspider, urls=urls_to_scrape)
process.start()
