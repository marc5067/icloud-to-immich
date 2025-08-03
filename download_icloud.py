import subprocess
import os
import sys
import re
import shutil
from collections import defaultdict
from dotenv import load_dotenv

def sanitize_name(name):
    """Sanitize the album name to make it a valid directory name."""
    return re.sub(r'[^\w\-_\. ]', '_', name.strip())


def stop(interactive):
    if not interactive:
        return
    inp1=input("if you want to continue press y: ")
    if inp1 != "y":
        inp2=input("you really dont want to continue? ")
        if inp2 != "y":
            sys.exit()

def check_tool(tool_name):
    if shutil.which(tool_name) is None:
        print(f"Error: {tool_name} is not installed or not found in PATH")
        sys.exit(1)

def start(base_dir, USERNAME, USER_API, IMMICH_SERVER, ADMIN_API_KEY, interactive):
    check_tool('icloudpd')
    check_tool('immich-go')
    if not os.path.exists('.env'):
        print("Error: .env file not found")
        sys.exit(1)

    load_dotenv()

 

    if not USERNAME or not USER_API:
        print("Error: Missing iCloud username or immich api in .env file")
        sys.exit(1)

    downloads_dir = os.path.join(base_dir, "downloads")
    albums_dir = os.path.join(base_dir, "albums")

    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(albums_dir, exist_ok=True)


    # Authenticate with iCloud
    print("Authenticating with iCloud...")
    try:
        auth_result = subprocess.run(['icloudpd', '--username', USERNAME, '--auth-only'], timeout=60)
        if auth_result.returncode != 0:
            print("Authentication failed.")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Authentication timed out after 60 seconds.")

    # List albums
    print("Listing albums...")
    try:
        list_result = subprocess.run(['icloudpd', '--username', USERNAME, '--list-albums'], capture_output=True, text=True, timeout=60)
        if list_result.returncode != 0:
            print(f"Failed to list albums: {list_result.stderr}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Album listing timed out after 60 seconds.")

    # Parse album names
    exclude_albums = {'Time-lapse', 'Videos', 'Slo-mo', 'Bursts', 'Panoramas', 'Screenshots', 'Live'}
    albums_output = list_result.stdout
    album_names = []
    start_parsing = False
    for line in albums_output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Albums:"):
            start_parsing = True
            continue
        if start_parsing and not line.startswith("DEBUG") and line not in exclude_albums:
            album_names.append(line)

    print(f"Found albums: {album_names}")

    # Get filenames for each album
    album_files = defaultdict(list)
    all_album_files = set()

    for album in album_names:
        print(f"Getting filenames for album '{album}'...")
        try:
            filenames_result = subprocess.run(['icloudpd', '--username', USERNAME, '--album', album, '--only-print-filenames', '--directory', base_dir], capture_output=True, text=True, timeout=60)
            if filenames_result.returncode != 0:
                print(f"Failed to get filenames for album '{album}': {filenames_result.stderr}")
                continue
            filenames = [os.path.basename(line.strip()) for line in filenames_result.stdout.splitlines() if line.strip()]
            album_files[album] = filenames
            all_album_files.update(filenames)
        except subprocess.TimeoutExpired:
            print(f"Timeout while getting filenames for album '{album}'")
            continue

    stop(interactive)

    # Download all photos
    print("Downloading all photos...")
    download_result = subprocess.run(['icloudpd', '--username', USERNAME, '--directory', downloads_dir, '--folder-structure',  'none', '--xmp-sidecar'])
    if download_result.returncode != 0:
        print(f"Failed to download photos: {download_result.stderr}")
        sys.exit(1)

    stop(interactive)

    # Copy photos to album folders
    for album, filenames in album_files.items():
        sanitized_album = sanitize_name(album)
        album_folder = os.path.join(albums_dir, sanitized_album)
        os.makedirs(album_folder, exist_ok=True)
        for filename in filenames:
            src_path = os.path.join(downloads_dir, filename)
            dest_path = os.path.join(album_folder, filename)
            src_xmp_path = os.path.join(downloads_dir, f"{filename}.xmp")
            dest_xmp_path = os.path.join(album_folder, f"{filename}.xmp")
            
            # Copy photo
            try:
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {filename} to {album_folder}")
                else:
                    print(f"File {filename} not found in {downloads_dir}")
            except Exception as e:
                print(f"Error copying {filename} to {album_folder}: {e}")
            
            # Copy XMP sidecar file if it exists
            try:
                if os.path.exists(src_xmp_path):
                    shutil.copy2(src_xmp_path, dest_xmp_path)
                    print(f"Copied {filename}.xmp to {album_folder}")
                else:
                    print(f"XMP file {filename}.xmp not found in {downloads_dir}")
            except Exception as e:
                print(f"Error copying {filename}.xmp to {album_folder}: {e}")

    print("\nAlbum pictures copied\n")

    stop(interactive)

    # Remove photos and their XMP sidecar files from base_dir
    for filename in all_album_files:
        file_path = os.path.join(downloads_dir, filename)
        xmp_path = os.path.join(downloads_dir, f"{filename}.xmp")
        
        # Remove photo
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed {filename} from {downloads_dir}")
            else:
                print(f"File {filename} not found in {downloads_dir}")
        except Exception as e:
            print(f"Error removing {filename} from {downloads_dir}: {e}")
        
        # Remove XMP sidecar file if it exists
        try:
            if os.path.exists(xmp_path):
                os.remove(xmp_path)
                print(f"Removed {filename}.xmp from {downloads_dir}")
            else:
                print(f"XMP file {filename}.xmp not found in {downloads_dir}")
        except Exception as e:
            print(f"Error removing {filename}.xmp from {downloads_dir}: {e}")

    print("\nAlbum pictures removed\n")

    stop(interactive)

    cmd1 = ['immich-go', 'upload', 'from-folder', f'--server={IMMICH_SERVER}', f'--api-key={USER_API}', f'--admin-api-key={ADMIN_API_KEY}', downloads_dir]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    if result1.returncode != 0:
        print(f"Failed to upload from {downloads_dir}: {result1.stderr}")
        sys.exit(1)

    stop(interactive)
    
    cmd2 = ['immich-go', 'upload', 'from-folder', '--folder-as-album=FOLDER', f'--server={IMMICH_SERVER}', f'--api-key={USER_API}', f'--admin-api-key={ADMIN_API_KEY}', albums_dir]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    if result2.returncode != 0:
        print(f"Failed to upload from {albums_dir}: {result2.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    base_dir = "C:\\Users\\user\\Documents\\images"  # Change this to your desired base directory
    interactive = True   # Set to False if you want to run non-interactively
    USERNAME="example.example@gmail.com"  #change to your iCloud username
    USER_API="your_api"  #change to your Immich API
    IMMICH_SERVER = "admin_api"  #change to your Immich admin API
    ADMIN_API_KEY = "http://192.168.0.214:30033"  #change to your Immich server url
    
    start(base_dir, USERNAME, USER_API, IMMICH_SERVER, ADMIN_API_KEY, interactive)