import requests
import csv
import datetime

# TODO: Fix whatever the fuck this is lol
# TODO: YAML Config file again

def get_event_id_from_slug(slug):
    """Fetch the event ID using the provided slug."""
    api_url = f"https://api.r3dlabs.com/events/{slug}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        event_data = response.json()
        return event_data.get("id")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching event ID for slug '{slug}': {e}")
        return None

def export_event_lineup_to_csv(event_slug, output_csv):
    """Export the event lineup to a CSV file."""
    # Step 1: Get the event ID using the slug
    event_id = get_event_id_from_slug(event_slug)
    if not event_id:
        print(f"Failed to retrieve event ID for slug: {event_slug}")
        return

    # Step 2: Use the event ID to fetch the lineup
    api_url = f"https://api.r3dlabs.com/train-events/{event_id}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        event_data = response.json()
        slot_list = event_data.get("slot_list", [])
        
        # Prepare CSV data columns
        csv_data = [["username", "user_country", "starttime","startday","starthour"]]
        
        for slot in slot_list:
            user_channel = slot.get("user_channel", {})
            user = slot.get("user", {})
            iso_time = slot.get("start_datetime", "")

            if user is not None:
                csv_data.append([
                    user_channel.get("display_name", "") if user_channel else '', # Username, with validation is there is a user there.
                    user['country'] if user["country"] else "", # User country
                    iso_time, # Time in ISO format
                    datetime.datetime.fromisoformat(iso_time).strftime('%m-%d'), # Month and Day of slot
                    datetime.datetime.fromisoformat(iso_time).strftime('%H:%M') # Hour and minute of slot
                ])
            else:
                print(f"User not found in slot data for {iso_time}")
                csv_data.append([
                    '', # Username, with validation is there is a user there.
                    '', # User country
                    iso_time, # Time in ISO format
                    datetime.datetime.fromisoformat(iso_time).strftime('%m-%d'), # Month and Day of slot
                    datetime.datetime.fromisoformat(iso_time).strftime('%H:%M') # Hour and minute of slot
                ])
        
        # Write to CSV
        with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        
        print(f"CSV exported successfully to {output_csv}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching event lineup: {e}")
    except Exception as e:
        print(f"Error processing data: {e}")

# Usage
event_slug = "sky-bass-horizon"  # Replace with your event slug
output_csv = "/event_lineup.csv"
export_event_lineup_to_csv(event_slug, output_csv)