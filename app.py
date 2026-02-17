import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import json
import pandas as pd

# --- CONFIG ---
DRIVE_FOLDER_ID = "YOUR_FOLDER_ID_HERE"  # Update this!
SERVICE_ACCOUNT_FILE = "service_secrets.json"

st.set_page_config(page_title="GameTracer Hub", page_icon="⚽", layout="wide")

# --- AUTHENTICATION ---
@st.cache_resource
def get_drive():
    settings = {
        "client_config_backend": "service",
        "service_config": {"client_json_file_path": SERVICE_ACCOUNT_FILE}
    }
    gauth = GoogleAuth(settings=settings)
    gauth.ServiceAuth()
    return GoogleDrive(gauth)

# --- APP LOGIC ---
st.title("⚽ GameTracer: AI Match Control")

try:
    drive = get_drive()
    
    # 1. DISCOVERY (Variables defined BEFORE they are used)
    file_list = drive.ListFile({'q': f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"}).GetList()
    drive_files = {f['title']: f['id'] for f in file_list if f['title'].endswith('.mp4')}
    filenames = sorted(list(drive_files.keys()))

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.subheader("📋 Team Roster")
        player_df = pd.DataFrame([{"#": "10", "Name": "Messi"}, {"#": "7", "Name": "Ronaldo"}])
        edited_df = st.data_editor(player_df, num_rows="dynamic", use_container_width=True)

    with col2:
        st.subheader("🎥 Video Selection")
        match_id = st.text_input("Unique Match ID", "Match_01")
        selected_left = st.selectbox("Select Left Camera", ["-- Select --"] + filenames)
        selected_right = st.selectbox("Select Right Camera", ["-- Select --"] + filenames)
        
        # TRIGGER LOGIC (Uses variables defined above)
        if st.button("🔥 START AI ENGINE", type="primary", use_container_width=True):
            if selected_left != "-- Select --" and selected_right != "-- Select --":
                with st.status("Syncing with AI Engine...") as status:
                    # A. Rename Videos (Quota-Safe Metadata update)
                    for side, sel_name in [("Left", selected_left), ("Right", selected_right)]:
                        f = drive.CreateFile({'id': drive_files[sel_name]})
                        f.FetchMetadata()
                        f['title'] = f"{match_id}_{side}.mp4"
                        f.Upload(param={'supportsAllDrives': True})

                    # B. Update Start Signal (Find & Edit existing file)
                    q = f"'{DRIVE_FOLDER_ID}' in parents and title = 'START_SIGNAL.txt'"
                    sigs = drive.ListFile({'q': q}).GetList()
                    if sigs:
                        sigs[0].SetContentString(match_id)
                        sigs[0].Upload(param={'supportsAllDrives': True})
                        status.update(label="AI Engaged! Check Colab.", state="complete")
                    else:
                        st.error("Missing START_SIGNAL.txt in Drive!")
            else:
                st.error("Please pick both camera angles.")

    st.divider()
    if st.button("🛑 EMERGENCY STOP", type="secondary"):
        q = f"'{DRIVE_FOLDER_ID}' in parents and title = 'STOP_SIGNAL.txt'"
        sigs = drive.ListFile({'q': q}).GetList()
        if sigs:
            sigs[0].SetContentString("SHUTDOWN")
            sigs[0].Upload(param={'supportsAllDrives': True})
            st.warning("Shutdown signal sent to Colab.")

except Exception as e:
    st.error(f"Waiting for Drive Auth: {e}")
