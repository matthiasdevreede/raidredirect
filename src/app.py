import time
import pandas as pd
import datetime as dt
import requests
import os
from dotenv import load_dotenv
import os
import yaml
from utils import LoggerSetup, YAMLReader

load_dotenv(override=True)

# TODO: Ability to reset CSV through discord
# TODO: Get CSV script easily callable every 5 minutes (if needed)
# TODO: Fix NaN values in CSV 

logger = LoggerSetup("Rijksoverheid").get_logger()

config = YAMLReader().get_yaml("config.yaml")
stream_state = YAMLReader().get_yaml("stream_state.yaml")

# Access the variables
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
CLOUDFLARE_URL = os.getenv("CLOUDFLARE_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
logger.info(f"API keys loaded successfully!\nDiscord URL: {DISCORD_WEBHOOK_URL}")


# Cloudflare redirect update function
def update_cloudflare_redirect(new_channel):
    """Update Cloudflare redirect rule."""

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
            logger.info(f"Successfully updated to {new_channel}")
            break
        except requests.RequestException as e:
            logger.warning(f"Error applying change. Attempt {attempt + 1} of 3. Error: {e}")
            time.sleep(60)
    else:
        logger.error(f"Failed to apply change after 3 attempts.")


class StreamUpdater:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.current_streamer = stream_state['current_streamer']
        self.last_message = stream_state['last_message']
    
    def run(self):
        while True:
            self.check_schedule()
            time.sleep(300)

    def check_schedule(self):
        try:
            csv = pd.read_csv(self.csv_file).dropna()
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            time.sleep(100)
            return

        now = dt.datetime.now()
        for _, row in csv.iterrows():
            stream_time = dt.datetime.strptime(row['starttime'], '%Y-%m-%dT%H:%M:%S')
            if stream_time.hour + 1 == now.hour and stream_time.day == now.day:
                new_channel = row['username']
                logger.info(f"Schedule match found. Current streamer should be {new_channel}.")
                if new_channel != self.current_streamer:
                    self._switch_stream(new_channel)
                else:
                    logger.info("Streamer unchanged.")
                break
        else:
            logger.info("No matching streamer for current time.")

    def _stream_switcher(self, new_channel):
        # Send the new channel to discord
        self.current_streamer = new_channel
        self._message_remover(self.last_message)
        self.last_message = self._message_sender(self.current_streamer)

        # Update streamer_state.yaml for the new streamer and message update.
        self._stream_state_updater(self.current_streamer, self.last_message)

        # Update the cloudflare redirect link
        update_cloudflare_redirect(self.current_streamer)

        # Wait for 5 minutes
        time.sleep(300)

    def _stream_state_updater(self, current_streamer, last_message):
        with open('stream_state.yaml', 'w') as file:
            yaml_send = {
                'current_streamer': current_streamer,
                'last_message': last_message,
            }
    
            yaml.dump(yaml_send, file)

    def _message_sender(self, current_streamer):
        # Define your message to send
        message = f"<@&{config['role_to_tag']}>\n\n https://twitch.tv/{current_streamer} is taking over the raid train!"
        
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
        
        return response_json.get('id')
 
    def _message_remover(self, last_message):
        # Remove the last sent message defined in Last message
        logger.info(f"Message to delete: {last_message}")

        response = requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{last_message}")

        if response.status_code in [200, 204]:
            try:
                logger.info(f"Message removed.")
            except ValueError:
                logger.info(f"Message deleted successfully (no JSON response).")
        else:
            logger.warning(f"Failed to find Discord message: {response.status_code}, {response.text}")                 

while True:
    StreamUpdater("data/event_lineup.csv").run()