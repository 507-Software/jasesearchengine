"""
Hello! Welcome to J.A.S.E. (Just Another Search Engine). This is a simple search engine that allows you to search for websites that have been crawled. You can also add new websites to the database by crawling them.

**To crawl a website**: Run this script normally, and it will ask you to enter a website URL to crawl.

**To run this as a server**: Use the command `gunicorn -w 4 -b 0.0.0.0:8000 main:app`

**License Notice**: This software uses the GPL license, so you can use it for free but you can't sell it.
"""
from flask import Flask, render_template, request
import os
import sqlite3
import json
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'recordings'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize the database
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

init_db()

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

def is_crawled(url):
    conn = sqlite3.connect('websites.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM websites WHERE url = ?", (url,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_links(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        return links
    except requests.RequestException:
        return []

def get_page_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.title.string if soup.title else 'No title'
    except requests.RequestException:
        return 'No title'

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

def load_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

def select_url_and_crawl():
    urls = load_json('websites.json')
    print("Select a URL to crawl:")
    for i, entry in enumerate(urls):
        print(f"{i + 1}. {entry['url']} (Depth: {entry['depth']})")
    
    choice = int(input("Enter the number of the URL to hack: ")) - 1
    if 0 <= choice < len(urls):
        url = urls[choice]['url']
        depth = urls[choice]['depth']
        crawl(url, depth)
    else:
        print("Invalid choice. Exiting.")

@app.route('/')
def index():
    conn = sqlite3.connect('websites.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM websites")
    website_count = c.fetchone()[0]
    conn.close()
    return render_template('index.html', website_count=website_count)

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.form.get('query')
    results = []
    if query:
        conn = sqlite3.connect('websites.db')
        c = conn.cursor()
        c.execute("SELECT url, title FROM websites WHERE title LIKE ?", ('%' + query + '%',))
        results = [{'url': row[0], 'title': row[1]} for row in c.fetchall()]
        conn.close()
    return render_template('results.html', query=query, results=results)

if __name__ == "__main__":
    # Uncomment the following line to run the Flask app
    # app.run(debug=True)
    
    # Run the CLI for selecting and crawling URLs
    select_url_and_crawl()
