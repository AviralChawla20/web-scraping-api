from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # Import Chrome options
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)
CORS(app)

chrome_binary_path = "/opt/render/project/.render/chrome/opt/google/chrome/chrome"


# Function to get the top-most hackathon name and logo
def get_top_hackathon_name_and_logo(url, link):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.binary_location = chrome_binary_path  # Set the path to the Chrome binary
    driver = webdriver.Chrome(options=options)  # Use Chrome driver here

    try:
        driver.get(url)
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        # Extract the top-most hackathon name and logo
        top_hackathon = soup.find('div', class_='single_profile')
        hackathon_info = {}

        if top_hackathon:
            # Extract competition name
            competition_name = top_hackathon.find('h2')
            if competition_name:
                hackathon_info['name'] = competition_name.text.strip()

            # Extract logo URL
            logo_img = top_hackathon.find('div', class_='img').find('img')
            if logo_img:
                hackathon_info['logo_url'] = logo_img['src']

            # Add the link parameter
            hackathon_info['link'] = link

        return hackathon_info

    finally:
        driver.quit()

# Function to scrape competition names and redirection links
def scrape_competitions_list(url, num_competitions):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.binary_location = chrome_binary_path  # Set the path to the Chrome binary
    driver = webdriver.Chrome(options=options)  # Use Chrome driver here

    try:
        driver.get(url)
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        competition_list = []

        # Find all competition listings
        competition_links = soup.find_all('a', class_='Link__LinkBase-sc-af40de1d-0 lkflLS')

        processed_competitions = set()  # To keep track of processed competition names

        for link in competition_links:
            competition_name = link.find('h3').text
            competition_link = link['href']

            # Skip if the competition has already been processed
            if competition_name in processed_competitions:
                continue

            try:
                # Visit the redirection link and extract the logo
                logo_url = get_competition_logo(competition_link)
            except Exception as e:
                print(f"Error getting logo for {competition_link}: {e}")
                logo_url = None  # Set logo_url to None in case of an error

            competition_list.append({'name': competition_name, 'link': competition_link, 'logo_url': logo_url})

            # Mark the competition as processed
            processed_competitions.add(competition_name)

            # Stop when we have collected the desired number of competitions
            if len(competition_list) >= num_competitions:
                break

        return competition_list

    except Exception as e:
        print(f"Error scraping competitions: {e}")
        return []  # Return an empty list in case of an error

    finally:
        driver.quit()


# Function to get the competition logo from the redirected page
def get_competition_logo(competition_link):
    options = Options()
    options.headless = True
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.binary_location = chrome_binary_path  # Set the path to the Chrome binary
    driver = webdriver.Chrome(options=options)  # Use Chrome driver here

    try:
        driver.get(competition_link)
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        # Extract logo URL from the redirected page
        logo_img = soup.find('img', src=True)
        if logo_img:
            logo_url = urljoin(competition_link, logo_img['src'])
            return logo_url

    except Exception as e:
        print(f"Error getting logo for {competition_link}: {e}")

    finally:
        driver.quit()

# Define a single API endpoint for combined data
@app.route('/api/combined_data', methods=['GET'])
def get_combined_data():
    current_link = 'https://unstop.com/hackathons?oppstatus=recent'
    devfolio_link = 'https://devfolio.co/hackathons'
    num_competitions = 4

    # Get the top-most hackathon data
    top_hackathon_info = get_top_hackathon_name_and_logo(current_link, link=current_link)

    # Scrape competition data
    competition_data = scrape_competitions_list(devfolio_link, num_competitions)

    # Add the top hackathon info to competition data
    competition_data.insert(0, top_hackathon_info)

    # Create a list of dictionaries in the desired format
    result = [
        {
            "name": item.get("name", "N/A"),  # Use "N/A" if 'name' is not present
            "logo_url": item.get("logo_url", "N/A"),  # Use "N/A" if 'logo_url' is not present
            "link": item.get("link", "N/A"),  # Use "N/A" if 'link' is not present
        }
        for item in competition_data
    ]

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
