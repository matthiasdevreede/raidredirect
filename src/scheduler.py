import time
import pandas as pd
import datetime as dt
import yaml
from utils import LoggerSetup, YAMLReader
from cloudflare import update_redirect
from discord import message_sender, message_remover
from scrapers.r3dlabs import lineup_to_csv

config = YAMLReader().get_yaml("config.yaml")
logger = LoggerSetup(__name__).get_logger()

stream_state = YAMLReader().get_yaml("./data/stream_state.yaml")
current_streamer = stream_state['current_streamer']
last_message = stream_state['last_message']

def check_schedule(csv_file):
    try:
        csv = pd.read_csv(csv_file).dropna(subset='username')
        csv["starttime"] = pd.to_datetime(csv["starttime"], format="%Y-%m-%dT%H:%M:%S", errors="coerce")

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return

    now = dt.datetime.now()
    logger.info(f'Current time is: {now}')
    window_start = now - dt.timedelta(hours=2)

    match = csv[
        (csv["starttime"] <= now) &
        (csv["starttime"] >= window_start)
    ]

    if not match.empty:
        new_channel = match.iloc[0]["username"]

        if new_channel != current_streamer:
            stream_switcher(new_channel)
        else:
            logger.info("Streamer unchanged.")
    else:
        logger.info("No matching streamer.")

def stream_switcher(new_channel):
    global current_streamer, last_message
    # Send the new channel to discord
    current_streamer = new_channel
    message_remover(last_message)
    last_message = message_sender(current_streamer)

    # Update streamer_state.yaml for the new streamer and message update.
    stream_state_updater(current_streamer, last_message)

    # Update the cloudflare redirect link
    update_redirect(current_streamer)

def stream_state_updater(current_streamer, last_message):
    with open('./data/stream_state.yaml', 'w') as file:
        yaml_send = {
            'current_streamer': current_streamer,
            'last_message': last_message,
        }

        yaml.dump(yaml_send, file)     

def run():
    lineup_to_csv(config['raid_train_slug'], f"./data/{config['csv_file_name']}")
    while True:
        check_schedule("./data/raidtrain.csv")
        time.sleep(300)