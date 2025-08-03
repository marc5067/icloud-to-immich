# icloud-to-immich
This Python script downloads photos from iCloud, organizes them into albums, and uploads them to an Immich server. It supports downloading photos with their metadata (XMP sidecar files) and organizing them into album-specific folders before uploading to Immich. This project is under development so it is not perfected yet and other functionalities are coming soon.

## Features
- Authenticates with iCloud to access photos and albums.
- Downloads photos and their metadata to a local directory.
- Organizes photos into album-specific folders.
- Uploads photos to an Immich server, preserving album structure.
- Supports interactive mode for user confirmation at key steps.

## Requirements
- Python 3.6+
- External tools:
   - icloudpd (iCloud Photos Downloader)
   - immich-go (Immich command-line tool)

## Installation
- Clone the repository:
  ```bash
  git clone https://github.com/your-username/icloud-to-immich-sync.git
  cd icloud-to-immich-sync
  ```
  OR
  download [download_icloud.py](./download_icloud.py) file

- Install external tools:
  - Install icloudpd: `pip install icloudpd`
  - Install immich-go: Follow the instructions at immich-go.

## Set up variables:
Edit variables with your credentials inside the if __name__ == "__main__": block.:\
- ICLOUD_USERNAME = icloud_username
- IMMICH_API = immich api key
- ADMIN_API_KEY = immich admin api key
- IMMICH_SERVER = immich url
- interactive: Enables interactive prompts for user confirmation (default: enabled(True)).

## Usage
Run the script with the following command:
`python download_icloud.py`
OR
`py download_icloud.py`

## Troubleshooting
Authentication failed: Verify your ICLOUD_USERNAME and ensure two-factor authentication is set up correctly.
Tool not found: Ensure icloudpd and immich-go are installed and accessible in your system's PATH.
Upload errors: Check the Immich server URL and API keys in the .env file.

## FUTURE
- add option to delete pictures from iCloud when they are downloaded (move them to Recently Deleted)
- docker container for this script with WebUI so you can have it as docker container on NAS (TrueNas) or any machine that is running Docker

## License
This project is licensed under the MIT License. See the LICENSE file for details.
