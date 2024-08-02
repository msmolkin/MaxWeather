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

# TODO for later: Modify the script to download reports for all locations concurrently,
# rather than processing them sequentially. This will involve restructuring the main()
# function to use concurrent.futures.ThreadPoolExecutor for location processing,
# similar to how we're currently fetching individual reports for each location.

def get_weather_report(url, version):
    full_url = f"{url}&format=TXT&version={version}&glossary=0"
    tries = 3
    for attempt in range(tries):
        try:
            start_time = time.time()
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            download_time = time.time() - start_time
            
            soup = BeautifulSoup(response.text, 'html.parser')
            pre_tag = soup.find('pre', class_='glossaryProduct')
            if pre_tag:
                content = pre_tag.text.strip()
                return content, len(content), download_time
            else:
                logging.warning(f"No data found for version {version}")
                return None, 0, download_time
        except requests.RequestException as e:
            if attempt < tries - 1:
                logging.warning(f"Attempt {attempt + 1} failed for version {version}: {str(e)}. Retrying...")
                time.sleep(2)
            else:
                logging.error(f"Failed to fetch data for version {version} after {tries} attempts: {str(e)}")
                return None, 0, 0

def get_total_versions(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        divs = soup.find_all('div')
        
        for div in divs:
            if 'Versions:' in div.text:
                links = div.find_all('a')
                if links:
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
    
    worker_count = min(cpu_count * 5, 32)
    
    return worker_count

def fetch_reports(url, versions):
    max_workers = get_optimal_worker_count()
    logging.info(f"Using {max_workers} workers for fetching reports")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_version = {executor.submit(get_weather_report, url, version): version for version in versions}
        results = {}
        total_bytes = 0
        total_time = 0
        
        with tqdm(total=len(versions), desc="Downloading reports", unit="report") as pbar:
            for future in concurrent.futures.as_completed(future_to_version):
                version = future_to_version[future]
                try:
                    data, bytes_downloaded, download_time = future.result()
                    if data:
                        results[version] = data
                        total_bytes += bytes_downloaded
                        total_time += download_time
                        
                        pbar.update(1)
                        avg_speed = total_bytes / (1024 * total_time) if total_time > 0 else 0
                        eta = (len(versions) - len(results)) * (total_time / len(results)) if len(results) > 0 else 0
                        pbar.set_postfix({
                            "Avg Speed": f"{avg_speed:.2f} KB/s",
                            "ETA": f"{eta:.2f}s"
                        }, refresh=True)
                except Exception as exc:
                    logging.error(f"Version {version} generated an exception: {exc}")
    
    return results

def process_location(url, file_name):
    total_versions = get_total_versions(url)
    if total_versions == 0:
        logging.error(f"Failed to determine the number of versions for {url}. Skipping.")
        return

    logging.info(f"Total versions to download for {url}: {total_versions}")

    all_reports = fetch_reports(url, range(1, total_versions + 1))

    sorted_reports = [f"<version_{v}>\n{all_reports[v]}\n</version_{v}>" for v in sorted(all_reports.keys())]

    with open(file_name, "w") as f:
        f.write("\n\n".join(sorted_reports))

    logging.info(f"Reports for {url} have been saved to {file_name}")

def main():
    start_time = time.time()

    locations = [
        ("https://forecast.weather.gov/product.php?site=MFL&product=CLI&issuedby=MIA", "weather_reports_MFL_Miami.txt"),
        ("https://forecast.weather.gov/product.php?site=EWX&product=CLI&issuedby=AUS", "weather_reports_EWX_Austin.txt"),
        ("https://forecast.weather.gov/product.php?site=LOT&product=CLI&issuedby=MDW", "weather_reports_LOT_Chicago.txt"),
        ("https://forecast.weather.gov/product.php?site=OKX&issuedby=NYC&product=CLI", "weather_reports_OKX_NewYork.txt")
    ]

    for url, file_name in locations:
        process_location(url, file_name)

    logging.info(f"All locations processed. Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
