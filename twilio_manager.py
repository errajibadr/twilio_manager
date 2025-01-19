import logging
from typing import Dict, List, Optional

from twilio.rest import Client


class TwilioManager:
    def __init__(self, account_sid: str, auth_token: str):
        """Initialize Twilio client with credentials."""
        self.client = Client(account_sid, auth_token)
        self.logger = logging.getLogger(__name__)


    def list_subaccounts(self, friendly_name: Optional[str] = None) -> List[Dict]:
        """
        List all subaccounts or filter by friendly name.
        
        Args:
            friendly_name: Optional filter by friendly name
            
        Returns:
            List of subaccount details
        """
        try:
            params = {}
            if friendly_name:
                params['friendly_name'] = friendly_name

            accounts = self.client.api.v2010.accounts.list(**params)
            return [
                {
                    "sid": account.sid,
                    "friendly_name": account.friendly_name,
                    "auth_token": account.auth_token
                } for account in accounts
            ]

        except Exception as e:
            self.logger.error(f"Failed to list subaccounts: {str(e)}")
            raise
        
    def get_account_numbers(self, account_sid: Optional[str] = None ) -> List[Dict]:
        """
        Get all phone numbers associated with a subaccount.
        
        Args:
            account_sid: The subaccount SID
            
        Returns:
            List of phone numbers and their details
        """
        try:
            numbers = []
            if account_sid:
                local_numbers = self.client.api.v2010.accounts(account_sid).incoming_phone_numbers.local.list()
                mobile_numbers = self.client.api.v2010.accounts(account_sid).incoming_phone_numbers.mobile.list()
            else:
                local_numbers = self.client.incoming_phone_numbers.local.list()
                mobile_numbers = self.client.incoming_phone_numbers.mobile.list()

            numbers.extend([{**number.__dict__, 'number_type': 'local'} for number in local_numbers])
            numbers.extend([{**number.__dict__, 'number_type': 'mobile'} for number in mobile_numbers])
            return numbers

        except Exception as e:
            self.logger.error(f"Failed to fetch phone numbers: {str(e)}")
            raise
        
    def get_addresses(self, account_sid: Optional[str] = None) -> List[Dict]:
        """
        Get all addresses associated with a subaccount.
        
        Args:
            account_sid: The subaccount SID
            
        Returns:
            List of addresses and their details
        """
        try:
            addresses = self.client.api.v2010.accounts(account_sid).addresses.list() # type: ignore
            return [address.__dict__ for address in addresses]
        except Exception as e:
            self.logger.error(f"Failed to fetch addresses: {str(e)}")
            raise
        
    def create_address(self, account_sid: str, customer_name: str = 'PrestigeWebb', friendly_name: str = 'PrestigeWebb', street: str = '22 rue du pont aux choux', city: str = 'Paris', region: str = 'Paris', postal_code: str = '75003', iso_country: str = 'FR') -> dict:
        """
        Create an address for a subaccount.
        """
        address = self.client.api.v2010.accounts(account_sid).addresses.create(customer_name=customer_name, friendly_name=friendly_name, street=street, city=city, region=region, postal_code=postal_code, iso_country=iso_country)
        return address.__dict__

    def duplicate_regulatory_bundle(
        self, bundle_sid: str, target_account_sid: str, friendly_name: Optional[str] = None
    ) -> Dict:
        """
        Duplicate a regulatory bundle to a subaccount.

        Args:
            bundle_sid: The SID of the regulatory bundle to duplicate
            target_account_sid: The target subaccount SID
            friendly_name: Optional name for the new bundle

        Returns:
            Dict containing the new bundle information
        """
        try:
            new_bundle = self.client.numbers.v2.bundle_clone(bundle_sid=bundle_sid).create(target_account_sid=target_account_sid,
             friendly_name=friendly_name)
            
            return new_bundle.__dict__

        except Exception as e:
            self.logger.error(f"Failed to duplicate bundle: {str(e)}")
            raise
        
    def duplicate_own_bundles_to_subaccount(self, target_account_sid: str,) -> List[Dict]:
        """
        Duplicate all own bundles to a subaccount.
        """
        bundles = self.client.numbers.v2.regulatory_compliance.bundles.list()
        for bundle in bundles:
            self.duplicate_regulatory_bundle(bundle_sid=bundle.sid, target_account_sid=target_account_sid, friendly_name=bundle.friendly_name) # type: ignore
        return [bundle.__dict__ for bundle in bundles]

    def get_bundle_sid(self, subaccount_sid: Optional[str] = None) -> Optional[str]:
        """
        Get the bundle SID for a subaccount.
        """
        bundles = self.client.numbers.v2.regulatory_compliance.bundles.list()
        for bundle in bundles:
            if bundle.account_sid == subaccount_sid:
                return bundle.sid
        return None
    
    def get_number_type_from_sid(self,sid: str,account_sid: Optional[str] = None) -> Optional[str]:
        """
        Get the number type from a phone number SID.
        """
        numbers = self.get_account_numbers(account_sid)
        for number in numbers:
            if number['sid'] == sid:
                return number['number_type']
        return None
        
    def transfer_phone_number(self, source_account_sid: str, phone_number_sid: str, target_account_sid: str, address_sid: Optional[str] = None, bundle_sid: Optional[str] = None) -> Dict:
        """
        Transfer a phone number to a different subaccount.

        Args:
            source_account_sid: The source subaccount SID
            phone_number_sid: The SID of the phone number to transfer
            target_account_sid: The target subaccount SID
            address_sid: The address SID
            bundle_sid: The bundle SID

        Returns:
            Dict containing the updated phone number information
        """
        try:
            if bundle_sid is None:
                number_type = self.get_number_type_from_sid(phone_number_sid, source_account_sid)
                reg_bundle = self.list_regulatory_bundles(account_sid=target_account_sid, number_type=number_type)
                if len(reg_bundle) == 0:
                    print('No bundle found, duplicating own bundles from main account')
                    self.duplicate_own_bundles_to_subaccount(target_account_sid)
                    reg_bundle = self.list_regulatory_bundles(account_sid=target_account_sid, number_type=number_type)
                    if len(reg_bundle) == 0:
                        raise Exception('No bundle found, creating one')
                bundle_sid = reg_bundle[0]['sid']
            if address_sid is None:
                addresses = self.get_addresses(target_account_sid)
                print(addresses)
                if len(addresses) == 0:
                    print('No address found, creating one')
                    address =  self.create_address(account_sid=target_account_sid)
                    address_sid = address['sid']
                    address_friendly_name = address['friendly_name']
                else:
                    print('Address found, using it')
                    address_sid = addresses[0]['sid']
                    address_friendly_name = addresses[0]['friendly_name']
                    
                print('address_sid {}, friendly_name {}'.format(address_sid, address_friendly_name))
            # Update the phone number's account
            updated_number = self.client.api.v2010.accounts(source_account_sid).incoming_phone_numbers(phone_number_sid).update(
                account_sid=target_account_sid,
                address_sid=address_sid,
                bundle_sid=bundle_sid
            )

            self.logger.info(
                f"Successfully transferred number {phone_number_sid} from account {source_account_sid} to account {target_account_sid}"
            )
            return updated_number.__dict__

        except Exception as e:
            self.logger.error(f"Failed to transfer phone number: {str(e)}")
            raise

    def list_regulatory_bundles(self, account_sid: Optional[str] = None, number_type: Optional[str] = None, iso_country: Optional[str] = 'FR') -> List[Dict]:
        """
        List regulatory bundles for a specific subaccount or main account.
        
        Args:
            account_sid: Optional subaccount SID. If not provided, lists bundles for the main account
            number_type: Optional filter for bundle type ('national' or 'mobile')
            iso_country: Country code for the bundles (default: 'FR')
            
        Returns:
            List of regulatory bundles and their details
        """
        try:
            # Select the appropriate client
            client = self.client
            if account_sid:
                auth_token = self.get_subaccount_auth_token(account_sid)
                client = Client(account_sid, auth_token)

            bundles = []
            
            # If specific number type requested, fetch only that type
            if number_type:
                bundles_list = client.numbers.v2.regulatory_compliance.bundles.list(
                    number_type=number_type,
                    iso_country=iso_country
                )
                bundles.extend([{**bundle.__dict__, 'number_type': number_type} for bundle in bundles_list])
            else:
                # Fetch both types
                number_types = {
                    'national': 'national',  # Map local to national in the response
                    'mobile': 'mobile'
                }
                
                for api_type, response_type in number_types.items():
                    type_bundles = client.numbers.v2.regulatory_compliance.bundles.list(
                        number_type=api_type,
                        iso_country=iso_country
                    )
                    bundles.extend([{**bundle.__dict__, 'number_type': response_type} for bundle in type_bundles])
            
            return bundles

        except Exception as e:
            self.logger.error(f"Failed to list regulatory bundles: {str(e)}")
            raise
    
    def get_subaccount_auth_token(self, account_sid: str) -> str:
        """
        Get the auth token for a specific subaccount.
        
        Args:
            account_sid: The subaccount SID
            
        Returns:
            The auth token for the subaccount
        """
        try:
            account = self.client.api.v2010.accounts(account_sid).fetch()
            if account is None:
                raise Exception('Account not found')
            return account.auth_token # type: ignore

        except Exception as e:
            self.logger.error(f"Failed to get subaccount auth token: {str(e)}")
            raise

