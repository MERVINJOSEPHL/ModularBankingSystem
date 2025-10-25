# smart-bank-modular/pages/auditor_dashboard.py - FINAL CORRECTED VERSION

import streamlit as st
import requests
import pandas as pd
import json 

def show_dashboard(api_url, get_headers):
    st.title("Auditor Dashboard 📜")
    st.subheader("Critical System Audit Logs")

    try:
        response = requests.get(
            f"{api_url}/auditor/audit-logs",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            data = response.json().get('logs', [])
            total_count = response.json().get('total_count', 0)
            st.success(f"Successfully retrieved {total_count} audit logs.")
            
            if data:
                df = pd.DataFrame(data)
                

                df['user_id'] = df['user_id'].apply(lambda x: str(x) if x else 'N/A')
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df['details'] = df['details'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else str(x))
                df = df[['timestamp', 'action', 'user_id', 'details', 'log_id']]
                
                st.dataframe(df, use_container_width=True) 
            else:
                st.info("The audit log is empty.")
                
        else:
            detail = response.json().get('detail', 'Authentication failed or API error.')
            st.error(f"Failed to retrieve audit logs: {detail}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: {e}")