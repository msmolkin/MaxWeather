"""
Weather Report Scraper for Kalshi Betting

This script scrapes weather reports for New York City, Miami, Austin, and Chicago
from the National Weather Service website. It's designed to provide comprehensive
historical weather data to inform betting strategies on prediction markets like Kalshi.

The script fetches multiple versions of daily climate reports for each city, allowing
for analysis of weather patterns and trends. This data can be particularly useful for
making informed decisions on weather-related contracts on Kalshi or similar platforms.

Cities covered:
- New York City, NY
- Miami, FL
- Austin, TX
- Chicago, IL

Note: This tool is intended for informational purposes only. Please use responsibly
and in accordance with all applicable laws and platform policies.

Author: Michael Smolkin
Date: 2024-07-16
"""

import requests
from bs4 import BeautifulSoup
import pyperclip
import concurrent.futures
import time
import logging
import os
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_weather_report(version, weather_site, national_weather_service_issuing_office):
    url = f"https://forecast.weather.gov/product.php?site=OKX&issuedby=NYC&product=CLI&format=TXT&version={version}&glossary=0"
    tries = 3
    for attempt in range(tries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            pre_tag = soup.find('pre', class_='glossaryProduct')
            if pre_tag:
                return pre_tag.text.strip()
            else:
                logging.warning(f"No data found for version {version}")
                return None
        except requests.RequestException as e:
            if attempt < tries - 1:
                logging.warning(f"Attempt {attempt + 1} failed for version {version}: {str(e)}. Retrying...")
                time.sleep(2)
            else:
                logging.error(f"Failed to fetch data for version {version} after {tries} attempts: {str(e)}")
                return None

def get_total_versions():
    url = "https://forecast.weather.gov/product.php?site=OKX&issuedby=NYC&product=CLI&format=TXT&version=1&glossary=0"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all divs
        divs = soup.find_all('div')
        
        # Look for the div that contains "Versions:" text
        for div in divs:
            if 'Versions:' in div.text:
                # Find all links within this div
                links = div.find_all('a')
                if links:
                    # Get the text of the last link, which should be the highest version number
                    last_version = int(links[-1].text)
                    return last_version
        
        logging.error("Could not find version information")
        return 0
    except requests.RequestException as e:
        logging.error(f"Failed to fetch total versions: {str(e)}")
        return 0
    except ValueError as e:
        logging.error(f"Failed to parse version number: {str(e)}")
        return 0

def get_optimal_worker_count():
    cpu_count = os.cpu_count()
    
    if cpu_count is None:
        return 5
    
    # For I/O bound tasks, we can use more workers than CPU cores
    # A common formula is to use 5x the number of CPU cores
    worker_count = min(cpu_count * 5, 32)  # cap at 32 to avoid potential rate limiting
    
    return worker_count
    
def fetch_reports(versions):
    """ Fetch weather reports for a list of versions using ThreadPoolExecutor 
    Args:
        versions (list): List of version numbers to fetch reports for
    Returns:
        dict: Dictionary containing version numbers as keys and weather reports as values
        
    """
    
    max_workers = get_optimal_worker_count()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_version = {executor.submit(get_weather_report, version): version for version in versions}
        results = {}
        for future in tqdm(concurrent.futures.as_completed(future_to_version), total=len(versions), desc="Fetching reports"):
            version = future_to_version[future]
            try:
                data = future.result()
                if data:
                    results[version] = data
            except Exception as exc:
                logging.error(f"Version {version} generated an exception: {exc}")
    return results

def main():
    start_time = time.time()
    
    total_versions = get_total_versions()
    if total_versions == 0:
        logging.error("Failed to determine the number of versions. Exiting.")
        return

    logging.info(f"Total versions: {total_versions}")

    all_reports = fetch_reports(range(1, total_versions + 1))

    # Sort reports by version number
    sorted_reports = [f"<version_{v}>\n{all_reports[v]}\n</version_{v}>" for v in sorted(all_reports.keys())]

    # Save to file
    with open("weather_reports_OKX_NYC.txt", "w") as f:
        f.write("\n\n".join(sorted_reports))

    # Save to clipboard
    clipboard_content = "<clip>\n\n" + "\n\n".join(sorted_reports) + "\n\n</clip>"
    pyperclip.copy(clipboard_content)

    logging.info(f"All reports have been saved to 'weather_reports.txt' and copied to the clipboard.")
    logging.debug(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
