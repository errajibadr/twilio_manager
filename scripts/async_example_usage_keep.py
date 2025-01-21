import asyncio
import logging
import os

from dotenv import load_dotenv

from src.api.async_twilio_manager import AsyncTwilioManager

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main():
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]

    async with AsyncTwilioManager(account_sid=account_sid, auth_token=auth_token) as manager:
        # subaccounts = await manager.list_subaccounts()
        # print(subaccounts)

        # numbers = await manager.get_account_numbers()
        # print(numbers)

        # bundles = await manager.list_regulatory_bundles()
        # print(bundles)

        number_type = await manager.get_number_type_from_sid(sid="PNxxxx", account_sid=account_sid)
        print(number_type)
        reg_bundle = await manager.list_regulatory_bundles(
            account_sid=account_sid, number_type=number_type
        )
        print(reg_bundle)

        # number = await manager.transfer_phone_number(
        #     phone_number_sid="PNxxx", target_account_sid="ACxxx", source_account_sid=account_sid
        # )
        # print(number)


if __name__ == "__main__":
    asyncio.run(main())
