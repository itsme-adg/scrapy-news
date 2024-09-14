import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import IgnoreRequest
from collections import Counter
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException


class DTspider(scrapy.Spider):
    name = "dt_spider"
    
    def __init__(self, urls=None, max_read_more=2, *args, **kwargs):
        super(DTspider, self).__init__(*args, **kwargs)
        self.start_urls = urls if urls else []
        self.output_file = 'DT.json'
        self.stats_file = 'dt_spider_stats.json'
        self.max_read_more = int(max_read_more)  # Convert to int in case it's passed as a string
        self.stats = {
            'total_baseURL': 0,
            'total_requests': 0,
            'successful_baseURL': 0,
            'failed_baseURL': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'articles_scraped': 0,
            'read_more_clicks': 0,
            'response_codes': Counter(),
            'errors': []
        }
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--start-maximized")
        self.driver = None
        self.current_base_url = None
        self.articles_to_parse = 0
        self.articles_parsed = 0
        # self.driver = webdriver.Chrome(options=chrome_options)

        # Create an empty list in the file if it doesn't exist
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w') as f:
                json.dump([], f)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, errback=self.errback_httpbin)

    def scroll_to_bottom(self, wait_time=1):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)  # Wait for any dynamic content to load


    def parse(self, response):
        self.stats['total_baseURL'] += 1
        self.stats['response_codes'][str(response.status)] += 1
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.current_base_url = response.meta.get('url')

        if response.status == 200:
            self.stats['successful_baseURL'] += 1
            self.driver.get(response.url)

            try:
                self.logger.info("Scrolling to the bottom of the page...")
                self.scroll_to_bottom()
                self.logger.info("Finished scrolling to the bottom of the page")

                while self.stats['read_more_clicks'] < self.max_read_more:
                    wait = WebDriverWait(self.driver, 10) 

                    try:
                        read_more_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '//div[@data-test-id="load-more"]'))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", read_more_button)
                        # time.sleep(2)  # Wait for scroll to complete
                        # self.driver.execute_script("arguments[0].scrollIntoView();", read_more_button)
                        try:
                            read_more_button.click()
                        except ElementClickInterceptedException:
                            # If direct click fails, try JavaScript click
                            self.driver.execute_script("arguments[0].click();", read_more_button)
                        
                        read_more_button.click()
                        time.sleep(2)
                        self.stats['read_more_clicks'] += 1
                        
                    except (TimeoutException, NoSuchElementException):
                        self.logger.info("No more 'Read More' button found or it's not clickable. Finished loading all articles.")
                        break

                if self.stats['read_more_clicks'] >= self.max_read_more:
                    self.logger.info(f"Reached maximum number of 'Read More' clicks ({self.max_read_more})")
                
                headlines = self.driver.find_elements(By.XPATH, '//div[@data-test-id="headline"]/a')
                for headline in headlines:
                        url = headline.get_attribute('href')
                        if url:
                            # print("!1!")
                            yield scrapy.Request(url, callback=self.parse_article)    

            except Exception as e:
                self.logger.error(f"Error parsing page: {response.url}. Error: {str(e)}")
                self.stats['errors'].append(f"Error parsing page: {response.url}. Error: {str(e)}")

           

        else:
            self.stats['failed_baseURL'] += 1
            self.logger.error(f"Failed to parse page: {response.url} with status code: {response.status}")

    def parse_article(self, response):
        self.stats['total_requests'] += 1
        self.stats['response_codes'][str(response.status)] += 1

        if response.status == 200:
            self.stats['successful_requests'] += 1
            self.stats['articles_scraped'] += 1

            title = response.xpath('//div[@class="arrow-component arr--story-headline story-headline-m_wrapper__1Wey6"]/h1/bdi/text()').get()
            author_name = response.css('div[data-test-id="author-name"] a::text').get()
            author_relative_url = response.css('div[data-test-id="author-name"] a::attr(href)').get()
        
            # Construct the full URL for the author using response.urljoin()
            author_url = response.urljoin(author_relative_url) if author_relative_url else None
            published_date = response.css('time::attr(datetime)').get()
            article_content = ' '.join(response.css('div[data-test-id="text"] p::text').getall())

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
        else:
            self.stats['failed_requests'] += 1
            self.logger.error(f"Failed to parse article: {response.url} with status code: {response.status}")

    def close_driver(self):
        if self.driver:
            self.logger.info(f"Closing WebDriver for URL: {self.current_base_url}")
            self.driver.quit()
            self.driver = None
    
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
            with open(self.output_file, 'r+') as file:
                try:
                    articles = json.load(file)
                except json.JSONDecodeError:
                    articles = []
                articles.append(data)
                file.seek(0)
                json.dump(articles, file, indent=4)
                file.truncate()
        except FileNotFoundError:
            with open(self.output_file, 'w') as file:
                json.dump([data], file, indent=4)
    
    def closed(self, reason):

        if self.driver:
            self.close_driver()

        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=4)
        
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Total BaseURLs: {self.stats['total_baseURL']}")
        self.logger.info(f"Successful BaseURL requests: {self.stats['successful_baseURL']}")
        self.logger.info(f"Failed BaseURL requests: {self.stats['failed_baseURL']}")
        self.logger.info(f"Total requests: {self.stats['total_requests']}")
        self.logger.info(f"Successful requests: {self.stats['successful_requests']}")
        self.logger.info(f"Failed requests: {self.stats['failed_requests']}")
        self.logger.info(f"Articles scraped: {self.stats['articles_scraped']}")
        self.logger.info(f"Response codes: {dict(self.stats['response_codes'])}")
        

# List of URLs to scrape
urls_to_scrape = [
    # "https://digitalterminal.in/trending",
    "https://digitalterminal.in/smart-phone",
    "https://digitalterminal.in/device",
    "https://digitalterminal.in/solutions",
    "https://digitalterminal.in/telecom",
    "https://digitalterminal.in/channel",
    "https://digitalterminal.in/enterprise",
    "https://digitalterminal.in/edutech",
    # "https://digitalterminal.in/health-tech",
    # "https://digitalterminal.in/tech-companies",
    # "https://digitalterminal.in/government",
    # "https://digitalterminal.in/dtv",
    # "https://digitalterminal.in/product-reviews",
    # "https://digitalterminal.in/dt-events",
    # "https://digitalterminal.in/interview",
    # "https://digitalterminal.in/meet-your-boss",
    # "https://digitalterminal.in/association-news",
    # "https://digitalterminal.in/case-study",
    # "https://digitalterminal.in/resource",

    
]

process = CrawlerProcess()
process.crawl(DTspider, urls=urls_to_scrape)
process.start()