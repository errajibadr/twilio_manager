import asyncio
import os

import streamlit as st
from dotenv import load_dotenv
from twilio_manager_async import AsyncTwilioManager

# Load environment variables
load_dotenv()

# Initialize session state
if 'twilio_manager' not in st.session_state:
    st.session_state.twilio_manager = AsyncTwilioManager(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN")
    )

async def load_data():
    """Load all necessary data for the app"""
    manager = st.session_state.twilio_manager
    
    # Get subaccounts
    subaccounts = await manager.list_subaccounts()
    
    # Get numbers for each subaccount
    numbers_by_account = {}
    for account in subaccounts:
        numbers = await manager.get_account_numbers(account['sid'])
        numbers_by_account[account['sid']] = numbers
        
    return subaccounts, numbers_by_account

async def transfer_number(source_sid: str, number_sid: str, target_sid: str):
    """Transfer a phone number between accounts"""
    manager = st.session_state.twilio_manager
    await manager.transfer_phone_number(
        source_account_sid=source_sid,
        phone_number_sid=number_sid,
        target_account_sid=target_sid
    )

def main():
    st.title("Twilio Number Manager")
    
    # Load data
    subaccounts, numbers_by_account = asyncio.run(load_data())
    
    # Display accounts and their numbers
    for account in subaccounts:
        with st.expander(f"📱 {account['friendly_name']} ({account['sid']})"):
            numbers = numbers_by_account.get(account['sid'], [])
            
            if not numbers:
                st.info("No phone numbers in this account")
                continue
                
            # Create a table for numbers
            for number in numbers:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"☎️ {number['phone_number']}")
                with col2:
                    st.write(f"Type: {number['number_type']}")
                with col3:
                    st.write(f"SID: {number['sid']}")
                with col4:
                    # Create transfer button with dropdown
                    target_account = st.selectbox(
                        "Transfer to:",
                        options=[acc['sid'] for acc in subaccounts if acc['sid'] != account['sid']],
                        key=f"transfer_{number['sid']}"
                    )
                    
                    if st.button("Transfer", key=f"btn_{number['sid']}"):
                        try:
                            asyncio.run(transfer_number(
                                account['sid'],
                                number['sid'],
                                target_account
                            ))
                            st.success("Transfer successful!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Transfer failed: {str(e)}")

if __name__ == "__main__":
    main() 