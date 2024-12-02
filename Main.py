from flask import Flask, render_template, request, send_from_directory
import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin, urlparse

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'recordings'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else 'No Title'
    add_to_database(url, title)
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if is_valid(href):
            yield href

def crawl(url, max_depth=2):
    visited = set()
    queue = [(url, 0)]
    while queue:
        url, depth = queue.pop(0)
        if depth > max_depth:
            continue
        if url in visited:
            continue
        visited.add(url)
        for link in get_all_links(url):
            if link not in visited:
                queue.append((link, depth + 1))

# Initialize the database connection
def get_db_connection():
    conn = sqlite3.connect('websites.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return 'File uploaded successfully'

@app.route('/recordings/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT url, title FROM websites WHERE title LIKE ? OR url LIKE ?", ('%' + query + '%', '%' + query + '%'))
        results = c.fetchall()
        conn.close()
        return render_template('results.html', query=query, results=results)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
    start_url = 'https://example.com'
    crawl(start_url)
    conn.close()