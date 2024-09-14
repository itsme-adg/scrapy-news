import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import IgnoreRequest
from collections import Counter
import logging
import re

class telegraphspider(scrapy.Spider):
    name = "telegraph_spider"
    def __init__(self, urls=None, *args, **kwargs):
        super(telegraphspider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'telegraph.json'
        self.stats_file = 'telegraph_spider_stats.json'
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
            
            
            links=response.xpath('//ul[@class="storylisting"]//a/@href').getall()
            full_links = [response.urljoin(link) for link in links]
        
            
            # Process the URL
            for url in full_links:  
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

            title = response.xpath('//h1/text()').get()
            author_name = response.xpath('//div[@class="publishdate mt-32"]/strong/text()').get()
            author_url = None
            publish_date_time = response.xpath('//div[@class="publishdate mt-32"]/text()').getall()
            # Clean and format the date and time
            publish_text_clean = ' '.join([part.strip() for part in publish_date_time if part.strip()])
            date_time_match = re.search(r'(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2} [APM]{2})', publish_text_clean)
            if date_time_match:
                published_date = date_time_match.group(1)  # Extracted date: 13.09.24
                publish_time = date_time_match.group(2)  # Extracted time: 07:18 AM
            else:
                published_date = None
                publish_time = None
            article_content = ' '.join(response.xpath('//article[@id="contentbox"]/p/text()').getall())
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
    "https://www.telegraphindia.com/opinion/page-1",
    "https://www.telegraphindia.com/india/page-1",
    "https://www.telegraphindia.com/west-bengal/kolkata/page-1",
    "https://www.telegraphindia.com/world/page-1",
    "https://www.telegraphindia.com/business/page-1",
    "https://www.telegraphindia.com/sports/cricket/page-1",
    "https://www.telegraphindia.com/sports/football/page-1",
    "https://www.telegraphindia.com/sports/horse-racing/news?page=2",
    "https://www.telegraphindia.com/entertainment/page-1",
    "https://www.telegraphindia.com/states/page-1",
    "https://www.telegraphindia.com/life/page-1",
    "https://www.telegraphindia.com/west-bengal/page-1",
    "https://www.telegraphindia.com/north-east/page-1",
    "https://www.telegraphindia.com/jharkhand/page-1",
    "https://www.telegraphindia.com/science-tech/page-1",
    "https://www.telegraphindia.com/health/page-1",
    "https://www.telegraphindia.com/culture/bob-dylan-at-80/page-1",
    "https://www.telegraphindia.com/culture/heritage/page-1",
    "https://www.telegraphindia.com/travel/page-1",
    "https://www.telegraphindia.com/culture/style/page-1",
    "https://www.telegraphindia.com/personalities/page-1",
    "https://www.telegraphindia.com/books/page-1",
    "https://www.telegraphindia.com/culture/food/page-1",
    "https://www.telegraphindia.com/culture/arts/page-1",
    "https://www.telegraphindia.com/music/page-1",
    "https://www.telegraphindia.com/gallery/page-1",
    "https://www.telegraphindia.com/my-kolkata/events/page-1",
    


]

process = CrawlerProcess()
# Pass the list of URLs
process.crawl(telegraphspider, urls=urls_to_scrape)
process.start()
