# smart-bank-modular/pages/admin_dashboard.py - FINAL CORRECTED VERSION

import streamlit as st
import requests
import pandas as pd
from decimal import Decimal 

def fetch_and_display_kyc(api_url, headers):
    st.subheader("KYC Applications for Review")
    try:
        response = requests.get(
            f"{api_url}/kyc/admin/for-review",
            headers=headers()
        )
        if response.status_code == 200:
            data = response.json().get('kyc_records', [])
            if data:
                return pd.DataFrame(data)
            else:
                st.info("No KYC applications currently in 'In Progress' status.")
        else:
            st.error(f"Failed to fetch KYC: {response.json().get('detail')}")
        return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error fetching KYC: {e}")
        return pd.DataFrame()

def review_kyc_action(api_url, headers, customer_id, is_approved):
    status_text = "Approved" if is_approved else "Reverted"
    

    data = {"is_approved": is_approved}
    
    try:
        response = requests.post(
            f"{api_url}/kyc/admin/{customer_id}/review",
            headers=headers(),
            json=data
        )
        if response.status_code == 200:
            st.success(f"Customer {customer_id} KYC {status_text} successfully.")
        else:
            st.error(f"Review Failed: {response.json().get('detail')}")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error during KYC review: {e}")

def review_loan_action(api_url, headers, loan_id, status_val, emi=None):
    request_data = {"loan_status": status_val}
    

    if status_val == 'Approved' and emi is not None and emi > 0:
        request_data['emi_amount'] = emi
        
    try:
        response = requests.post(
            f"{api_url}/loan/admin/{loan_id}/review",
            headers=headers(),
            json=request_data
        )
        if response.status_code == 200:
            st.success(f"Loan {loan_id} marked as {status_val}.")
        else:
            st.error(f"Loan Review Failed: {response.json().get('detail')}")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error during Loan review: {e}")

def show_dashboard(api_url, get_headers):
    st.title("Admin Dashboard 💼")

    tab1, tab2 = st.tabs(["KYC Review", "Loan Review"])

    with tab1:
        df_kyc = fetch_and_display_kyc(api_url, get_headers)
        
        if not df_kyc.empty:
            st.dataframe(df_kyc, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Process KYC")
            
            with st.form("kyc_review_form"):
                customer_id_to_review = st.selectbox("Select Customer ID", df_kyc['customer_id'].tolist())
                action = st.radio("Action", ["Approve", "Revert"])
                
                kyc_submitted = st.form_submit_button(f"Execute {action}")
                
                if kyc_submitted:
                    is_approved = True if action == "Approve" else False
                    review_kyc_action(api_url, get_headers, customer_id_to_review, is_approved)
                    st.rerun()

    with tab2:
        st.subheader("Pending Loan Applications")
        try:
            response = requests.get(
                f"{api_url}/loan/admin/pending-loans",
                headers=get_headers()
            )
            if response.status_code == 200:
                data = response.json().get('loans', [])
                df_loans = pd.DataFrame(data)
                
                if df_loans.empty:
                    st.info("No pending loan applications.")
                else:
                    st.dataframe(df_loans, use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader("Process Loan")
                    
                    with st.form("loan_review_form"):
                        loan_id_to_review = st.selectbox("Select Loan ID", df_loans['loan_id'].tolist())
                        loan_action = st.radio("Action", ["Approved", "Rejected"])
                        emi_amount = None
                        
                        if loan_action == "Approved":
                            default_loan = df_loans[df_loans['loan_id'] == loan_id_to_review].iloc[0]
                            
                            # --- FIX APPLIED: Convert string to float for formatting ---
                            loan_amount_float = float(default_loan['loan_amount']) 
                            st.write(f"Original Loan Amount: **${loan_amount_float:,.2f}**")
                            # ---------------------------------------------------------
                            
                            emi_amount = st.number_input("Final Approved EMI Amount", min_value=1.0, format="%.2f")

                        loan_submitted = st.form_submit_button(f"Execute {loan_action}")

                        if loan_submitted:
                            review_loan_action(api_url, get_headers, loan_id_to_review, loan_action, emi_amount)
                            st.rerun()

            else:
                st.error(f"Failed to fetch loans: {response.json().get('detail')}")
        except requests.exceptions.RequestException as e:
            st.error(f"API Error fetching loans: {e}")