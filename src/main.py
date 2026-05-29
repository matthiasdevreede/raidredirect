from dotenv import load_dotenv
load_dotenv(override=True)

from utils import LoggerSetup
from cloudflare import CLOUDFLARE_API_KEY, CLOUDFLARE_URL
from discord import DISCORD_WEBHOOK_URL
from scheduler import run

logger = LoggerSetup(__name__).get_logger()

logger.info(f"Cloudflare token present: {bool(CLOUDFLARE_API_KEY)}")
logger.info(f"Cloudflare URL: {CLOUDFLARE_URL}")
logger.info(f"Discord webhook present: {bool(DISCORD_WEBHOOK_URL)}")

if __name__ == "__main__":
    run()