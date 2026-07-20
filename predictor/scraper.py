from curl_cffi import requests
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

def get_forex_factory_data():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        logger.info(f"Fetching calendar data from {url}...")
        
        # Using curl_cffi to bypass Cloudflare
        resp = requests.get(url, impersonate="chrome110", timeout=30)
        
        try:
            events_data = resp.json()
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            return None

        extracted_events = []

        for event in events_data:
            title = event.get('title')
            country = event.get('country')
            impact = event.get('impact')
            forecast = event.get('forecast', '')
            previous = event.get('previous', '')
            date_str = event.get('date', '')
            
            timestamp = 0
            utc_string = "N/A"
            
            if date_str:
                try:
                    # ISO string to UTC timestamp
                    dt_obj = datetime.fromisoformat(date_str)
                    dt_obj_utc = dt_obj.astimezone(timezone.utc)
                    timestamp = int(dt_obj_utc.timestamp())
                    utc_string = dt_obj_utc.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass

            extracted_events.append({
                "title": title,
                "country": country,
                "currency": country,  # currency is usually same as country code in FF
                "impact": impact,
                "forecast": forecast,
                "previous": previous,
                "actual": "",
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
