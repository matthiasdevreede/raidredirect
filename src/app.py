import time
import pandas as pd
import datetime as dt
import requests
import os
from dotenv import load_dotenv
import os
import json
import subprocess
import logger

load_dotenv(override=True)

# TODO: Add YAML config file to remove hard coded values, replace config.json (personal preference)
# TODO: Proper logging
# TODO: Ability to reset CSV through discord
# TODO: Get CSV script easily callable every 5 minutes (if needed)
# TODO: Fix NaN values in CSV 
# TODO: 


# Access the variables
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
CLOUDFLARE_URL = os.getenv("CLOUDFLARE_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not CLOUDFLARE_API_KEY or not DISCORD_WEBHOOK_URL:
    raise ValueError("Missing API keys. Ensure they are set in the .env file.")

print(f"{dt.datetime.now()} - API keys loaded successfully!\nDiscord URL: {DISCORD_WEBHOOK_URL}")
# Ensure API keys exist
if not CLOUDFLARE_API_KEY or not DISCORD_WEBHOOK_URL:
    raise ValueError("Missing API keys. Ensure environment variables are set.")

# Cloudflare redirect update function
def update_cloudflare_redirect(new_channel):
    """Update Cloudflare redirect rule."""
    global current_channel
    if new_channel == current_channel:
        return  

    body = {
        "action": "redirect",
        "action_parameters": {
            "from_value": {
                "preserve_query_string": False,
                "status_code": 307,
                "target_url": {
                    "value": f"https://twitch.tv/{new_channel}"
                }
            }
        },
        "description": "SkyBass Redirect",
        "enabled": True,
        "expression": '(http.host eq "skybass.raidredirect.com")',
        "id": "eca63e1048bc441d9a0e4feed8066600",
        "ref": "eca63e1048bc441d9a0e4feed8066600",
        "version": "4"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"
    }

    url = CLOUDFLARE_URL

    for attempt in range(3):
        try:
            response = requests.patch(url, headers=headers, json=body)
            response.raise_for_status()
            current_channel = new_channel
            print(f"{dt.datetime.now()} - Successfully updated to {new_channel}")
            break
        except requests.RequestException as e:
            print(f"{dt.datetime.now()} - Error applying change. Attempt {attempt + 1} of 3. Error: {e}")
            time.sleep(60)
    else:
        print(f"{dt.datetime.now()} - Failed to apply change after 3 attempts.")


# Initial setup
# Load initial setup from a JSON file
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        current_channel = config.get("current_channel", "DjRyaru")
        last_message = config.get("last_message", 1379483597656031323)

except Exception as e:
    print(f"{dt.datetime.now()} - Error reading config.json: {e}, assuming no last streamer")
    current_channel="UNKNOWN"

print(f"Raid train bot started! Initial channel: {current_channel}")


while True:
    print(f"{dt.datetime.now()} - Started script")
    # Reload CSV file inside loop to get latest schedule
    try:
        csv = pd.read_csv('event_lineup.csv')
    except Exception as e:
        print(f"{dt.datetime.now()} - Error reading CSV file: {e}")
        time.sleep(100)
        continue

    for _, row in csv.iterrows():
        try:
            # Get stream times and fix
            stream_time = dt.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S')
            hour_csv, day_csv = stream_time.hour+1, stream_time.day
            hour_current, day_current = dt.datetime.now().hour, dt.datetime.now().day
             
            if hour_csv == hour_current and day_csv == day_current:
                print(f"{dt.datetime.now()} - Current hour: {hour_current}, CSV hour found as: {hour_csv}")
                new_channel = row['username']
                print(f"{dt.datetime.now()} - Currently playing: {new_channel}")

                if new_channel != current_channel: 
                    # Send the new channel to current channel
                    current_channel = new_channel

                    # Define your message to send
                    message = f"<@&1352061567927320607>\n\n https://twitch.tv/{current_channel} is taking over the raid train!"
                    
                    # Send the POST request
                    response = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"content": message})

                    if response.status_code in [200, 204]:
                        try:
                            response_json = response.json()
                            print(f"{dt.datetime.now()} - Message sent. ID: {response_json.get('id')}")
                        except ValueError:
                            print(f"{dt.datetime.now()} - Message sent successfully (no JSON response).")
                    else:
                        print(f"{dt.datetime.now()} - Failed to send Discord message: {response.status_code}, {response.text}")
                    
                    # Remove the last sent message defined in Last message
                    print(f"{dt.datetime.now()} - Message to delete: {last_message}")

                    response = requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{last_message}")
                    last_message = response_json.get('id')
                    if response.status_code in [200, 204]:
                        try:
                            print(f"{dt.datetime.now()} - Message removed.")
                        except ValueError:
                            print(f"{dt.datetime.now()} - Message deleted successfully (no JSON response).")
                    else:
                        print(f"{dt.datetime.now()} - Failed to find Discord message: {response.status_code}, {response.text}")

                    # Update config.json for the new streamer and message update.
                    try:
                        with open('config.json', 'w') as config_file:
                            json.dump({"current_channel": current_channel, "last_message": last_message}, config_file, indent=4)
                        print(f"{dt.datetime.now()} - Config file updated successfully.")
                    except Exception as e:
                        print(f"{dt.datetime.now()} - Error updating config.json: {e}")

                    # Update the cloudflare redirect link
                    update_cloudflare_redirect(new_channel)

                # Catch if current_streamer and new_streamer are the same    
                else:
                    print(f"{dt.datetime.now()} - Streamer has not changed.")
        except Exception as e:
            print(f"Error processing row {row}: {e}")

    # Wait for 5 minutes
    time.sleep(300)