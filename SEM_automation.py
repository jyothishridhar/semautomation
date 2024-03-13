import streamlit as st
import pandas as pd
import os
import base64
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from itertools import permutations
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options

def generate_variants(property_name, max_variants=5):
    # Split the property name into words
    words = property_name.split()

    # Generate permutations of words
    word_permutations = permutations(words)

    # Join permutations to form variant names
    variants = [' '.join(perm) for i, perm in enumerate(word_permutations) if i < max_variants]

    return variants

# Define function to scrape the first proper paragraph
def scrape_first_proper_paragraph(url):
    try:
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad requests
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all <p> tags
        p_tags = soup.find_all('p')
        
        # Find the first proper paragraph
        first_proper_paragraph = None
        for p in p_tags:
            paragraph = p.text.strip()
            if len(paragraph) > 200:  # Adjust the length threshold as needed
                first_proper_paragraph = paragraph
                break
        
        # Split the first paragraph into two sentences
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', first_proper_paragraph)
        ad_copy1 = sentences[0] if len(sentences) >= 1 else ''
        ad_copy2 = sentences[1] if len(sentences) >= 2 else ''
        
        return ad_copy1, ad_copy2
        
    except Exception as e:
        print("An error occurred:", e)
        return None, None

# Define function to scrape the first header
def scrape_first_header(url):
    try:
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad requests

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first header tag (h1, h2, h3, etc.)
        first_header = soup.find(['h1','h2'])

        # Check if any header tag was found
        if first_header:
            return first_header.text.strip()
        else:
            return "No header tag found on the page."

    except Exception as e:
        print("An error occurred while scraping the webpage:", e)
        return None

# Define function to scrape site links
def scrape_site_links(url, max_links=8):
    try:
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad requests

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor (a) tags
        anchor_tags = soup.find_all('a')

        # Set to store unique URLs
        unique_urls = set()

        # List to store the found site links
        site_links = []

        # Define patterns to match variations in link text
        link_text_patterns = [
            "Official\s?Site",
            "Rooms\s?&\s?Suites",
            "WEDDING",
            "Facilities\s?&\s?Activities",
            "Sports\s?&\s?Entertainment",
            "Water\s?Park",
            "Swimming\s?pool",
            "Specials",
            "Activities",
            "Groups\s?&\s?Meetings",
            "Dining",
            "Meetings\s?&\s?Events",
            "Contact\s?Us",
            "ACCOMMODATION",
            "Photos",
            "Events",
            "Pool & sea",
            "Wellness & fitness"
        ]

        # Compile regex pattern
        link_text_pattern = re.compile('|'.join(link_text_patterns), re.IGNORECASE)

        # Loop through all anchor tags and extract links with specific text
        for a in anchor_tags:
            # Get the text of the anchor tag, stripped of leading and trailing whitespace
            link_text = a.get_text(strip=True)

            # Check if the link text matches any of the desired site links
            if link_text_pattern.search(link_text):
                # Extract the href attribute to get the link URL
                link_url = a.get('href')

                # Complete relative URLs if necessary
                link_url = urljoin(url, link_url)

                # Add the URL to the set of unique URLs
                if link_url not in unique_urls:
                    unique_urls.add(link_url)
                    # Append the link text and URL to the site_links list
                    site_links.append((link_text, link_url))

                    # Break the loop if the maximum number of links is reached
                    if len(site_links) >= max_links:
                        break

        return site_links

    except Exception as e:
        print("An error occurred while scraping the site links:", e)
        return None

def scrape_similar_hotels(google_url, first_header):
    try:
        print("Fetching similar hotels...")
        # Set up the Selenium webdriver
        # from selenium import webdriver

        # from selenium.webdriver.chrome.service import Service as ChromeService

        # from webdriver_manager.chrome import ChromeDriverManager

        # driver=webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()

        driver = webdriver.Chrome()

        # # Navigate to the URL
        driver.get(google_url)

        time.sleep(2)

        # Find the search box element by XPath
        search_box = driver.find_element(By.XPATH, "//textarea[@id='APjFqb' and @name='q']")

        # Type the search query
        search_box.send_keys(first_header)

        # Press Enter to perform the search
        search_box.send_keys(Keys.RETURN)

        # Wait for a few seconds to let the search results load
        time.sleep(5)

        # Find elements matching the XPath for the search results
        search_results = driver.find_elements(By.XPATH, "//div[@class='hrZZ8d']")

        negative_keywords = []
        for result in search_results:
            negative_keywords.append(result.text)

        # Close the browser
        driver.quit()

        print("Negative Keywords:", negative_keywords)
        return negative_keywords
    
    except Exception as e:
        print("An error occurred while scraping similar hotels:", e)
        return None


# Streamlit app code
st.title("Web Scraping Demo")

# Input URL field
url = st.text_input("Enter URL")

if st.button("Scrape Data"):
    if url:
        ad_copy1, ad_copy2 = scrape_first_proper_paragraph(url)
        first_header = scrape_first_header(url)  # Get the first header here
        site_links = scrape_site_links(url)

        # Generate property name variants
        property_name_variants = generate_variants(first_header)

        # Scraping similar hotels
        negative_keywords = scrape_similar_hotels("https://www.google.com", first_header)


        # Creating DataFrames for each piece of data
        header_df = pd.DataFrame({'Header Text': [first_header]})
        paragraph_df = pd.DataFrame({'Ad copy1': [ad_copy1], 'Ad copy2': [ad_copy2]})
        site_links_df = pd.DataFrame(site_links, columns=['Link Text', 'Link URL'])
        property_url = pd.DataFrame({'property_url': [url]})
        property_name_variants_df = pd.DataFrame({'Variants of Property Name': property_name_variants})
        negative_keywords_df = pd.DataFrame(negative_keywords, columns=['Negative Keywords'])
        callouts_df = pd.DataFrame({'Callouts': ["Book Direct", "Great Location", "Spacious Suites"]})
        # Concatenating DataFrames horizontally
        df = pd.concat([header_df, paragraph_df, site_links_df, property_url, property_name_variants_df, negative_keywords_df,callouts_df], axis=1)

        # Define the directory path
        output_directory = 'C://SEM creation//SEM_Automation//'

        # Create the directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        # Define the output file path
        output_file = os.path.join(output_directory, 'scraped_data_yaktsa.tiara-hotels.xlsx')

        # Writing to Excel
        df.to_excel(output_file, index=False)

        st.success(f"Data has been saved to {output_file}")

        # Display the DataFrame
        st.dataframe(df)

    else:
        st.warning("Please enter a URL.")
