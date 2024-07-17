"""
Weather Report Scraper for Kalshi Betting

This script scrapes the latest weather report for New York City, Miami, Austin, and Chicago
from the National Weather Service website. It extracts specific information useful for
weather-related predictions and betting strategies.

Cities covered:
- New York City, NY
- Miami, FL
- Austin, TX
- Chicago, IL

Author: Michael Smolkin
Date: 2024-07-17
"""

import requests
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime, timedelta
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_weather_report(url):
    full_url = f"{url}&format=TXT&version=1&glossary=0"
    tries = 3
    for attempt in range(tries):
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            pre_tag = soup.find('pre', class_='glossaryProduct')
            if pre_tag:
                return pre_tag.text.strip()
            else:
                logging.warning("No data found in the weather report")
                return None
        except requests.RequestException as e:
            if attempt < tries - 1:
                logging.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
            else:
                logging.error(f"Failed to fetch data after {tries} attempts: {str(e)}")
                return None

def parse_weather_report(report):
    # Extract location name
    location_match = re.search(r'\.\.\.THE\s+(.+?)\s+CLIMATE\s+SUMMARY', report)
    location = location_match.group(1) if location_match else "Unknown Location"

    # Extract date
    date_match = re.search(r'FOR\s+(\w+\s+\d{1,2}\s+\d{4})', report)
    date = date_match.group(1) if date_match else None

    # Extract valid_as_of_time
    valid_time_match = re.search(r'VALID\s+.*?AS\s+OF\s+(\d{4}\s+[AP]M(?:\s+LOCAL\s+TIME)?)', report, re.IGNORECASE)
    valid_as_of_time = valid_time_match.group(1) if valid_time_match else None

    # Extract report_time
    report_time_match = re.search(r'(\d{3,4}\s+(?:A|P)M\s+\w{3}\s+\w{3}\s+\d{1,2}\s+\d{4})', report)
    report_time = report_time_match.group(1) if report_time_match else None

    # Extract maximum temperature
    max_temp_match = re.search(r'MAXIMUM\s+(\d+)\s+(\d{1,4}\s+(?:A|P)M)', report)
    max_temp = {
        "temp": int(max_temp_match.group(1)) if max_temp_match else None,
        "time": max_temp_match.group(2) if max_temp_match else None
    }

    # Standardize time format and include timezone
    timezone_match = re.search(r'\b([CE]DT|EST)\b', report)
    timezone = timezone_match.group(1) if timezone_match else "Unknown"
    
    tz_map = {"EDT": "America/New_York", "CDT": "America/Chicago", "EST": "America/New_York"}
    pytz_timezone = pytz.timezone(tz_map.get(timezone, "America/New_York"))

    def standardize_time(time_str, date_str):
        if not time_str or not date_str:
            return None
        try:
            full_datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(full_datetime_str, "%b %d %Y %I%M %p")
            return pytz_timezone.localize(dt).isoformat()
        except ValueError:
            return None

    return {
        "location": location,
        "date": date,
        "valid_as_of_time": standardize_time(valid_as_of_time, date) if valid_as_of_time else None,
        "report_time": standardize_time(report_time, date) if report_time else None,
        "max_temp": {
            "temp": max_temp["temp"],
            "time": standardize_time(max_temp["time"], date) if max_temp["time"] else None
        },
        "timezone": timezone
    }

def process_location(url):
    report = get_weather_report(url)
    if report:
        parsed_data = parse_weather_report(report)
        logging.info(f"Processed data for {parsed_data['location']}:")
        logging.info(parsed_data)
        return parsed_data
    else:
        logging.error(f"Failed to process location: {url}")
        return None

def main():
    locations = [
        "https://forecast.weather.gov/product.php?site=OKX&issuedby=NYC&product=CLI",
        "https://forecast.weather.gov/product.php?site=MFL&product=CLI&issuedby=MIA",
        "https://forecast.weather.gov/product.php?site=EWX&product=CLI&issuedby=AUS",
        "https://forecast.weather.gov/product.php?site=LOT&product=CLI&issuedby=MDW"
    ]

    for url in locations:
        process_location(url)

if __name__ == "__main__":
    main()