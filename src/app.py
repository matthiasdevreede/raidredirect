import time
import pandas as pd
import datetime as dt
import requests
import os
from dotenv import load_dotenv
import os
import json

from utils import LoggerSetup, YAMLReader

load_dotenv(override=True)

# TODO: Ability to reset CSV through discord
# TODO: Get CSV script easily callable every 5 minutes (if needed)
# TODO: Fix NaN values in CSV 
# TODO: 

logger = LoggerSetup("Rijksoverheid").get_logger()

config = YAMLReader().get_yaml("config.yaml")
stream_state = YAMLReader().get_yaml("stream_state.yaml")

current_streamer = stream_state['current_streamer']
last_message = stream_state['last_message']

# Access the variables
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
CLOUDFLARE_URL = os.getenv("CLOUDFLARE_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
logger.info(f"API keys loaded successfully!\nDiscord URL: {DISCORD_WEBHOOK_URL}")


logger.info(f"Raid train bot started! Initial channel: {current_channel}")

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
        "description": f"{config['cloudflare_rule_name']} Redirect",
        "enabled": True,
        "expression": f'(http.host eq "{config['cloudflare_rule_name']}.raidredirect.com")',
        "id": f"{config['cloudflare_rule_id']}",
        "ref": f"{config['cloudflare_rule_id']}",
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
            logger.info(f"Successfully updated to {new_channel}")
            break
        except requests.RequestException as e:
            logger.warning(f"Error applying change. Attempt {attempt + 1} of 3. Error: {e}")
            time.sleep(60)
    else:
        logger.error(f"Failed to apply change after 3 attempts.")

while True:
    logger.info(f"Started script")
    # Reload CSV file inside loop to get latest schedule
    try:
        csv = pd.read_csv('event_lineup.csv')
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        time.sleep(100)
        continue

    for _, row in csv.iterrows():
        try:
            # Get stream times and fix
            stream_time = dt.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S')
            hour_csv, day_csv = stream_time.hour+1, stream_time.day
            hour_current, day_current = dt.datetime.now().hour, dt.datetime.now().day
             
            if hour_csv == hour_current and day_csv == day_current:
                logger.info(f"Current hour: {hour_current}, CSV hour found as: {hour_csv}")
                new_channel = row['username']
                logger.info(f"Currently playing: {new_channel}")

                if new_channel != current_channel: 
                    # Send the new channel to current channel
                    current_channel = new_channel

                    # Define your message to send
                    message = f"<@&{config['role_to_tag']}>\n\n https://twitch.tv/{current_channel} is taking over the raid train!"
                    
                    # Send the POST request
                    response = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"content": message})

                    if response.status_code in [200, 204]:
                        try:
                            response_json = response.json()
                            logger.info(f"Message sent. ID: {response_json.get('id')}")
                        except ValueError:
                            logger.info(f"Message sent successfully (no JSON response).")
                    else:
                        logger.warning(f"Failed to send Discord message: {response.status_code}, {response.text}")
                    
                    # Remove the last sent message defined in Last message
                    logger.info(f"Message to delete: {last_message}")

                    response = requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{last_message}")
                    last_message = response_json.get('id')
                    if response.status_code in [200, 204]:
                        try:
                            logger.info(f"Message removed.")
                        except ValueError:
                            logger.info(f"Message deleted successfully (no JSON response).")
                    else:
                        logger.warning(f"Failed to find Discord message: {response.status_code}, {response.text}")

                    # Update config.json for the new streamer and message update.
                    try:
                        with open('config.json', 'w') as config_file:
                            json.dump({"current_channel": current_channel, "last_message": last_message}, config_file, indent=4)
                        logger.info(f"Config file updated successfully.")
                    except Exception as e:
                        logger.error(f"Error updating config.json: {e}")

                    # Update the cloudflare redirect link
                    update_cloudflare_redirect(new_channel)

                # Catch if current_streamer and new_streamer are the same    
                else:
                    logger.info(f"Streamer has not changed.")
        except Exception as e:
            logger.warning(f"Error processing row {row}: {e}")

    # Wait for 5 minutes
    time.sleep(300)