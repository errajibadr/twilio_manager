import asyncio
import logging

import streamlit as st

from async_twilio_manager import AsyncTwilioManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Adjust these with your main Twilio account credentials (or load from st.secrets, environment, etc.)
MAIN_ACCOUNT_SID = st.secrets["twilio"]["account_sid"]
MAIN_AUTH_TOKEN = st.secrets["twilio"]["auth_token"]

@st.cache_data(show_spinner=False)
def get_subaccounts():
    """
    Fetch subaccounts from Twilio and cache them until refreshed.
    """
    async def fetch_subaccounts():
        async with AsyncTwilioManager(MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN) as manager:
            # manager.list_subaccounts() returns a list of subaccount details:
            # [
            #     {
            #         "sid": "ACxxxx",
            #         "friendly_name": "My Subaccount",
            #         "auth_token": "xxxx"
            #     },
            #     ...
            # ]
            return await manager.list_subaccounts()
    return asyncio.run(fetch_subaccounts())

def get_subaccount_numbers(subaccount_sid):
    """
    Fetch phone numbers for a specific subaccount.
    """
    async def fetch_phone_numbers():
        async with AsyncTwilioManager(MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN) as manager:
            return await manager.get_account_numbers(account_sid=subaccount_sid)
    return asyncio.run(fetch_phone_numbers())

def do_transfer_phone_number(source_sid, phone_number_sid, target_sid):
    """
    Transfer a phone number from one subaccount to another.
    """
    async def transfer():
        async with AsyncTwilioManager(MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN) as manager:
            return await manager.transfer_phone_number(
                source_account_sid=source_sid,
                phone_number_sid=phone_number_sid,
                target_account_sid=target_sid
            )
    return asyncio.run(transfer())

def refresh_subaccounts():
    """
    Clear the cached subaccounts and force a reload.
    """
    get_subaccounts.clear()

def main():
    st.title("Async Twilio Manager UI")

    # Refresh button to clear and re-fetch subaccounts
    if st.button("Refresh Subaccounts"):
        refresh_subaccounts()

    subaccounts = get_subaccounts()
    
    if not subaccounts:
        st.warning("No subaccounts found.")
        return

    # Choose a subaccount to view phone numbers
    subaccount_sids = [sa["sid"] for sa in subaccounts]
    subaccount_map = {sa["sid"]: sa["friendly_name"] for sa in subaccounts}
    selected_sub_sid = st.selectbox("Select a subaccount", subaccount_sids, format_func=lambda x: subaccount_map[x])

    if selected_sub_sid:
        with st.spinner("Loading phone numbers..."):
            phone_numbers = get_subaccount_numbers(selected_sub_sid)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"Found {len(phone_numbers)} phone numbers in subaccount {subaccount_map[selected_sub_sid]}:")
        with col2:
            # Refresh button for phone numbers
            if st.button("Refresh phone numbers"):
                phone_numbers = get_subaccount_numbers(selected_sub_sid)
                st.rerun()

        if phone_numbers:
            # Combine SID with friendly_name in parentheses
            selected_num_sid = st.selectbox(
                "Select a phone number SID to transfer",
                [p["sid"] for p in phone_numbers],
                format_func=lambda sid: f"{sid} ({next((p.get('friendly_name') for p in phone_numbers if p['sid'] == sid), '')})"
            )

            # If we pick a phone number, allow transferring to another subaccount
            st.write("Transfer to another subaccount:")
            other_subaccounts = [sa for sa in subaccounts if sa["sid"] != selected_sub_sid]
            if not other_subaccounts:
                st.info("No other subaccounts available for transfer.")
            else:
                target_account_sid = st.selectbox(
                    "Choose target subaccount",
                    [sa["sid"] for sa in other_subaccounts],
                    format_func=lambda sid: next((sa["friendly_name"] for sa in other_subaccounts if sa["sid"] == sid), sid)
                )

                if st.button("Transfer Number"):
                    with st.spinner("Transferring phone number..."):
                        result = do_transfer_phone_number(
                            source_sid=selected_sub_sid,
                            phone_number_sid=selected_num_sid,
                            target_sid=target_account_sid
                        )
                        st.success(f"Phone number {selected_num_sid} transferred successfully!")
                        st.json(result)
        else:
            st.warning("This subaccount has no phone numbers.")

if __name__ == "__main__":
    main()
