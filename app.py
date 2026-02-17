import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import pandas as pd

# CONFIG
DRIVE_FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID"

st.set_page_config(page_title="GameTracer Pro", page_icon="⚽", layout="wide")

def get_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
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
            if sel_l != "-- Select --" and sel_r != "-- Select --":
                with st.status("Syncing Data...") as s:
                    # 1. Save Team Sheet to JSON
                    team_dict = dict(zip(edited_df['#'].astype(str), edited_df['Name']))
                    with open("teams.json", "w") as f: json.dump(team_dict, f)
                    
                    # 2. Upload Team Sheet
                    ts_file = drive.CreateFile({'title': f"{match_id}_teams.json", 'parents': [{'id': DRIVE_FOLDER_ID}]})
                    ts_file.SetContentFile("teams.json")
                    ts_file.Upload()
                    
                    # 3. Rename Videos
                    for side, sel in [("Left", sel_l), ("Right", sel_r)]:
                        f = drive.CreateFile({'id': drive_files[sel]})
                        f['title'] = f"{match_id}_{side}.mp4"
                        f.Upload()
                    
                    # 4. Signal Colab
                    sig = drive.CreateFile({'title': 'START_SIGNAL.txt', 'parents': [{'id': DRIVE_FOLDER_ID}]})
                    sig.SetContentString(match_id)
                    sig.Upload()
                    s.update(label="AI Processing Started!", state="complete")
            else:
                st.error("Please assign both cameras.")

    st.divider()
    if st.button("🛑 EMERGENCY STOP (SAVE CREDITS)", type="secondary"):
        stop_file = drive.CreateFile({'title': 'STOP_SIGNAL.txt', 'parents': [{'id': DRIVE_FOLDER_ID}]})
        stop_file.SetContentString("KILL"); stop_file.Upload()
        st.warning("Stop signal sent.")

except Exception as e:
    st.error(f"Waiting for Drive Auth: {e}")
