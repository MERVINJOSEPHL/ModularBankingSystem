# smart-bank-modular/pages/customer_dashboard.py - FULL PAGE

import streamlit as st
import requests
import pandas as pd
from decimal import Decimal

def show_kyc_submission(api_url, headers):
    st.subheader("KYC Registration")
    
    with st.form("kyc_form"):
        name = st.text_input("Full Legal Name")
        phone_number = st.text_input("Phone Number")
        address = st.text_area("Residential Address")
        submitted = st.form_submit_button("Submit KYC Details")
        
        if submitted:
            kyc_data = {"name": name, "phone_number": phone_number, "address": address}
            try:
                response = requests.post(
                    f"{api_url}/kyc/customer/submit",
                    headers=headers(),
                    json=kyc_data
                )
                if response.status_code == 200:
                    st.success(f"KYC submitted successfully! Status: {response.json()['kyc_status']}")
                else:
                    st.error(f"KYC Submission Failed: {response.json().get('detail', 'Error.')}")
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")

def show_fund_transfer(api_url, headers):
    st.subheader("Fund Transfer (P2P) & Balance Check")
    
    account_number = st.text_input("Your Source Account Number")
    
    if st.button("Check Account Balance"):
        if not account_number:
             st.warning("Please enter your account number.")
        else:
            try:
                response = requests.get(
                    f"{api_url}/transactions/customer/balance/{account_number}",
                    headers=headers()
                )
                if response.status_code == 200:
                    data = response.json()
                
                    st.success(f"Balance: **${float(data['current_balance']):,.2f}**")
                    st.info(f"Daily Limit: ${float(data['daily_transfer_limit']):,.2f} | Used Today: ${float(data['daily_transacted_amount_today']):,.2f}")
                else:
                    st.error(f"Balance check failed: {response.json().get('detail', 'Error.')}")
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")

    st.markdown("---")
    

    with st.form("transfer_form"):
        st.write(f"Transferring from: **{account_number or 'Not Entered'}**")
        target_acc = st.text_input("Target Account Number")
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")
        description = st.text_input("Description (Optional)")
        
        submitted = st.form_submit_button("Execute Transfer")
        
        if submitted:
            if not account_number:
                st.error("Please enter your Source Account Number above.")
            else:
                transfer_data = {
                    "source_account_number": account_number, 
                    "target_account_number": target_acc,
                    "amount": amount,
                    "description": description
                }
                try:
                    response = requests.post(
                        f"{api_url}/transactions/customer/transfer",
                        headers=headers(),
                        json=transfer_data
                    )
                    if response.status_code == 201:
                        st.success(f"Transfer Successful! Txn ID: {response.json()['transaction_id']}")
                        st.rerun()
                    else:
                        st.error(f"Transfer Failed: {response.json().get('detail', 'Error.')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"API Error: {e}")

def show_loan_application(api_url, headers):
    st.subheader("Loan Application")
    st.info("Requires KYC Approval before applying for a loan.")
    
    with st.form("loan_form"):
        loan_type = st.selectbox("Loan Type", ["Personal", "Home", "Auto"])
        loan_amount = st.number_input("Loan Amount", min_value=1000.0, format="%.2f")
        tenure_months = st.number_input("Tenure (Months)", min_value=1, max_value=360)
        submitted = st.form_submit_button("Apply for Loan")
        
        if submitted:
            loan_data = {
                "loan_type": loan_type,
                "loan_amount": loan_amount,
                "tenure_months": tenure_months
            }
            try:
                response = requests.post(
                    f"{api_url}/loan/customer/apply",
                    headers=headers(),
                    json=loan_data
                )
                if response.status_code == 201:
                    st.success(f"Loan application submitted! ID: {response.json()['loan_id']}")
                else:
                    st.error(f"Loan Application Failed: {response.json().get('detail', 'Error.')}")
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {e}")

def show_loan_status(api_url, headers):
    st.subheader("My Loan Status")


    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected", "Active", "Paid"])
    
    params = {}
    if status_filter != "All":
        params['status_filter'] = status_filter
        
    if st.button("Refresh Loan List"):
        try:
            response = requests.get(
                f"{api_url}/loan/customer/my-loans",
                headers=headers(),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json().get('loans', [])
                
                if data:
                    df = pd.DataFrame(data)
                    df['loan_id'] = df['loan_id'].astype(str).str[:8] + '...'
                    
                    st.success(f"Found {len(data)} loans (Filtered: {status_filter}).")
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No loans found matching the selected criteria.")
            else:
                st.error(f"Failed to fetch loan status: {response.json().get('detail', 'Error.')}")

        except requests.exceptions.RequestException as e:
            st.error(f"API Error fetching loans: {e}")

def show_dashboard(api_url, get_headers):
    st.title("Customer Dashboard 💰")
    
    tab1, tab2, tab3, tab4 = st.tabs([ "Transfer", "Loan Application", "Loan Status","KYC"])
    
    
    
    with tab1:
        show_fund_transfer(api_url, get_headers)

    with tab2:
        show_loan_application(api_url, get_headers)
        
    with tab3:
        # Call the new function
        show_loan_status(api_url, get_headers)
    
    with tab4:
        show_kyc_submission(api_url, get_headers)