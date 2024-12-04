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
    c.execute('''CREATE TABLE IF NOT EXISTS websites
                 (id INTEGER PRIMARY KEY, url TEXT UNIQUE, title TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_to_database(url, title):
    conn = sqlite3.connect('websites.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO websites (url, title) VALUES (?, ?)", (url, title))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
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

def crawl(url, max_depth):
    visited = set()
    queue = [(url, 0)]
    while queue:
        current_url, depth = queue.pop(0)
        if depth > max_depth:
            continue
        if current_url in visited or is_crawled(current_url):
            continue
        visited.add(current_url)
        print(f"Crawling: {current_url} at depth {depth}")
        for link in get_all_links(current_url):
            if link not in visited and not is_crawled(link):
                queue.append((link, depth + 1))
        time.sleep(0.1)  # Add a delay between requests

def load_json_and_crawl(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
        for entry in data:
            url = entry.get('url')
            depth = entry.get('depth', 1)  # Default depth is 1 if not specified
            if url and not is_crawled(url):
                crawl(url, depth)

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
    # Load JSON data and start crawling when the application starts
    load_json_and_crawl('websites.json')
    app.run(debug=True)
