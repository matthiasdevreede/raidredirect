import time
import os
import requests
from utils import LoggerSetup, YAMLReader

# Cloudflare redirect update function
config = YAMLReader().get_yaml("config.yaml")

CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
CLOUDFLARE_URL = os.getenv("CLOUDFLARE_URL")

logger = LoggerSetup(__name__).get_logger()

def update_redirect(new_channel):
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
        "expression": f'(http.host eq "{config["cloudflare_rule_name"]}.raidredirect.com")',
        "id": f"{config['cloudflare_rule_id']}",
        "ref": f"{config['cloudflare_rule_id']}",
        "version": "4"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"
    }

    cloudflare_updated = False

    for attempt in range(3):
        try:
            response = requests.patch(CLOUDFLARE_URL, headers=headers, json=body)
            response.raise_for_status()
            logger.info(f"Successfully updated to {new_channel}")
            cloudflare_updated = True
            break

        except requests.RequestException as e:
            if e.response is not None:
                logger.warning(
                    f"Attempt {attempt+1}/3 failed\n"
                    f"Status: {e.response.status_code}\n"
                    f"Body: {e.response.text}"
                )
            else:
                logger.warning(f"Request failed: {e}")
                
            time.sleep(60)
        
    return cloudflare_updated