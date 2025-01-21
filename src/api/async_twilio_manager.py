# Move your existing AsyncTwilioManager class here
import asyncio
import logging
from typing import Any, Dict, List, Optional

from twilio.rest import Client

from src.api.async_twilio_http_client import AsyncTwilioHttpClient

_logger = logging.getLogger(__name__)


class AsyncTwilioManager:
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        timeout: Optional[float] = None,
        logger: logging.Logger = _logger,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.timeout = timeout
        self.logger = logger
        self._http_client = AsyncTwilioHttpClient()
        self._client = None

    @property
    def client(self) -> Client:
        """Get the Twilio client, raising an error if it's not initialized."""
        if not self._client:
            self._client = Client(self.account_sid, self.auth_token, http_client=self._http_client)
        return self._client

    async def __aenter__(self):
        await self._http_client.init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.close_session()

    async def list_subaccounts(self, friendly_name: Optional[str] = None) -> List[Dict]:
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
                params["friendly_name"] = friendly_name

            accounts = await self.client.api.v2010.accounts.list_async(**params)
            return [
                {
                    "sid": account.sid,
                    "friendly_name": account.friendly_name,
                    "auth_token": account.auth_token,
                }
                for account in accounts
            ]

        except Exception as e:
            self.logger.error(f"Failed to list subaccounts: {str(e)}")
            raise

    async def get_account_numbers(self, account_sid: Optional[str] = None) -> List[Dict]:
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
                local_numbers = await self.client.api.v2010.accounts(
                    account_sid
                ).incoming_phone_numbers.local.list_async()
                mobile_numbers = await self.client.api.v2010.accounts(
                    account_sid
                ).incoming_phone_numbers.mobile.list_async()
            else:
                local_numbers = await self.client.incoming_phone_numbers.local.list_async()
                mobile_numbers = await self.client.incoming_phone_numbers.mobile.list_async()

            numbers.extend(
                [{**number.__dict__, "number_type": "national"} for number in local_numbers]
            )
            numbers.extend(
                [{**number.__dict__, "number_type": "mobile"} for number in mobile_numbers]
            )
            return numbers

        except Exception as e:
            self.logger.error(f"Failed to fetch phone numbers: {str(e)}")
            raise

    async def get_addresses(self, account_sid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all addresses associated with a subaccount.

        Args:
            account_sid: The subaccount SID

        Returns:
            List of addresses and their details
        """
        try:
            addresses = await self.client.api.v2010.accounts(account_sid).addresses.list_async()  # type: ignore
            return [address.__dict__ for address in addresses]
        except Exception as e:
            self.logger.error(f"Failed to fetch addresses: {str(e)}")
            raise

    async def create_address(
        self,
        account_sid: str,
        customer_name: str = "PrestigeWebb",
        friendly_name: str = "PrestigeWebb",
        street: str = "22 rue du pont aux choux",
        city: str = "Paris",
        region: str = "Paris",
        postal_code: str = "75003",
        iso_country: str = "FR",
    ) -> dict[str, str]:
        """
        Create an address for a subaccount.
        """
        address = await self.client.api.v2010.accounts(account_sid).addresses.create_async(
            customer_name=customer_name,
            friendly_name=friendly_name,
            street=street,
            city=city,
            region=region,
            postal_code=postal_code,
            iso_country=iso_country,
        )
        return address.__dict__

    async def duplicate_regulatory_bundle(
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
            new_bundle = await self.client.numbers.v2.bundle_clone(
                bundle_sid=bundle_sid
            ).create_async(target_account_sid=target_account_sid, friendly_name=friendly_name)

            return new_bundle.__dict__

        except Exception as e:
            self.logger.error(f"Failed to duplicate bundle: {str(e)}")
            raise

    async def duplicate_own_bundles_to_subaccount(
        self,
        target_account_sid: str,
    ) -> List[Dict]:
        """
        Duplicate all own bundles to a subaccount.
        """
        bundles = await self.client.numbers.v2.regulatory_compliance.bundles.list_async()
        for bundle in bundles:
            if bundle.sid is None:
                self.logger.error(f"Bundle {bundle.friendly_name} has no SID")
                continue
            await self.duplicate_regulatory_bundle(
                bundle_sid=bundle.sid,
                target_account_sid=target_account_sid,
                friendly_name=bundle.friendly_name,
            )  # type: ignore
        return [bundle.__dict__ for bundle in bundles]

    async def get_bundle_sid(self, subaccount_sid: Optional[str] = None) -> Optional[str]:
        """
        Get the bundle SID for a subaccount.
        """
        bundles = await self.client.numbers.v2.regulatory_compliance.bundles.list_async()
        for bundle in bundles:
            if bundle.account_sid == subaccount_sid:
                return bundle.sid
        return None

    async def get_number_type_from_sid(
        self, sid: str, account_sid: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the number type from a phone number SID.
        """
        numbers = await self.get_account_numbers(account_sid)
        for number in numbers:
            if number["sid"] == sid:
                return number["number_type"]
        return None

    async def transfer_phone_number(
        self,
        source_account_sid: str,
        phone_number_sid: str,
        target_account_sid: str,
        address_sid: Optional[str] = None,
        bundle_sid: Optional[str] = None,
    ) -> Dict:
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
            # Get or create bundle if not provided
            bundle_sid = await self._get_or_create_bundle(
                bundle_sid, phone_number_sid, source_account_sid, target_account_sid
            )

            # Get or create address if not provided
            address_sid = await self._get_or_create_address(address_sid, target_account_sid)

            return await self._execute_number_transfer(
                source_account_sid, phone_number_sid, target_account_sid, address_sid, bundle_sid
            )

        except Exception as e:
            self.logger.error(f"Failed to transfer phone number: {str(e)}")
            raise

    async def _get_or_create_bundle(
        self,
        bundle_sid: Optional[str],
        phone_number_sid: str,
        source_account_sid: str,
        target_account_sid: str,
    ) -> str:
        """Helper method to get or create a regulatory bundle"""
        if bundle_sid is not None:
            return bundle_sid

        number_type = await self.get_number_type_from_sid(phone_number_sid, source_account_sid)
        reg_bundle = await self.list_regulatory_bundles(
            account_sid=target_account_sid, number_type=number_type
        )

        if not reg_bundle:
            self.logger.info("No bundle found, duplicating own bundles from main account")
            await self.duplicate_own_bundles_to_subaccount(target_account_sid)
            reg_bundle = await self.list_regulatory_bundles(
                account_sid=target_account_sid, number_type=number_type
            )
            if not reg_bundle:
                raise Exception("No bundle found, creating one")

        return reg_bundle[0]["sid"]

    async def _get_or_create_address(
        self, address_sid: Optional[str], target_account_sid: str
    ) -> str:
        """Helper method to get or create an address"""
        if address_sid is not None:
            return address_sid

        addresses: list[dict[str, str]] = await self.get_addresses(target_account_sid)
        if len(addresses) == 0:
            self.logger.info("No address found, creating one")
            address = await self.create_address(account_sid=target_account_sid)
            address_sid = address["sid"]
            address_friendly_name = address["friendly_name"]
        else:
            self.logger.info("Address found, using it")
            address_sid = addresses[0]["sid"]
            address_friendly_name = addresses[0]["friendly_name"]

        self.logger.info(f"Using address_sid {address_sid}, friendly_name {address_friendly_name}")
        return address_sid

    async def _execute_number_transfer(
        self,
        source_account_sid: str,
        phone_number_sid: str,
        target_account_sid: str,
        address_sid: str,
        bundle_sid: str,
    ) -> Dict:
        """Helper method to execute the actual number transfer"""
        try:
            updated_number = (
                await self.client.api.v2010.accounts(source_account_sid)
                .incoming_phone_numbers(phone_number_sid)
                .update_async(
                    account_sid=target_account_sid, address_sid=address_sid, bundle_sid=bundle_sid
                )
            )
            self.logger.info(
                f"Successfully transferred number {phone_number_sid} from account {source_account_sid} to account {target_account_sid}"
            )
            return updated_number.__dict__

        except Exception as transfer_error:
            return await self._verify_transfer(transfer_error, phone_number_sid, target_account_sid)

    async def _verify_transfer(
        self, transfer_error: Exception, phone_number_sid: str, target_account_sid: str
    ) -> Dict:
        """Helper method to verify transfer status in case of errors"""
        try:
            await asyncio.sleep(2)
            target_numbers = await self.get_account_numbers(target_account_sid)

            for number in target_numbers:
                if number.get("sid") == phone_number_sid:
                    self.logger.info(
                        f"Number {phone_number_sid} found in target account despite error. Transfer likely successful."
                    )
                    return number

            raise transfer_error

        except Exception as verify_error:
            self.logger.error(f"Error during transfer verification: {str(verify_error)}")
            raise transfer_error

    async def list_regulatory_bundles(
        self,
        account_sid: Optional[str] = None,
        number_type: Optional[str] = None,
        iso_country: Optional[str] = "FR",
    ) -> List[Dict]:
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
            subaccount_http_client = None

            if account_sid:
                auth_token = await self.get_subaccount_auth_token(account_sid)
                if auth_token is None:
                    raise Exception("Auth token not found")

                # Create a new HTTP client with proper lifecycle management
                subaccount_http_client = AsyncTwilioHttpClient()
                await subaccount_http_client.__aenter__()
                client = Client(account_sid, auth_token, http_client=subaccount_http_client)

            try:
                bundles = []

                # If specific number type requested, fetch only that type
                if number_type:
                    bundles_list = await client.numbers.v2.regulatory_compliance.bundles.list_async(
                        number_type=number_type, iso_country=iso_country
                    )
                    bundles.extend(
                        [{**bundle.__dict__, "number_type": number_type} for bundle in bundles_list]
                    )
                else:
                    # Fetch both types
                    number_types = {
                        "national": "national",  # Map local to national in the response
                        "mobile": "mobile",
                    }

                    for api_type, response_type in number_types.items():
                        type_bundles = (
                            await client.numbers.v2.regulatory_compliance.bundles.list_async(
                                number_type=api_type, iso_country=iso_country
                            )
                        )
                        bundles.extend(
                            [
                                {**bundle.__dict__, "number_type": response_type}
                                for bundle in type_bundles
                            ]
                        )

                return bundles

            finally:
                # Clean up the subaccount HTTP client if we created one
                if subaccount_http_client:
                    await subaccount_http_client.__aexit__(None, None, None)

        except Exception as e:
            self.logger.error(f"Failed to list regulatory bundles: {str(e)}")
            raise

    async def get_subaccount_auth_token(self, account_sid: str) -> str | None:
        """
        Get the auth token for a specific subaccount.

        Args:
            account_sid: The subaccount SID

        Returns:
            The auth token for the subaccount
        """
        try:
            account = await self.client.api.v2010.accounts(account_sid).fetch_async()
            if account is None:
                raise Exception("Account not found")
            return account.auth_token

        except Exception as e:
            self.logger.error(f"Failed to get subaccount auth token: {str(e)}")
            raise
