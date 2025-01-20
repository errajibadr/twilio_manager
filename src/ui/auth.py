from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit_authenticator as stauth
import yaml

from src.utils.logger import setup_logger

# Set up logger
logger = setup_logger("auth", Path(__file__).parent.parent.parent / "logs" / "auth.log")


class StreamlitAuth:
    def __init__(self, config_path: str):
        """Initialize the authenticator with a config file path."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"Initialized auth with config from {config_path}")

    def _load_config(self) -> dict:
        """Load the YAML configuration file."""
        if not self.config_path.exists():
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path) as file:
                config = yaml.safe_load(file)
                logger.debug(f"Loaded config: {config}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            raise

    def login(self, username: str, password: str) -> bool:
        """Verify login credentials."""
        logger.info(f"Login attempt for user: {username}")

        if username not in self.config["credentials"]:
            logger.warning(f"Login failed: Username '{username}' not found")
            return False

        stored_password = self.config["credentials"][username]["password"]
        logger.info(f"Stored password: {stored_password}")
        logger.info(f"Password: {password}")
        logger.info(f"Hasher: {stauth.Hasher([]).hash(password)}")

        is_valid = stauth.Hasher([]).hash(password) == stored_password

        if is_valid:
            logger.info(f"Login successful for user: {username}")
        else:
            logger.warning(f"Login failed: Invalid password for user '{username}'")

        return is_valid

    def check_auth(self) -> Optional[str]:
        """Check authentication status and return username if logged in."""
        if "authenticated" not in st.session_state:
            logger.debug("Initializing authentication state")
            st.session_state.authenticated = False
            st.session_state.username = None

        if st.session_state.authenticated:
            logger.debug(f"User already authenticated: {st.session_state.username}")
            return st.session_state.username

        # Create login form
        st.markdown(
            """
            <div style="background-color:#f0f2f6; padding:1rem; border-radius: 5px;">
            <h2 style="color:#1c4e80;">Login Required</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if self.login(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                logger.info(f"User authenticated: {username}")
                st.rerun()
            else:
                logger.warning(f"Authentication failed for username: {username}")
                st.error("Invalid username or password")

        return None
