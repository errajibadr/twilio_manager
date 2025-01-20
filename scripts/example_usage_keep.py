import os

from dotenv import load_dotenv

from src.api.twilio_manager import TwilioManager

load_dotenv()

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

# Initialize the manager
manager = TwilioManager(account_sid=account_sid, auth_token=auth_token)


# List all subaccounts with their auth tokens
subaccounts = manager.list_subaccounts()
print("\nAll subaccounts:")
for account in subaccounts:
    print(
        f"Name: {account['friendly_name']}, SID: {account['sid']}, Auth Token: {account['auth_token']}"
    )

# Get numbers for a specific subaccount
numbers = manager.get_account_numbers()
print("\nPhone numbers:")
for number in numbers:
    print(f"Phone Number: {number['phone_number']}")
    print(f"Number Type: {number['number_type']}")
    print(f"Account SID: {number['account_sid']}")
    print(f"friendly name: {number['friendly_name']}, SID: {number['sid']}")

manager.get_number_type_from_sid("PNxxx")

manager.transfer_phone_number(
    source_account_sid=account_sid, phone_number_sid="PNxxx", target_account_sid="ACxxx"
)


addresses = manager.get_addresses()
[address for address in addresses]
