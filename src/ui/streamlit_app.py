import asyncio
from pathlib import Path

import streamlit as st

from src.api.async_twilio_manager import AsyncTwilioManager
from src.ui.auth import StreamlitAuth
from src.utils.config import MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN
from src.utils.logger import setup_logger

# Set up logger
logger = setup_logger("streamlit_app", Path(__file__).parent.parent.parent / "logs" / "app.log")

# Initialize authenticator
auth_config_path = Path(__file__).parent / "auth_config.yaml"

authenticator = StreamlitAuth(str(auth_config_path))


@st.cache_data(show_spinner=False)
def get_subaccounts():
    """
    Fetch subaccounts from Twilio and cache them until refreshed.
    """

    async def fetch_subaccounts():
        async with AsyncTwilioManager(MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN) as manager:
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
                target_account_sid=target_sid,
            )

    return asyncio.run(transfer())


def refresh_subaccounts():
    """
    Clear the cached subaccounts and force a reload.
    """
    get_subaccounts.clear()


def get_subaccount_bundles(subaccount_sid):
    """
    Fetch regulatory bundles for a specific subaccount.
    """

    async def fetch_bundles():
        async with AsyncTwilioManager(MAIN_ACCOUNT_SID, MAIN_AUTH_TOKEN) as manager:
            return await manager.list_regulatory_bundles(account_sid=subaccount_sid)

    return asyncio.run(fetch_bundles())


def main():
    st.set_page_config(page_title="Async Twilio Manager", layout="wide")

    # Check authentication before showing any content
    username = authenticator.check_auth()
    if not username:
        return

    # Show welcome message
    st.sidebar.markdown(f"Welcome, **{username}**!")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    st.sidebar.title("Async Twilio Manager UI")
    # Moved the refresh subaccounts button to the sidebar
    if st.sidebar.button("Refresh Subaccounts"):
        refresh_subaccounts()
        st.rerun()

    if st.sidebar.checkbox("Debug Mode"):
        st.sidebar.write("Auth Config Path:", auth_config_path)
        st.sidebar.write("Auth Config Exists:", auth_config_path.exists())
        if auth_config_path.exists():
            with open(auth_config_path) as f:
                st.sidebar.code(f.read())

    subaccounts = get_subaccounts()

    if not subaccounts:
        st.sidebar.warning("No subaccounts found.")
        return

    # Sidebar selectbox for subaccount
    subaccount_sids = [sa["sid"] for sa in subaccounts]
    subaccount_map = {sa["sid"]: sa["friendly_name"] for sa in subaccounts}
    selected_sub_sid = st.sidebar.selectbox(
        "Select a subaccount", subaccount_sids, format_func=lambda x: subaccount_map[x]
    )

    # Layout columns: left for tabs with phone numbers & bundles, right for transfer UI
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown(
            """
            <div style="background-color:#e8f4fa; padding:0.5rem; border-radius: 5px;">
            <h3 style="color:#1c4e80;">Subaccount Details</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(f"Subaccount SID: {selected_sub_sid}")

        # Show tabs for phone numbers and regulatory bundles
        tab_numbers, tab_bundles = st.tabs(["Phone Numbers", "Regulatory Bundles"])

        with tab_numbers:
            # We fetch phone numbers for the selected subaccount
            with st.spinner("Loading phone numbers..."):
                phone_numbers = get_subaccount_numbers(selected_sub_sid)

            # Refresh phone numbers button
            if st.button("Refresh phone numbers"):
                phone_numbers = get_subaccount_numbers(selected_sub_sid)
                st.rerun()

            st.write(
                f"Found {len(phone_numbers)} phone numbers in subaccount {subaccount_map[selected_sub_sid]}:"
            )

            if phone_numbers:
                # Display each phone number with an emoji based on type
                for p in phone_numbers:
                    # If the stored number_type is 'mobile', use a mobile phone emoji; otherwise '☎️'
                    emoji = "📱" if p.get("number_type") == "mobile" else "☎️"
                    friendly = p.get("friendly_name") or "No Friendly Name"
                    st.markdown(f"- {emoji} **{p['sid']}** ({friendly})")
            else:
                st.warning("This subaccount has no phone numbers.")

        with tab_bundles:
            # We fetch regulatory bundles for the selected subaccount
            with st.spinner("Loading regulatory bundles..."):
                bundles = get_subaccount_bundles(selected_sub_sid)

            if st.button("Refresh bundles"):
                bundles = get_subaccount_bundles(selected_sub_sid)
                st.rerun()

            st.write(
                f"Found {len(bundles)} bundles in subaccount {subaccount_map[selected_sub_sid]}:"
            )

            if bundles:
                for b in bundles:
                    # Use a phone emoji for 'national' or 'mobile' type
                    number_type = b.get("number_type", "")
                    emoji = "📱" if number_type == "mobile" else "☎️"
                    friendly = b.get("friendly_name") or b.get("sid")
                    st.markdown(f"- {emoji} **{b['sid']}** ({friendly}), Type: {number_type}")
            else:
                st.warning("This subaccount has no regulatory bundles.")

    with col_right:
        st.markdown(
            """
            <div style="background-color:#f8f2fa; padding:0.5rem; border-radius: 5px;">
            <h3 style="color:#7b1ca0;">Transfer Phone Number</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Provide a selectbox for phone numbers to transfer
        phone_numbers = get_subaccount_numbers(selected_sub_sid)
        if phone_numbers:
            selected_num_sid = st.selectbox(
                "Select a phone number to transfer",
                [p["sid"] for p in phone_numbers],
                format_func=lambda sid: (
                    # Look up the phone number object by SID
                    f"{('📱' if next((p for p in phone_numbers if p['sid'] == sid), {}).get('number_type') == 'mobile' else '☎️')} "
                    f"{next((p for p in phone_numbers if p['sid'] == sid), {}).get('friendly_name', 'No Friendly Name')}"
                ),
            )

            # Next, pick a target subaccount
            other_subaccounts = [sa for sa in subaccounts if sa["sid"] != selected_sub_sid]
            if not other_subaccounts:
                st.info("No other subaccounts available for transfer.")
            else:
                target_account_sid = st.selectbox(
                    "Choose target subaccount",
                    [sa["sid"] for sa in other_subaccounts],
                    format_func=lambda sid: next(
                        (sa["friendly_name"] for sa in other_subaccounts if sa["sid"] == sid), sid
                    ),
                )

                if st.button("Transfer Number", key="transfer_btn"):
                    with st.spinner("Transferring phone number..."):
                        result = do_transfer_phone_number(
                            source_sid=selected_sub_sid,
                            phone_number_sid=selected_num_sid,
                            target_sid=target_account_sid,
                        )
                        st.success(f"Phone number {selected_num_sid} transferred successfully!")
                        st.json(result)
        else:
            st.warning("No phone numbers available; cannot transfer.")


if __name__ == "__main__":
    main()
