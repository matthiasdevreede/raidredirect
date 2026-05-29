
import os
from utils import LoggerSetup, YAMLReader
import requests

logger = LoggerSetup(__name__).get_logger()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

config = YAMLReader().get_yaml("config.yaml")

def message_sender(current_streamer):
    # Define your message to send
    message = f"<@&{config['role_to_tag']}>\n\n https://twitch.tv/{current_streamer} is taking over the raid train!"
    
    # Send the POST request
    response = requests.post(f"{DISCORD_WEBHOOK_URL}?wait=true", json={"content": message})
    if response.status_code in [200, 204]:
        try:
            response_json = response.json()
            logger.info(f"Message sent. ID: {response_json.get('id')}")
            return response_json.get('id')
        except ValueError:
            logger.info("Message sent successfully (no JSON response).")
    else:
        logger.warning(f"Failed to send Discord message: {response.status_code}, {response.text}")
    return None

def message_remover(last_message):
    # Remove the last sent message defined in Last message
    logger.info(f"Message to delete: {last_message}")

    response = requests.delete(f"{DISCORD_WEBHOOK_URL}/messages/{last_message}")

    if response.status_code in [200, 204]:
        logger.info(f"Message deleted successfully.")
        return True
    else:
        logger.warning(f"Failed to find Discord message: {response.status_code}, {response.text}") 
        return False  