import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin, urlparse
import time
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the database
conn = sqlite3.connect('websites.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS websites
             (id INTEGER PRIMARY KEY, url TEXT UNIQUE, title TEXT)''')
conn.commit()

def add_to_database(url, title):
    try:
        c.execute("INSERT INTO websites (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def get_all_links(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else 'No Title'
    add_to_database(url, title)
    links = []
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if is_valid(href):
            links.append(href)
    return links

def is_crawled(url):
    c.execute("SELECT 1 FROM websites WHERE url = ?", (url,))
    return c.fetchone() is not None

def crawl(url, max_depth=2):
    visited = set()
    queue = [(url, 0)]
    while queue:
        url, depth = queue.pop(0)
        if depth > max_depth:
            continue
        if url in visited or is_crawled(url):
            continue
        visited.add(url)
        logging.info(f"Crawling: {url} at depth {depth}")
        print(f"Visited: {url}")
        for link in get_all_links(url):
            if link not in visited and not is_crawled(link):
                queue.append((link, depth + 1))
        time.sleep(0.001)  # Add a delay between requests

if __name__ == "__main__":
    start_url = input("Enter a URL to crawl: ")
    initial_links = get_all_links(start_url)
    for link in initial_links:
        if not is_crawled(link):
            crawl(link)
    conn.close()