#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Extraction Script for Wikipedia's Highest-Grossing Films page.
Extracts film data, stores in SQLite DB, and exports to JSON.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sqlite3
import os
import time
import random
from typing import Dict, List, Any

# Constants
URL = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
DB_PATH = "data/highest_grossing_films.db"
JSON_PATH = "data/films.json"

def fetch_wikipedia_page(url: str) -> str:
    """Fetch HTML content from Wikipedia"""
    print(f"Fetching page from {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        print("Successfully fetched page")
        return response.text
    else:
        raise Exception(f"Failed to fetch page. Status code: {response.status_code}")

def parse_html_content(html_content: str) -> List[Dict[str, Any]]:
    """Extract film data from HTML content"""
    print("Parsing HTML content...")
    
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        print("Using lxml parser")
    except Exception:
        print("Falling back to html.parser")
        soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create data directory and save debug HTML
    os.makedirs('data', exist_ok=True)
    with open('data/debug_page.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Method 1: Try to find tables with 'wikitable' class
    print("Looking for tables with class 'wikitable'")
    tables = soup.find_all('table', class_='wikitable')
    print(f"Found {len(tables)} tables with class 'wikitable'")
    
    if not tables:
        # Method 2: Try to find any table
        print("Looking for any tables")
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        if not tables:
            print("No tables found in the page")
            return []
    
    # Method 3: Look for headings related to highest-grossing films
    section_heading = soup.find(lambda tag: tag.name in ['h1', 'h2', 'h3'] and 
                               'highest-grossing films' in tag.text.lower())
    if section_heading:
        print(f"Found relevant section: {section_heading.text}")
        # Try to find the table after this heading
        section_table = section_heading.find_next('table')
        if section_table:
            print("Found table after the section heading")
            tables.insert(0, section_table)  # Prioritize this table
    
    # Find the table with relevant headers
    print("Looking for table with film data...")
    table = None
    for i, t in enumerate(tables):
        headers = [h.text.strip().lower() for h in t.find_all('th')]
        print(f"Table {i+1} headers: {headers}")
        
        # Try different conditions to find the right table
        if any(h for h in headers if 'title' in h or 'film' in h):
            if any(h for h in headers if 'box office' in h or 'gross' in h or 'worldwide' in h):
                table = t
                print(f"Found relevant table at index {i+1}")
                break
            
    # Fallback - just use the first table if we couldn't identify one by headers
    if not table and tables:
        table = tables[0]
        print("Using first table as fallback")
    
    if not table:
        print("No suitable table found")
        return []
    
    # Extract column indices
    header_row = table.find('tr')
    headers = [th.text.strip().lower() for th in header_row.find_all('th')]
    print(f"Header row: {headers}")
    
    # Find column indices with fallbacks
    title_idx = -1
    for i, h in enumerate(headers):
        if 'title' in h or 'film' in h:
            title_idx = i
            break
    if title_idx == -1:
        title_idx = 1 if len(headers) > 1 else 0
        
    year_idx = -1
    for i, h in enumerate(headers):
        if 'year' in h or 'released' in h or 'release' in h:
            year_idx = i
            break
            
    box_office_idx = -1
    for i, h in enumerate(headers):
        if 'box office' in h or 'gross' in h or 'worldwide' in h:
            box_office_idx = i
            break
    if box_office_idx == -1:
        # Try to find a column with currency symbols
        for i, h in enumerate(headers):
            if '$' in h or '¥' in h or '€' in h:
                box_office_idx = i
                break
        if box_office_idx == -1:
            box_office_idx = 2 if len(headers) > 2 else len(headers) - 1
    
    print(f"Using indices - Title: {title_idx}, Year: {year_idx}, Box Office: {box_office_idx}")
    
    # Extract data from rows
    films_data = []
    rows = table.find_all('tr')[1:]  # Skip header row
    print(f"Processing {len(rows)} data rows")
    
    for row in rows:
        cells = row.find_all(['th', 'td'])
        
        if len(cells) <= max(title_idx, box_office_idx):
            continue
        
        try:
            # Extract title and wiki link
            title_cell = cells[title_idx]
            title_link = title_cell.find('a')
            
            if title_link:
                title = title_link.text.strip()
                wiki_link = title_link.get('href', '')
            else:
                title = title_cell.text.strip()
                wiki_link = ""
            
            # Clean title (remove footnotes)
            title = re.sub(r'\[\d+\]', '', title).strip()
            
            # Extract box office value
            box_office_text = cells[box_office_idx].text.strip()
            box_office_text = re.sub(r'\[\d+\]', '', box_office_text)
            box_office_value = re.sub(r'[^\d.]', '', box_office_text)
            
            try:
                box_office = float(box_office_value) if box_office_value else 0.0
                # Fix extremely large values
                if box_office > 5000000000:
                    magnitude = len(str(int(box_office)))
                    if magnitude > 10:
                        box_office = box_office / (10 ** (magnitude - 10))
            except ValueError:
                box_office = 0.0
            
            # Extract year
            year = 0
            if year_idx != -1 and year_idx < len(cells):
                year_text = cells[year_idx].text.strip()
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', year_text)
                if year_match:
                    year = int(year_match.group(1))
            else:
                # Try to extract year from title
                year_match = re.search(r'\((\d{4})\)', title)
                if year_match:
                    year = int(year_match.group(1))
                    title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
            
            # Create film data
            film_data = {
                'title': title,
                'release_year': year,
                'box_office': box_office,
                'wiki_link': wiki_link,
                'director': "Unknown",
                'country': "Unknown",
            }
            
            films_data.append(film_data)
            
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    print(f"Extracted data for {len(films_data)} films")
    
    # Show a sample of extracted data
    if films_data:
        print("Sample of extracted data:")
        for i, film in enumerate(films_data[:3]):
            print(f"  {i+1}. {film['title']} - Year: {film['release_year']}, Box Office: {film['box_office']}")
    
    return films_data

def get_film_details(film_url: str) -> Dict[str, str]:
    """Extract director and country from film's Wikipedia page"""
    details = {"director": "Unknown", "country": "Unknown"}
    
    if not film_url:
        return details
    
    # Maximum number of retries
    max_retries = 3
    base_timeout = 10
    
    for attempt in range(max_retries):
        try:
            # Exponential backoff for timeout and retry delay
            current_timeout = base_timeout * (2 ** attempt)
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'}
            full_url = f"https://en.wikipedia.org{film_url}"
            print(f"Fetching details from: {full_url} (Attempt {attempt+1}/{max_retries})")
            
            response = requests.get(full_url, headers=headers, timeout=current_timeout)
            
            if response.status_code != 200:
                print(f"Received status code {response.status_code}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            info_box = soup.find('table', class_='infobox')
            
            if info_box:
                # Extract director
                director_rows = info_box.find_all(lambda tag: tag.name == 'th' and 
                                                ('Directed by' in tag.text or 'Director' in tag.text))
                
                for row in director_rows:
                    if row and row.find_next('td'):
                        director_text = row.find_next('td').text.strip()
                        # Clean and get the first director
                        director_text = re.sub(r'\[\d+\]', '', director_text)  # Remove citations
                        # Split by common separators and take the first one
                        director_parts = re.split(r',|\band\b|;|\|', director_text, maxsplit=1)
                        details["director"] = director_parts[0].strip()
                        break
                
                # Extract country
                country_rows = info_box.find_all(lambda tag: tag.name == 'th' and 
                                               ('Country' in tag.text or 'Countries' in tag.text))
                
                for row in country_rows:
                    if row and row.find_next('td'):
                        country_text = row.find_next('td').text.strip()
                        # Clean and get the first country
                        country_text = re.sub(r'\[\d+\]', '', country_text)  # Remove citations
                        # Split by common separators and take the first one
                        country_parts = re.split(r',|\band\b|;|\|', country_text, maxsplit=1)
                        details["country"] = country_parts[0].strip()
                        break
            
            # Clean up extracted text
            for key in details:
                if details[key] != "Unknown":
                    details[key] = re.sub(r'\s+', ' ', details[key]).strip()  # Clean whitespace
            
            # If we got here without exception, break the retry loop
            break
            
        except requests.exceptions.Timeout:
            print(f"Timeout occurred (Attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error fetching details: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    print(f"Extracted details: Director={details['director']}, Country={details['country']}")
    return details

def enrich_film_data(films_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add director and country information to film data"""
    print("Enriching film data with directors and countries...")
    enriched_data = [dict(film) for film in films_data]
    
    # Track consecutive failures for adaptive delay
    consecutive_failures = 0
    base_delay = 1.0
    
    for i, film in enumerate(enriched_data):
        if film['wiki_link']:
            print(f"Processing film {i+1}/{len(enriched_data)}: {film['title']}")
            
            # Adaptive delay based on consecutive failures
            current_delay = base_delay
            if consecutive_failures > 0:
                # Increase delay if we've had failures (up to 10 seconds)
                current_delay = min(base_delay * (2 ** consecutive_failures), 10.0)
            
            # Add randomization to delay (±30%)
            jitter = current_delay * 0.3 * (random.random() * 2 - 1)
            actual_delay = max(0.5, current_delay + jitter)
            
            print(f"Waiting {actual_delay:.2f} seconds before next request...")
            time.sleep(actual_delay)
            
            # Try to get details
            details = get_film_details(film['wiki_link'])
            
            # Track failures/successes to adjust delay dynamically
            if details['director'] == "Unknown" and details['country'] == "Unknown":
                consecutive_failures += 1
                print(f"Extraction failed. Consecutive failures: {consecutive_failures}")
            else:
                # Reset counter after a successful extraction
                if consecutive_failures > 0:
                    consecutive_failures = max(0, consecutive_failures - 1)
            
            film['director'] = details['director']
            film['country'] = details['country']
    
    return enriched_data

def create_database(films_data: List[Dict[str, Any]]) -> None:
    """Store film data in SQLite database"""
    print("Creating SQLite database...")
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS films (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        release_year INTEGER,
        director TEXT,
        box_office REAL,
        country TEXT
    )
    ''')
    
    # Clear existing data
    cursor.execute("DELETE FROM films")
    
    # Insert data
    for film in films_data:
        cursor.execute('''
        INSERT INTO films (title, release_year, director, box_office, country)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            film['title'],
            film['release_year'],
            film['director'],
            film['box_office'],
            film['country']
        ))
    
    conn.commit()
    
    # Verify data was inserted
    cursor.execute("SELECT COUNT(*) FROM films")
    count = cursor.fetchone()[0]
    print(f"Inserted {count} records into the database")
    
    conn.close()

def export_to_json() -> None:
    """Export database data to JSON file"""
    print("Exporting data to JSON...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM films")
    rows = cursor.fetchall()
    
    films_json = []
    for row in rows:
        film_dict = {}
        for key in row.keys():
            film_dict[key] = row[key]
        films_json.append(film_dict)
    
    conn.close()
    
    with open(JSON_PATH, 'w') as json_file:
        json.dump(films_json, json_file, indent=4)
    
    print(f"Exported {len(films_json)} films to JSON file: {JSON_PATH}")

def main() -> None:
    """Main execution function"""
    try:
        # Step 1: Fetch and parse Wikipedia data
        html_content = fetch_wikipedia_page(URL)
        films_data = parse_html_content(html_content)
        
        if not films_data:
            print("No film data extracted. Exiting.")
            return
        
        # Step 2: Enrich with director and country info
        try:
            enriched_data = enrich_film_data(films_data)
        except Exception as e:
            print(f"Error during enrichment: {e}")
            print("Proceeding with basic film data")
            enriched_data = films_data
        
        # Step 3: Store in database
        try:
            create_database(enriched_data)
        except Exception as e:
            print(f"Error creating database: {e}")
            print("Proceeding with JSON export only")
        
        # Step 4: Export to JSON
        export_to_json()
        
        print(f"Data extraction completed. Processed {len(enriched_data)} films.")
        
    except Exception as e:
        print(f"Error during data extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()