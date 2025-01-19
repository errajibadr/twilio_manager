import logging
from typing import Dict, List, Optional
import httpx
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class AsyncTwilioManager:
    def __init__(self, account_sid: str, auth_token: str):
        """Initialize Twilio client with credentials."""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.client = Client(account_sid, auth_token)
        self.logger = logging.getLogger(__name__)
        self.async_client = httpx.AsyncClient(
            auth=(account_sid, auth_token),
            base_url="https://api.twilio.com",
            timeout=30.0
        )

    async def list_subaccounts(self, friendly_name: Optional[str] = None) -> List[Dict]:
        """Async version of list_subaccounts"""
        try:
            params = {}
            if friendly_name:
                params['FriendlyName'] = friendly_name

            response = await self.async_client.get(
                f"/2010-04-01/Accounts.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return [
                {
                    "sid": account["sid"],
                    "friendly_name": account["friendly_name"],
                    "auth_token": account["auth_token"],
                    "status": account["status"]
                } for account in data["accounts"]
            ]

        except Exception as e:
            self.logger.error(f"Failed to list subaccounts: {str(e)}")
            raise

    async def get_account_numbers(self, account_sid: Optional[str] = None) -> List[Dict]:
        """Async version of get_account_numbers"""
        try:
            account_path = f"/2010-04-01/Accounts/{account_sid or self.account_sid}"
            
            # Get local numbers
            local_response = await self.async_client.get(
                f"{account_path}/IncomingPhoneNumbers/Local.json"
            )
            local_response.raise_for_status()
            local_data = local_response.json()

            # Get mobile numbers
            mobile_response = await self.async_client.get(
                f"{account_path}/IncomingPhoneNumbers/Mobile.json"
            )
            mobile_response.raise_for_status()
            mobile_data = mobile_response.json()

            numbers = []
            numbers.extend([{**number, 'number_type': 'local'} for number in local_data["incoming_phone_numbers"]])
            numbers.extend([{**number, 'number_type': 'mobile'} for number in mobile_data["incoming_phone_numbers"]])
            
            return numbers

        except Exception as e:
            self.logger.error(f"Failed to fetch phone numbers: {str(e)}")
            raise

    async def transfer_phone_number(
        self, 
        source_account_sid: str, 
        phone_number_sid: str, 
        target_account_sid: str
    ) -> Dict:
        """Async version of transfer_phone_number"""
        try:
            # For transfers, we'll still use the sync client as this operation is less common
            # and more critical to get right
            updated_number = self.client.api.v2010.accounts(source_account_sid)\
                .incoming_phone_numbers(phone_number_sid)\
                .update(account_sid=target_account_sid)

            self.logger.info(
                f"Successfully transferred number {phone_number_sid} from "
                f"account {source_account_sid} to account {target_account_sid}"
            )
            
            return updated_number._properties

        except Exception as e:
            self.logger.error(f"Failed to transfer phone number: {str(e)}")
            raise

    async def close(self):
        """Close the async client"""
        await self.async_client.aclose() 