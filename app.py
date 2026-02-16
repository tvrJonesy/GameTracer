import streamlit as st
import pandas as pd
import json
import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# --- 1. SETTINGS & DRIVE AUTH ---
# Replace this with your actual Google Drive Folder ID
GAMETRACER_FOLDER_ID = "YOUR_FOLDER_ID_HERE"

st.set_page_config(page_title="GameTracer Hub", page_icon="⚽")

def get_drive_connection():
    """Connects to Google Drive using the secrets file"""
    gauth = GoogleAuth()
    # If using Streamlit Cloud, it will look for 'client_secrets.json' 
    # in the same folder you uploaded to GitHub.
    gauth.LocalWebserverAuth() 
    return GoogleDrive(gauth)

# --- 2. THE UI ---
st.title("⚽ GameTracer Pro")
st.markdown("---")

# Section A: Team Sheet
st.subheader("📋 1. Setup Team Sheet")
st.caption("The AI uses this to read jersey numbers and tag players by name.")

# Create an editable table
data = [
    {"Number": "10", "Name": "Player 1"},
    {"Number": "7", "Name": "Player 2"},
    {"Number": "1", "Name": "Goalkeeper"}
]
df = pd.DataFrame(data)
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# Section B: Video Upload
st.subheader("📤 2. Upload Match Footage")
uploaded_file = st.file_uploader("Choose a 4K MP4 file", type=['mp4'])

# --- 3. THE UPLOAD LOGIC ---
if uploaded_file and st.button("🚀 Send to GameTracer Engine"):
    try:
        drive = get_drive_connection()
        
        with st.spinner('Uploading files to Google Drive...'):
            # A. Save and Upload Team Sheet (JSON)
            team_dict = dict(zip(edited_df['Number'].astype(str), edited_df['Name']))
            json_name = f"{uploaded_file.name}_teamsheet.json"
            
            with open("temp_sheet.json", "w") as f:
                json.dump(team_dict, f)
            
            json_file = drive.CreateFile({'title': json_name, 'parents': [{'id': GAMETRACER_FOLDER_ID}]})
            json_file.SetContentFile("temp_sheet.json")
            json_file.Upload()

            # B. Save and Upload Video
            video_file = drive.CreateFile({'title': uploaded_file.name, 'parents': [{'id': GAMETRACER_FOLDER_ID}]})
            
            # Write the uploaded buffer to a temp file
            with open("temp_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            video_file.SetContentFile("temp_video.mp4")
            video_file.Upload()

            st.success("✅ Success! Video and Team Sheet are now in the GameTracer folder.")
            st.balloons()
            
            # Clean up temp files
            os.remove("temp_sheet.json")
            os.remove("temp_video.mp4")
            
    except Exception as e:
        st.error(f"Authentication Error: Ensure your client_secrets.json is in the folder. Error: {e}")

st.markdown("---")
st.info("💡 **Next Step:** Open your Google Colab notebook and hit 'Run All' to start the AI tracking.")
