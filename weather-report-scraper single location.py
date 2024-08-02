import requests
from bs4 import BeautifulSoup
import pyperclip
import concurrent.futures
import time
import logging
import os
from tqdm import tqdm

URL_INDEX = 0

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_url_from_location_dict(location):
        """
        Create the URL for a given location using the location dictionary.

        Args:
            location (dict): The dictionary containing the location information.

        Returns:
            str: The URL for the location's weather reports page.
        """
        url = f"https://forecast.weather.gov/product.php?site={location['site']}&issuedby={location['issuedby']}&product={location['product']}&format={location['format']}&version={location['version']}&glossary=0"
        return url

def get_weather_report(location, version):
    url = f"https://forecast.weather.gov/product.php?site={location['site']}&issuedby={location['issuedby']}&product={location['product']}&format=TXT&version={version}&glossary=0"
    tries = 3
    for attempt in range(tries):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            download_time = time.time() - start_time
            
            soup = BeautifulSoup(response.text, "html.parser")
            pre_tag = soup.find("pre", class_="glossaryProduct")
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

def get_total_versions(location_url):
    """
    Get the total number of versions available for a given location.
    
    Args:
        location_url (str): The URL of the location's weather reports page.
        
    Returns:
        int: The total number of versions available.
    """
    try:
        response = requests.get(location_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all divs
        divs = soup.find_all("div")
        
        # Look for the div that contains "Versions:" text
        for div in divs:
            if "Versions:" in div.text:
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
    
def fetch_reports(location, versions):
    max_workers = get_optimal_worker_count()
    logging.info(f"Using {max_workers} workers for fetching reports")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_version = {executor.submit(get_weather_report, location, version): version for version in versions}
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
                        
                        # Update progress bar
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

def main():
    # Create a menu of locations
    locations = {
        "New York": {"site": "OKX", "issuedby": "NYC", "product": "CLI",
                      "format": "TXT",  "version": 1,
                      "file_name": "weather_reports_OKX_NewYork.txt"},
         "Austin":   {"site": "EWX", "issuedby": "AUS", "product": "CLI",
                      "format": "TXT","version": 1, "location": "Austin",
                      "file_name": "weather_reports_EWX_Austin.txt"},
         "Chicago":  {"site": "LOT", "issuedby": "MDW", "product": "CLI",
                      "format": "TXT", "version": 1,
                      "file_name": "weather_reports_LOT_Chicago.txt"},
         "Miami":   {"site": "MFL", "issuedby": "MIA", "product": "CLI",
                     "format": "TXT", "version": 1,
                     "file_name": "weather_reports_MFL_Miami.txt"}
    }
    # Ask user to select a location
    print("Select a location:")
    for i, location in enumerate(locations, 1):
        print(f"{i}. {location}")
    
    choice = input("Enter the number corresponding to the location: ")
    try:
        choice = int(choice)
        if 1 <= choice <= len(locations):
            location = list(locations.keys())[choice - 1]
            print(f"Selected location: {location}")
            location = locations[location]
        else:
            logging.error("Invalid choice. Exiting.")
            return
    except ValueError:
        logging.error("Invalid choice. Exiting.")
        return
    
    
    start_time = time.time()
    
    total_versions = get_total_versions(create_url_from_location_dict(location))
    
    if total_versions == 0:
        logging.error("Failed to determine the number of versions. Exiting.")
        return

    logging.info(f"Total versions to download: {total_versions}")
    
    all_reports = fetch_reports(location, range(1, total_versions + 1))

    # Sort reports by version number
    sorted_reports = [f"<version_{v}>\n{all_reports[v]}\n</version_{v}>" for v in sorted(all_reports.keys())]

    # Save to file
    with open("weather_reports.txt", "w") as f:
        f.write("\n\n".join(sorted_reports))

    # Save to clipboard
    clipboard_content = "<clip>\n\n" + "\n\n".join(sorted_reports) + "\n\n</clip>"
    pyperclip.copy(clipboard_content)

    logging.info(f"All reports have been saved to 'weather_reports.txt' and copied to the clipboard.")
    logging.info(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Program exited due to keyboard interrupt.")