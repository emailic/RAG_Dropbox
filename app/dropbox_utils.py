import dropbox
import os
from dotenv import load_dotenv
from typing import List

load_dotenv(override=True)

def get_dropbox_client():
    """Initialize Dropbox client"""
    return dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))


def list_dropbox_files() -> List[str]:
    """List all files in the configured Dropbox folder"""
    dbx = get_dropbox_client()
    try:
        response = dbx.files_list_folder("")
        return [entry.name for entry in response.entries]
    except Exception as e:
        print(f"Error listing Dropbox files: {e}")
        return []

def download_file(filename: str) -> str:
    """Download a file from Dropbox to local storage"""
    dbx = get_dropbox_client()
    local_path = os.path.join("temp_downloads", filename)
    os.makedirs("temp_downloads", exist_ok=True)
    
    try:
        dbx.files_download_to_file(local_path, f"/{filename}")
        return local_path
    except Exception as e:
        print(f"Error downloading file {filename}: {e}")
        raise
    
# print(os.getenv("DROPBOX_ACCESS_TOKEN"))
# a = list_dropbox_files()