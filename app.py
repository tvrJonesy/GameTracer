import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import pandas as pd
import os

# CONFIG
DRIVE_FOLDER_ID = "14TMFY4tb6byRO_ipspgv0g1PzAojm98D"

st.set_page_config(page_title="GameTracer Pro", page_icon="⚽", layout="wide")

def get_drive():
    # settings dictionary tells pydrive2 to use the Service Account
    settings = {
        "client_config_backend": "service",
        "service_config": {
            "client_json_file_path": "service_secrets.json",
        }
    }
    gauth = GoogleAuth(settings=settings)
    gauth.ServiceAuth() # This logs in silently!
    return GoogleDrive(gauth)
    
st.title("⚽ GameTracer: Tactical Hub")

try:
    drive = get_drive()
    file_list = drive.ListFile({'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"}).GetList()
    drive_files = {f['title']: f['id'] for f in file_list if f['title'].endswith('.mp4')}
    filenames = sorted(list(drive_files.keys()))

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📋 Team Sheet")
        # Editable table for player names
        player_df = pd.DataFrame([{"#": "10", "Name": "Captain"}, {"#": "7", "Name": "Striker"}])
        edited_df = st.data_editor(player_df, num_rows="dynamic", use_container_width=True)

    with col2:
        st.subheader("🎥 Camera Setup")
        match_id = st.text_input("Match Name", "Finals_V1")
        sel_l = st.selectbox("Left Camera", ["-- Select --"] + filenames)
        sel_r = st.selectbox("Right Camera", ["-- Select --"] + filenames)
        
    if st.button("🔥 START AI ENGINE", type="primary", use_container_width=True):
        if selected_left != "-- Select --" and selected_right != "-- Select --":
            with st.status("🚀 Processing...") as s:
                # A. RENAME VIDEOS (Metadata Update - Doesn't use robot quota)
                for side, sel in [("Left", selected_left), ("Right", selected_right)]:
                    f_id = drive_files[sel]
                    f = drive.CreateFile({'id': f_id})
                    f.FetchMetadata() 
                    f['title'] = f"{match_id}_{side}.mp4"
                    f.Upload(param={'supportsAllDrives': True}) 
            
                # B. UPDATE SIGNAL (Finds the file YOU created and edits it)
                query = f"'{DRIVE_FOLDER_ID}' in parents and title = 'START_SIGNAL.txt'"
                signals = drive.ListFile({'q': query}).GetList()
            
            if signals:
                start_sig = signals[0]
                start_sig.SetContentString(match_id)
                start_sig.Upload(param={'supportsAllDrives': True})
                s.update(label="Engine Engaged!", state="complete")
            else:
                st.error("⚠️ Error: START_SIGNAL.txt not found. Create it manually in Drive!")


    st.divider()
    if st.button("🛑 STOP RESOURCE USAGE", type="secondary"):
        query = f"'{DRIVE_FOLDER_ID}' in parents and title = 'STOP_SIGNAL.txt'"
        signals = drive.ListFile({'q': query}).GetList()
        if signals:
            stop_sig = signals[0]
            stop_sig.SetContentString("SHUTDOWN")
            stop_sig.Upload(param={'supportsAllDrives': True})
            st.warning("Shutdown signal sent.")

except Exception as e:
    st.error(f"Waiting for Drive Auth: {e}")
