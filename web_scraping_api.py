from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

app = Flask(__name__)
CORS(app)

chrome_binary_path = "/opt/render/project/.render/chrome/opt/google/chrome/chrome"

# Function to set up a Chrome driver
def setup_driver():
    options = Options()
    options.headless = True
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.binary_location = chrome_binary_path
    driver = webdriver.Chrome(options=options)
    return driver

# Function to safely extract text from an element
def extract_text(element):
    return element.text.strip() if element else "N/A"

# Function to safely extract an attribute from an element
def extract_attribute(element, attribute):
    return element.get(attribute) if element else None

# Function to get the top-most hackathon name and logo
def get_top_hackathon_name_and_logo(url, link):
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(2)  # Add a delay to ensure page loads properly

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        # Extract the top-most hackathon name and logo
        top_hackathon = soup.find('div', class_='single_profile')
        hackathon_info = {}

        hackathon_info['name'] = extract_text(top_hackathon.find('h2'))
        hackathon_info['logo_url'] = extract_attribute(top_hackathon.find('div', class_='img').find('img'), 'src')
        hackathon_info['link'] = link

        return hackathon_info

    finally:
        driver.quit()

# Function to scrape competition names and redirection links
def scrape_competitions_list(url, num_competitions):
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(2)  # Add a delay to ensure page loads properly

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        competition_list = []

        # Find all competition listings
        competition_links = soup.find_all('a', class_='Link__LinkBase-sc-af40de1d-0 lkflLS')

        processed_competitions = set()

        for link in competition_links:
            competition_name = link.find('h3').text
            competition_link = link['href']

            if competition_name not in processed_competitions:
                try:
                    logo_url = get_competition_logo(competition_link)
                    competition_list.append({'name': competition_name, 'link': competition_link, 'logo_url': logo_url})
                    processed_competitions.add(competition_name)

                    if len(competition_list) >= num_competitions:
                        break

                except Exception as e:
                    print(f"Error getting logo for {competition_link}: {e}")

        return competition_list

    finally:
        driver.quit()

# Function to get the competition logo from the redirected page
def get_competition_logo(competition_link):
    driver = setup_driver()
    try:
        driver.get(competition_link)
        time.sleep(2)  # Add a delay to ensure page loads properly

        page_html = driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')

        # Extract logo URL from the redirected page
        logo_img = soup.find('img', src=True)
        logo_url = urljoin(competition_link, extract_attribute(logo_img, 'src'))
        return logo_url

    except Exception as e:
        print(f"Error getting logo for {competition_link}: {e}")
        return None

    finally:
        driver.quit()

# Define a single API endpoint for combined data
@app.route('/api/data', methods=['GET'])
def get_data():
    current_link = 'https://unstop.com/hackathons?oppstatus=recent'
    devfolio_link = 'https://devfolio.co/hackathons'
    num_competitions = 6

    # Get the top-most hackathon data
    # top_hackathon_info = get_top_hackathon_name_and_logo(current_link, link=current_link)

    # Scrape competition data
    competition_data = scrape_competitions_list(devfolio_link, num_competitions)

    # Add the top hackathon info to competition data
    # competition_data.insert(0, top_hackathon_info)

    # Create a list of dictionaries in the desired format
    result = [
        {
            "name": item['name'],
            "logo_url": item['logo_url'],
            "link": item['link'],
        }
        for item in competition_data
    ]

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
