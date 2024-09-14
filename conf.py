from economist import economistspider
import scrapy
import json
import os
from scrapy.crawler import CrawlerProcess


def get_urls(foldername,max_pages=5):
    urls_to_scrape=[]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, foldername, 'urls.txt')
    with open(file_path, 'r') as file:
        urls = file.readlines()
    
    for url in urls:
        url = url.strip()  # Remove extra spaces or newlines
        if url:
            for page_num in range(1, max_pages + 1):
                urls_to_scrape.append(f"{url}?page={page_num}")    
    return urls_to_scrape    


# Check the modified URLs (optional, for debugging purposes)
print("Modified URLs to scrape:")
# print(get_urls('economist'))


process = CrawlerProcess()
process.crawl(economistspider, urls=get_urls('economist'))
process.start()