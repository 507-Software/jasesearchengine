"""
Hello! Welcome to J.A.S.E. (Just Another Search Engine). This is a simple search engine that allows you to search for websites that have been crawled. You can also add new websites to the database by crawling them.

**To crawl a website**: Run this script normally, and it will ask you to enter a website URL to crawl.

**To run this as a server**: Use the command `gunicorn -w 4 -b 0.0.0.0:8000 main:app`

**License Notice**: This software uses the GPL license, so you can use it for free but you can't sell it.
"""
from flask import Flask, render_template, request
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'recordings'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('websites.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS websites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_to_database(url, title):
    try:
        conn = sqlite3.connect('websites.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO websites (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_page_title(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.title.string.strip() if soup.title and soup.title.string else 'No Title'
    except requests.RequestException as e:
        print(f"Error fetching title from {url}: {e}")
        return 'No Title'

def get_all_links(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        return links
    except requests.RequestException as e:
        print(f"Error fetching links from {url}: {e}")
        return []

def crawl(url, depth=2):
    queue = [(url, depth)]
    visited = set()

    while queue:
        current_url, current_depth = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"Crawling: {current_url}")

        # Get page title
        title = get_page_title(current_url)
        print(f"Title: {title}")

        # Add to database
        add_to_database(current_url, title)

        if current_depth > 0:
            links = get_all_links(current_url)
            for link in links:
                if link not in visited:
                    queue.append((link, current_depth - 1))
        time.sleep(0.1)  # Delay between requests

@app.route('/')
def index():
    conn = sqlite3.connect('websites.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM websites")
    website_count = c.fetchone()[0]
    conn.close()
    return render_template('index.html', website_count=website_count)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    results = []
    if query:
        conn = sqlite3.connect('websites.db')
        c = conn.cursor()
        c.execute("SELECT url, title FROM websites WHERE title LIKE ? OR url LIKE ?", ('%' + query + '%', '%' + query + '%'))
        results = [{'url': row[0], 'title': row[1]} for row in c.fetchall()]
        conn.close()
    return render_template('results.html', query=query, results=results)

def select_url_and_crawl():
    start_url = input("Enter the URL to start crawling: ")
    crawl(start_url)

if __name__ == "__main__":
    init_db()
    select_url_and_crawl()
    # Uncomment the following line to run the Flask app
    # app.run(debug=True)
