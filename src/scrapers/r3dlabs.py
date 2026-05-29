import requests
import csv
import datetime as dt
from utils import LoggerSetup

logger = LoggerSetup(__name__).get_logger()

def get_event_id_from_slug(slug):
    """Fetch the event ID using the provided slug."""
    api_url = f"https://api.r3dlabs.com/events/{slug}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        event_data = response.json()
        return event_data.get("id")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching event ID for slug '{slug}': {e}")
        return None

def lineup_to_csv(event_slug, output_csv):
    """Export the event lineup to a CSV file."""

    # Step 1: Get the event ID using the slug
    event_id = get_event_id_from_slug(event_slug)
    if not event_id:
        logger.error(f"Failed to retrieve event ID for slug: {event_slug}")
        return

    # Step 2: Use the event ID to fetch the lineup
    api_url = f"https://api.r3dlabs.com/train-events/{event_id}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        event_data = response.json()
        slot_list = event_data.get("slot_list", [])
        
        # Prepare CSV data columns
        csv_data = [["username", "user_country", "starttime","startday","starthour","endtime","endday","endhour"]]
        
        for slot in slot_list:
            user_channel = slot.get("user_channel", {})
            user = slot.get("user", {})
            start_date = slot.get("start_datetime", "")
            end_date = slot.get("end_datetime", "")
            if user != None:
                username = user_channel.get("display_name", "")
                country = ""
            elif slot.get("reserved", {}) == True:
                username = "RESERVED"
                country = ""
            else:
                username = ""
                country = ""

            csv_data.append([
                username,
                country,
                start_date, # Time in ISO format
                dt.datetime.fromisoformat(start_date).strftime('%m-%d'), # Month and Day of slot
                dt.datetime.fromisoformat(start_date).strftime('%H:%M'), # Hour and minute of slot
                end_date,
                dt.datetime.fromisoformat(end_date).strftime('%m-%d'), # Month and Day of slot
                dt.datetime.fromisoformat(end_date).strftime('%H:%M') # Hour and minute of slot
            ])
        
        # Write to CSV
        with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        
        logger.info(f"CSV exported successfully to {output_csv}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching event lineup: {e}")
    except Exception as e:
        logger.error(f"Error processing data: {e}")