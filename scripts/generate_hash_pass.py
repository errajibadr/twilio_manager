# hash_password.py
import getpass
import os
from pathlib import Path

import streamlit_authenticator as stauth
import yaml
from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def hash_password(password: str) -> str:
    return stauth.Hasher([password]).hash(password=password)


def main():
    print("Password Generator for Twilio Manager")
    print("-" * 40)

    credentials = {}
    while True:
        username = input("Enter username (or press Enter to finish): ").strip()
        if not username:
            break

        password = getpass.getpass("Enter password: ")
        credentials[username] = {
            "password": password  # In production, use a proper password hashing method
        }

    config = {"credentials": credentials}

    # Save to auth_config.yaml
    config_path = Path(__file__).parent.parent / "src" / "ui" / "auth_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    print(f"\nConfiguration saved to {config_path}")


# Example usage:
# python hash_password.py
if __name__ == "__main__":
    main()
