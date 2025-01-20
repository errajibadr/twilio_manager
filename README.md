# Twilio Manager

A Streamlit-based UI for managing Twilio subaccounts and phone numbers.

## Project Structure

- `src/`: Source code
  - `api/`: API integration code
  - `ui/`: Streamlit UI code
  - `utils/`: Utility functions and configuration
- `tests/`: Test files
- `.env`: Environment variables (not tracked in git)

## Setup

1. Clone the repository
2. Create a `.env` file with your Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `streamlit run src/ui/streamlit_app.py`
