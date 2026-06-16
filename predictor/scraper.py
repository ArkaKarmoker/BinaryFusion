from curl_cffi import requests
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

def get_forex_factory_data():
    try:
        url = "https://www.forexfactory.com/calendar"
        logger.info(f"Navigating to {url}...")
        
        # Using curl_cffi to bypass Cloudflare
        resp = requests.get(url, impersonate="chrome110", timeout=30)
        
        text = resp.text
        start_idx = text.find('days: [')
        if start_idx == -1:
            logger.error("Error: Could not find 'days: [' in HTML.")
            return None
            
        start_idx += 6 # points to '['
        bracket_count = 0
        end_idx = -1
        for i in range(start_idx, len(text)):
            if text[i] == '[':
                bracket_count += 1
            elif text[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx == -1:
            logger.error("Error: Could not find matching closing bracket.")
            return None
            
        days_json = text[start_idx:end_idx]
        try:
            days_data = json.loads(days_json)
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            return None

        extracted_events = []

        for day in days_data:
            for event in day.get('events', []):
                        
                        timestamp = event.get('dateline')
                        utc_string = "N/A"
                        
                        if timestamp:
                            # Convert Unix timestamp to UTC object
                            dt_object = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                            utc_string = dt_object.strftime('%Y-%m-%d %H:%M:%S')

                        # Logic: If 'revision' exists, the website displays 'revision'.
                        # Otherwise, it displays the original 'previous'.
                        raw_previous = event.get('previous', '')
                        raw_revision = event.get('revision', '')
                        display_previous = raw_revision if raw_revision else raw_previous

                        extracted_events.append({
                            "title": event.get('name'),
                            "country": event.get('country'),
                            "currency": event.get('currency'),
                            "impact": event.get('impactTitle'),
                            "forecast": event.get('forecast', ''),
                            "previous": display_previous,
                            "actual": event.get('actual', ''),
                            "utc_timestamp": timestamp,
                            "utc_datetime": utc_string
                        })

        last_fetch_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        return {
            "count": len(extracted_events),
            "timezone_info": "All times are in UTC",
            "last_updated": last_fetch_time,
            "events": extracted_events
        }

    except Exception as e:
        logger.error(f"Scraper Error: {str(e)}")
        return None
