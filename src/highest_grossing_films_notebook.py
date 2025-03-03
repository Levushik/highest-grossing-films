#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Highest-Grossing Films Data Analysis Notebook

This notebook-style script extracts data from the Wikipedia page on Highest-Grossing Films,
cleans the data, stores it in a SQLite database, and exports it to JSON
for use in a web application.
"""

# %% [markdown]
# # Highest-Grossing Films Data Extraction
# 
# This notebook extracts and processes data about the highest-grossing films from Wikipedia.
# 
# It performs the following steps:
# 1. Fetching data from Wikipedia
# 2. Parsing and cleaning the data
# 3. Enriching the data with additional information
# 4. Storing the data in a SQLite database
# 5. Exporting the data to JSON

# %% [markdown]
# ## 1. Setup and Imports
# 
# First, let's import all the necessary libraries.

# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import json
import sqlite3
import os
import time
from typing import Dict, List, Any, Optional, Union

# Constants
URL = "https://en.wikipedia.org/wiki/List_of_highest-grossing_films"
DB_PATH = "data/highest_grossing_films.db"
JSON_PATH = "data/films.json"

# %% [markdown]
# ## 2. Data Fetching Functions
# 
# These functions are responsible for fetching data from Wikipedia.

# %%
def fetch_wikipedia_page(url: str) -> str:
    """
    Fetch the HTML content of a Wikipedia page.
    
    Args:
        url: URL of the Wikipedia page
        
    Returns:
        HTML content of the page
    
    Raises:
        Exception: If the page cannot be fetched
    """
    print(f"Fetching page: {url}")
    
    # Set a user agent to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("Successfully fetched the page")
            return response.text
        else:
            raise Exception(f"Failed to fetch the page. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error when fetching the page: {e}")

# %% [markdown]
# ## 3. Data Parsing Functions
# 
# These functions are responsible for parsing the HTML content and extracting film data.

# %%
def parse_html_content(html_content: str) -> List[Dict[str, Any]]:
    """
    Parse the HTML content and extract film data.
    
    Args:
        html_content: HTML content of the Wikipedia page
        
    Returns:
        List of dictionaries containing film data
    """
    print("Parsing HTML content...")
    
    # Try to use lxml parser for better HTML handling, fall back to html.parser if not available
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        print("Using lxml parser")
    except Exception as e:
        print(f"Could not use lxml parser: {e}. Falling back to html.parser")
        soup = BeautifulSoup(html_content, 'html.parser')
    
    # Save a copy of the HTML for debugging purposes
    try:
        os.makedirs('data', exist_ok=True)
        with open('data/debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Saved HTML content to data/debug_page.html for debugging")
    except Exception as e:
        print(f"Could not save debug HTML: {e}")
    
    # Try different approaches to find the table with highest-grossing films
    tables = soup.find_all('table', class_='wikitable')
    print(f"Found {len(tables)} tables with class 'wikitable'")
    
    if len(tables) == 0:
        # If no tables with class 'wikitable', try to find any table
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables in total")
        if len(tables) == 0:
            raise Exception("No tables found on the page")
    
    # Look for the table with the highest-grossing films
    # This is typically a table with 'Box office' or 'Worldwide gross' in the headers
    highest_grossing_table = None
    for i, table in enumerate(tables):
        headers = [header.text.strip() for header in table.find_all('th')]
        print(f"Table {i+1} headers: {headers}")
        
        # Check if this looks like the table we want
        if any('box office' in header.lower() for header in headers) or \
           any('worldwide gross' in header.lower() for header in headers) or \
           any('rank' in header.lower() and 'title' in ' '.join(headers).lower() for header in headers):
            highest_grossing_table = table
            print(f"Selected table {i+1} as it contains relevant headers")
            break
    
    # If we still haven't found a suitable table, use the first one with a reasonable number of columns
    if highest_grossing_table is None and len(tables) > 0:
        # Find the table with the most columns, which is likely to be our data table
        max_columns = 0
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if rows:
                cells = rows[0].find_all(['th', 'td'])
                if len(cells) > max_columns:
                    max_columns = len(cells)
                    highest_grossing_table = table
                    print(f"Selected table {i+1} as it has the most columns ({max_columns})")
    
    if highest_grossing_table is None:
        raise Exception("Could not identify the table with highest-grossing films")
    
    # Extract the rows
    rows = highest_grossing_table.find_all('tr')
    if len(rows) <= 1:
        raise Exception("Selected table has insufficient rows")
    
    # Extract the header to determine column indices
    header_row = rows[0]
    headers = [header.text.strip().lower() for header in header_row.find_all(['th'])]
    print(f"Table headers: {headers}")
    
    # Find indices for the relevant columns
    title_idx = next((i for i, h in enumerate(headers) if 'title' in h or 'film' in h), None)
    revenue_idx = next((i for i, h in enumerate(headers) if 'box office' in h or 'worldwide gross' in h or 'gross' in h), None)
    year_idx = next((i for i, h in enumerate(headers) if 'year' in h or 'release' in h), None)
    
    # If we couldn't find exact column matches, make a best guess
    if title_idx is None:
        # The title column is typically the first or second column
        title_idx = 1 if len(headers) > 1 else 0
        print(f"Could not find title column, using index {title_idx}")
    
    if revenue_idx is None:
        # The revenue column is typically towards the end
        revenue_idx = len(headers) - 1 if len(headers) > 2 else 2
        print(f"Could not find revenue column, using index {revenue_idx}")
    
    print(f"Using title column index: {title_idx}, revenue column index: {revenue_idx}")
    
    # Skip the header row and extract data
    films_data = []
    print("Extracting film data...")
    
    for row in rows[1:]:  # Skip the header row
        cells = row.find_all(['td', 'th'])
        if len(cells) >= max(title_idx + 1, revenue_idx + 1):  # Ensure we have enough cells
            # Extract data from cells
            film_info = {}
            
            # Extract film title
            title_cell = cells[title_idx]
            title = title_cell.get_text().strip()
            film_info['title'] = title
            
            # Extract release year from title
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                film_info['release_year'] = int(year_match.group(1))
                # Clean title by removing the year
                film_info['title'] = re.sub(r'\s*\(\d{4}\)', '', title).strip()
            elif year_idx is not None and len(cells) > year_idx:
                # Try to get the year from the dedicated year column
                year_text = cells[year_idx].get_text().strip()
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    film_info['release_year'] = int(year_match.group(1))
                else:
                    film_info['release_year'] = None
            else:
                film_info['release_year'] = None
            
            # Extract box office revenue
            box_office_cell = cells[revenue_idx]
            box_office_text = box_office_cell.get_text().strip()
            # Remove non-numeric characters except for decimal points
            box_office_value = re.sub(r'[^\d.]', '', box_office_text)
            try:
                film_info['box_office'] = float(box_office_value) if box_office_value else None
            except ValueError:
                film_info['box_office'] = None
            
            # Extract link to film's Wikipedia page for further details
            film_link = None
            link = title_cell.find('a')
            if link and 'href' in link.attrs:
                href = link['href']
                # Handle different types of URLs
                if href.startswith('/wiki/'):
                    film_link = href
                elif href.startswith('https://en.wikipedia.org/'):
                    film_link = href
                else:
                    print(f"Skipping unexpected link format: {href}")
            
            film_info['wiki_link'] = film_link
            print(f"Found film: {film_info['title']}, link: {film_link}")
            
            # Set placeholders for director and country
            film_info['director'] = "Unknown"
            film_info['country'] = "Unknown"
            
            films_data.append(film_info)
    
    print(f"Extracted data for {len(films_data)} films")
    
    if not films_data:
        raise Exception("No film data could be extracted from the table")
        
    return films_data

# %% [markdown]
# ## 4. Data Enrichment Functions
# 
# These functions fetch additional details about each film from their individual Wikipedia pages.

# %%
def get_film_details(film_url: str) -> Dict[str, str]:
    """
    Extract director and country information from a film's Wikipedia page.
    
    Args:
        film_url: URL of the film's Wikipedia page
        
    Returns:
        Dictionary containing director and country information
    """
    details = {"director": "Unknown", "country": "Unknown"}
    
    try:
        # Set a user agent to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Construct the full URL, handling both relative and absolute URLs
        full_url = film_url
        if film_url.startswith('/wiki/'):
            full_url = f"https://en.wikipedia.org{film_url}"
        
        print(f"Fetching details from: {full_url}")
        
        response = requests.get(full_url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for {full_url}")
            return details
        
        # Try to use lxml parser for better HTML handling, fall back to html.parser if not available
        try:
            soup = BeautifulSoup(response.text, 'lxml')
        except Exception:
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the infobox
        info_box = soup.find('table', class_='infobox')
        
        if info_box:
            # Extract director
            director_found = False
            
            # Method 1: Find by row header text
            director_row = info_box.find(lambda tag: tag.name == 'th' and 'Directed by' in tag.text)
            if director_row and director_row.find_next('td'):
                details["director"] = director_row.find_next('td').text.strip()
                director_found = True
                print(f"Found director using method 1: {details['director']}")
            
            # Method 2: Look for specific formatting in the infobox
            if not director_found:
                director_links = info_box.find_all(lambda tag: tag.name == 'a' and tag.get('href', '').startswith('/wiki/') and 'director' in tag.get('href', '').lower())
                if director_links:
                    directors = [link.text.strip() for link in director_links if link.text.strip()]
                    if directors:
                        details["director"] = ', '.join(directors)
                        director_found = True
                        print(f"Found director using method 2: {details['director']}")
            
            # Method 3: Look directly in page content if not found in infobox
            if not director_found:
                director_section = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'director' in tag.text.lower())
                if director_section:
                    next_para = director_section.find_next('p')
                    if next_para:
                        details["director"] = next_para.text.strip()
                        print(f"Found director using method 3: {details['director']}")
            
            # Extract country
            country_found = False
            
            # Method 1: Find by row header text
            country_row = info_box.find(lambda tag: tag.name == 'th' and ('Country' in tag.text or 'Countries' in tag.text))
            if country_row and country_row.find_next('td'):
                details["country"] = country_row.find_next('td').text.strip()
                country_found = True
                print(f"Found country using method 1: {details['country']}")
            
            # Method 2: Look for country links in the infobox
            if not country_found:
                country_links = info_box.find_all(lambda tag: tag.name == 'a' and tag.get('href', '').startswith('/wiki/') and ('country' in tag.get('href', '').lower() or tag.get('href', '').lower().endswith('_film)') or tag.get('href', '').lower().endswith('_cinema)')))
                if country_links:
                    countries = [link.text.strip() for link in country_links if link.text.strip() and not 'film' in link.text.lower()]
                    if countries:
                        details["country"] = ', '.join(countries)
                        print(f"Found country using method 2: {details['country']}")
        else:
            print(f"No infobox found for {full_url}")
        
        # Clean up the extracted text
        for key in details:
            if details[key] != "Unknown":
                # Remove citations and references
                details[key] = re.sub(r'\[\d+\]', '', details[key])
                # Remove extra whitespace
                details[key] = re.sub(r'\s+', ' ', details[key]).strip()
    
    except Exception as e:
        print(f"Error fetching details for {film_url}: {e}")
    
    return details

# %%
def enrich_film_data(films_data: List[Dict[str, Any]], max_films: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Enrich film data with director and country information.
    
    Args:
        films_data: List of film data dictionaries
        max_films: Maximum number of films to enrich (for testing purposes)
        
    Returns:
        Enriched film data
    """
    print("Enriching film data with directors and countries...")
    
    # Limit the number of films if specified
    films_to_enrich = films_data if max_films is None else films_data[:max_films]
    
    enriched_count = 0
    for i, film in enumerate(films_to_enrich):
        if film['wiki_link']:
            print(f"Fetching details for film {i+1}/{len(films_to_enrich)}: {film['title']}")
            details = get_film_details(film['wiki_link'])
            film['director'] = details['director']
            film['country'] = details['country']
            
            if details['director'] != "Unknown" or details['country'] != "Unknown":
                enriched_count += 1
            
            # Add a small delay to be respectful to Wikipedia's servers
            time.sleep(0.5)
        else:
            print(f"No Wikipedia link available for {film['title']}")
    
    print(f"Successfully enriched {enriched_count} out of {len(films_to_enrich)} films")
    return films_data

# %% [markdown]
# ## 5. Database Functions
# 
# These functions handle the creation of the SQLite database and storing the data.

# %%
def create_database(films_data: List[Dict[str, Any]]) -> None:
    """
    Create a SQLite database and store the film data.
    
    Args:
        films_data: List of film data dictionaries
    """
    print("Creating SQLite database...")
    
    # Create a directory for the database if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the films table
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
    
    # Clear existing data if any
    cursor.execute("DELETE FROM films")
    
    # Insert data into the database
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
    
    # Commit the changes
    conn.commit()
    
    # Verify the data was inserted
    cursor.execute("SELECT COUNT(*) FROM films")
    count = cursor.fetchone()[0]
    print(f"Number of films in the database: {count}")
    
    # Close the connection
    conn.close()

# %% [markdown]
# ## 6. Data Export Functions
# 
# These functions export the data from the database to a JSON file.

# %%
def export_to_json() -> None:
    """
    Export data from the SQLite database to a JSON file.
    """
    print("Exporting data to JSON...")
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Query all data from the database
    cursor.execute("SELECT * FROM films")
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    films_json = []
    for row in rows:
        film_dict = {}
        for key in row.keys():
            film_dict[key] = row[key]
        films_json.append(film_dict)
    
    # Close the connection
    conn.close()
    
    # Save to JSON file
    with open(JSON_PATH, 'w') as json_file:
        json.dump(films_json, json_file, indent=4)
    
    print(f"Exported {len(films_json)} films to JSON file: {JSON_PATH}")

# %% [markdown]
# ## 7. Main Execution
# 
# This is the main workflow that ties everything together.

# %%
def main() -> None:
    """
    Main function to execute the data extraction workflow.
    """
    try:
        # Step 1: Fetch Wikipedia page
        html_content = fetch_wikipedia_page(URL)
        
        # Step 2: Extract and parse data
        films_data = parse_html_content(html_content)
        
        if not films_data:
            print("No film data was extracted. Exiting.")
            return
        
        print(f"Successfully extracted data for {len(films_data)} films")
        print("Sample of extracted data:")
        for i, film in enumerate(films_data[:3]):  # Show first 3 films
            print(f"  {i+1}. {film['title']} - Box Office: {film['box_office']}")
        
        # Step 3: Enrich data with director and country information
        print("\nEnriching film data with additional details...")
        
        # For demonstration/testing purposes, limit to a smaller number of films
        # Set max_films to None for production use to process all films
        max_films = 25
        
        try:
            enriched_data = enrich_film_data(films_data, max_films=max_films)
            
            # Check if enrichment was successful
            enriched_count = sum(1 for film in enriched_data[:max_films] 
                               if film.get('director') != "Unknown" or film.get('country') != "Unknown")
            
            if enriched_count == 0 and max_films > 0:
                print("Warning: No films were successfully enriched. There might be an issue with the Wikipedia API or parsing.")
                print("You may need to check the network connection or update the parsing logic.")
            
        except Exception as e:
            print(f"Error during data enrichment: {e}")
            print("Proceeding with basic film data without enrichment")
            enriched_data = films_data
        
        # Step 4: Create SQLite database and store data
        try:
            create_database(enriched_data)
        except Exception as e:
            print(f"Error creating database: {e}")
            print("Will proceed with JSON export only")
        
        # Step 5: Export data to JSON
        try:
            # Create a simplified version of the data for JSON export
            simplified_data = []
            for film in enriched_data:
                simplified_film = {
                    'title': film['title'],
                    'release_year': film['release_year'],
                    'director': film['director'],
                    'box_office': film['box_office'],
                    'country': film['country']
                }
                simplified_data.append(simplified_film)
            
            # Create directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Write directly to JSON file
            with open(JSON_PATH, 'w') as json_file:
                json.dump(simplified_data, json_file, indent=4)
            
            print(f"Successfully exported {len(simplified_data)} films to JSON file: {JSON_PATH}")
            
            # Print enrichment statistics
            unknown_directors = sum(1 for film in simplified_data if film['director'] == "Unknown")
            unknown_countries = sum(1 for film in simplified_data if film['country'] == "Unknown")
            
            print(f"Films with unknown directors: {unknown_directors}/{len(simplified_data)} ({unknown_directors/len(simplified_data):.1%})")
            print(f"Films with unknown countries: {unknown_countries}/{len(simplified_data)} ({unknown_countries/len(simplified_data):.1%})")
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
        
        print("Data extraction completed!")
        
    except Exception as e:
        print(f"An error occurred during data extraction: {e}")
        import traceback
        traceback.print_exc()

# %% [markdown]
# ## 8. Execution Entry Point
# 
# Run the main function if this script is executed directly.

# %%
if __name__ == "__main__":
    main() 