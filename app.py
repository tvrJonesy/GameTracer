import streamlit as st
import pandas as pd
import json
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- CONFIGURATION ---
# Replace this with the long ID found in your Google Drive folder URL
GAMETRACER_FOLDER_ID = "1Wts9vOMDBrUg8R_VX8J5PQPvChdSUwUm"

st.set_page_config(page_title="GameTracer Hub", page_icon="⚽", layout="wide")

def get_drive_connection():
    """Authenticates using client_secrets.json in the app folder"""
    gauth = GoogleAuth()
    # Looking for client_secrets.json in your GitHub/local directory
    gauth.LocalWebserverAuth() 
    return GoogleDrive(gauth)

# --- USER INTERFACE ---
st.title("⚽ GameTracer Pro Dashboard")
st.markdown("Use this hub to prepare match data and trigger the AI tracking engine.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 Step 1: Team Sheet")
    st.info("The AI uses these numbers to identify players in the video.")
    
    # Default player list
    default_players = [
        {"Number": "10", "Name": "Captain Jack"},
        {"Number": "7", "Name": "Striker Sam"},
        {"Number": "1", "Name": "Goalie Gabe"}
    ]
    
    # Editable table for player names
    df = pd.DataFrame(default_players)
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

with col2:
    st.subheader("📤 Step 2: Upload & Run")
    uploaded_file = st.file_uploader("Upload Raw 4K Match Footage (.mp4)", type=['mp4'])
    
    if uploaded_file:
        st.success(f"Ready to upload: {uploaded_file.name}")
        
        if st.button("🚀 START AI ENGINE"):
            try:
                drive = get_drive_connection()
                
                with st.status("Processing Uploads...", expanded=True) as status:
                    # A. Upload the Team Sheet (JSON)
                    st.write("Creating Team Sheet...")
                    team_dict = dict(zip(edited_df['Number'].astype(str), edited_df['Name']))
                    ts_filename = f"{uploaded_file.name}_teamsheet.json"
                    
                    with open("temp_ts.json", "w") as f:
                        json.dump(team_dict, f)
                    
                    ts_file = drive.CreateFile({'title': ts_filename, 'parents': [{'id': GAMETRACER_FOLDER_ID}]})
                    ts_file.SetContentFile("temp_ts.json")
                    ts_file.Upload()

                    # B. Upload the Video
                    st.write("Uploading Video (This may take a few minutes)...")
                    with open("temp_vid.mp4", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    vid_file = drive.CreateFile({'title': uploaded_file.name, 'parents': [{'id': GAMETRACER_FOLDER_ID}]})
                    vid_file.SetContentFile("temp_vid.mp4")
                    vid_file.Upload()

                    # C. Create the Trigger Signal
                    st.write("Waking up Colab Engine...")
                    sig_file = drive.CreateFile({'title': 'START_SIGNAL.txt', 'parents': [{'id': GAMETRACER_FOLDER_ID}]})
                    sig_file.SetContentString("GO")
                    sig_file.Upload()
                    
                    status.update(label="✅ Upload Complete! AI is now tracking.", state="complete")
                    st.balloons()

                # Cleanup
                os.remove("temp_ts.json")
                os.remove("temp_vid.mp4")

            except Exception as e:
                st.error(f"Error: {e}. Check if 'client_secrets.json' is present.")

st.divider()
st.caption("GameTracer AI Engine v2.0 - Powered by Streamlit & YOLOv8")
