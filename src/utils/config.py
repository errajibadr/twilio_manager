import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Twilio credentials
MAIN_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
MAIN_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

AUTH_CONFIG_PATH = Path(__file__).parent.parent.parent / "ui" / "auth_config.yaml"
